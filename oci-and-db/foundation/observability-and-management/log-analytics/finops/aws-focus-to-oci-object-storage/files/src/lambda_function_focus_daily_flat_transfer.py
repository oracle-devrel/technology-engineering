import hashlib
import http.client
import json
import logging
import os
import re
import tempfile
import traceback
from datetime import datetime, timezone, timedelta
from urllib.parse import quote, urlsplit

import boto3
from botocore.exceptions import ClientError


# -----------------------------
# AWS clients
# -----------------------------
s3 = boto3.client("s3")


# -----------------------------
# Logging setup
# -----------------------------
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


# -----------------------------
# Environment variables
# -----------------------------
SOURCE_BUCKET = os.environ["SOURCE_BUCKET"]
SOURCE_PREFIX = os.environ.get("SOURCE_PREFIX", "").lstrip("/")

OCI_BASE_URL = os.environ["OCI_BASE_URL"].rstrip("/")
DEST_PREFIX = os.environ.get("DEST_PREFIX", "").strip("/")
OUTPUT_FILE_PREFIX = os.environ.get("OUTPUT_FILE_PREFIX", "aws_focus_daily")

LOOKBACK_HOURS = int(os.environ.get("LOOKBACK_HOURS", "24"))
PROCESS_ALL = os.environ.get("PROCESS_ALL", "false").lower() == "true"

LOG_BUCKET = os.environ.get("LOG_BUCKET", SOURCE_BUCKET)
LOG_PREFIX = os.environ.get("LOG_PREFIX", "transfer-logs").strip("/")
ENABLE_S3_AUDIT_LOG = os.environ.get("ENABLE_S3_AUDIT_LOG", "true").lower() == "true"

OCI_REGION = os.environ.get("OCI_REGION", "")
OCI_NAMESPACE = os.environ.get("OCI_NAMESPACE", "")
OCI_BUCKET = os.environ.get("OCI_BUCKET", "")


# This is cleared at the start of every Lambda invocation.
# It is global only so helper functions can add audit events.
AUDIT_EVENTS = []


# -----------------------------
# Utility functions
# -----------------------------
def to_bool(value):
    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in ["true", "1", "yes", "y"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize_prefix(prefix: str) -> str:
    prefix = prefix.lstrip("/")

    if prefix and not prefix.endswith("/"):
        prefix += "/"

    return prefix


def is_focus_report_file(key: str) -> bool:
    return key.endswith(".csv.gz") and not key.endswith("/")


def source_relative_key(key: str, prefix: str) -> str:
    prefix = normalize_prefix(prefix)

    if prefix and key.startswith(prefix):
        return key[len(prefix):].lstrip("/")

    return key.lstrip("/")


def emit_audit_event(event_type: str, **fields) -> None:
    """
    Sends structured logs to CloudWatch and stores events for the monthly S3 audit log.

    Important:
    Do not log OCI_BASE_URL because it contains the OCI PAR token.
    """

    event = {
        "timestamp_utc": utc_now_iso(),
        "event_type": event_type,
        **fields
    }

    # CloudWatch structured log
    logger.info(json.dumps(event, default=str))

    # Monthly S3 audit log buffer
    AUDIT_EVENTS.append(event)


def monthly_audit_log_key() -> str:
    now = datetime.now(timezone.utc)
    month = now.strftime("%Y-%m")
    return f"{LOG_PREFIX}/focus-transfer-log-{month}.jsonl"


def write_monthly_audit_log_to_s3() -> None:
    """
    Writes one JSONL audit log file per month.

    S3 is not an append-only filesystem, so this function reads the existing
    monthly log, appends this invocation's entries, and writes the full object back.

    Reserved concurrency should be set to 1 to avoid two Lambda executions writing
    to the same monthly log at the same time.
    """

    if not ENABLE_S3_AUDIT_LOG:
        logger.info("S3 audit logging disabled.")
        return

    if not AUDIT_EVENTS:
        logger.info("No audit events to write.")
        return

    log_key = monthly_audit_log_key()

    new_lines = "".join(
        json.dumps(event, default=str, separators=(",", ":")) + "\n"
        for event in AUDIT_EVENTS
    )

    try:
        existing_obj = s3.get_object(Bucket=LOG_BUCKET, Key=log_key)
        existing_body = existing_obj["Body"].read().decode("utf-8")

    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code")

        if error_code in ["NoSuchKey", "404", "NotFound"]:
            existing_body = ""
        elif error_code == "AccessDenied":
            raise PermissionError(
                "Unable to read the monthly audit log object. Confirm the Lambda role has "
                "s3:GetObject and s3:PutObject on the transfer-logs prefix, plus s3:ListBucket "
                "for the transfer-logs prefix."
            ) from exc
        else:
            raise

    final_body = existing_body + new_lines

    s3.put_object(
        Bucket=LOG_BUCKET,
        Key=log_key,
        Body=final_body.encode("utf-8"),
        ContentType="application/x-ndjson"
    )

    logger.info(f"Monthly audit log written to s3://{LOG_BUCKET}/{log_key}")


# -----------------------------
# OCI object naming
# -----------------------------
def safe_flat_filename(relative_key: str, etag: str, last_modified: str) -> str:
    """
    Converts the S3 object path into one flat OCI filename.

    Example source relative key:
      billing_period=2026-05/AWSfocusDataexport-00001.csv.gz

    Example OCI object name:
      aws_focus_daily__billing_period=2026-05__AWSfocusDataexport-00001__a1b2c3d4.csv.gz

    There is no "/" in this name, so OCI will not show a folder structure.
    """

    cleaned = relative_key.strip("/")

    # Replace S3 folder separators with double underscores.
    cleaned = cleaned.replace("/", "__")

    # Keep safe readable characters.
    cleaned = re.sub(r"[^A-Za-z0-9._=\-]+", "_", cleaned)

    # Remove the original extension before adding our unique suffix.
    if cleaned.endswith(".csv.gz"):
        cleaned = cleaned[:-7]

    etag_clean = etag.replace('"', "")

    short_hash = hashlib.sha256(
        f"{relative_key}|{etag_clean}|{last_modified}".encode("utf-8")
    ).hexdigest()[:8]

    return f"{OUTPUT_FILE_PREFIX}__{cleaned}__{short_hash}.csv.gz"


def build_oci_object_name(relative_key: str, etag: str, last_modified: str) -> str:
    flat_name = safe_flat_filename(relative_key, etag, last_modified)

    if DEST_PREFIX:
        return f"{DEST_PREFIX}/{flat_name}"

    return flat_name


def build_oci_url(object_name: str) -> str:
    encoded_object_name = quote(object_name, safe="/=._-")
    return f"{OCI_BASE_URL}/{encoded_object_name}"


# -----------------------------
# OCI upload
# -----------------------------
def put_file_to_oci(local_file_path: str, oci_object_url: str) -> None:
    parsed = urlsplit(oci_object_url)

    if parsed.scheme != "https":
        raise ValueError("OCI upload URL must use HTTPS.")

    request_path = parsed.path

    if parsed.query:
        request_path += f"?{parsed.query}"

    file_size = os.path.getsize(local_file_path)

    headers = {
        "Content-Type": "application/gzip",
        "Content-Length": str(file_size)
    }

    conn = http.client.HTTPSConnection(parsed.netloc, timeout=300)

    try:
        with open(local_file_path, "rb") as file_body:
            conn.request(
                method="PUT",
                url=request_path,
                body=file_body,
                headers=headers
            )

            response = conn.getresponse()
            response_body = response.read().decode("utf-8", errors="replace")

            if response.status < 200 or response.status >= 300:
                raise Exception(
                    f"OCI upload failed. HTTP {response.status} {response.reason}. "
                    f"Response: {response_body}"
                )

            logger.info(f"OCI upload successful. HTTP {response.status} {response.reason}")

    finally:
        conn.close()


# -----------------------------
# S3 discovery
# -----------------------------
def list_candidate_objects(lookback_hours: int, process_all: bool):
    """
    EventBridge scheduled mode.

    Scans SOURCE_BUCKET / SOURCE_PREFIX and selects .csv.gz files modified inside
    the lookback window.

    Since there is no DynamoDB or other state store, the lookback window is the
    mechanism used to select the daily files.
    """

    prefix = normalize_prefix(SOURCE_PREFIX)
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    emit_audit_event(
        "S3_SCAN_STARTED",
        source_bucket=SOURCE_BUCKET,
        source_prefix=prefix,
        process_all=process_all,
        lookback_hours=lookback_hours,
        cutoff_time_utc=cutoff_time.isoformat()
    )

    candidates = []
    paginator = s3.get_paginator("list_objects_v2")

    for page in paginator.paginate(Bucket=SOURCE_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            last_modified = obj["LastModified"]

            if not is_focus_report_file(key):
                logger.info(f"Skipping non-report object: {key}")
                continue

            if not process_all and last_modified < cutoff_time:
                logger.info(f"Skipping old object: {key}, LastModified={last_modified}")
                continue

            candidates.append({
                "bucket": SOURCE_BUCKET,
                "key": key,
                "etag": obj.get("ETag", ""),
                "size": obj.get("Size", 0),
                "last_modified": last_modified.isoformat()
            })

    candidates.sort(key=lambda item: item["last_modified"])

    emit_audit_event(
        "S3_SCAN_COMPLETED",
        candidate_count=len(candidates)
    )

    return candidates


# -----------------------------
# Per-file transfer
# -----------------------------
def process_object(candidate, request_id: str):
    bucket = candidate["bucket"]
    key = candidate["key"]
    etag = candidate["etag"]
    size = candidate["size"]
    last_modified = candidate["last_modified"]

    relative_key = source_relative_key(key, SOURCE_PREFIX)
    oci_object_name = build_oci_object_name(relative_key, etag, last_modified)
    oci_url = build_oci_url(oci_object_name)

    emit_audit_event(
        "FILE_TRANSFER_STARTED",
        lambda_request_id=request_id,
        source_bucket=bucket,
        source_key=key,
        source_size_bytes=size,
        source_etag=etag,
        source_last_modified=last_modified,
        source_relative_key=relative_key,
        destination_type="OCI_OBJECT_STORAGE",
        oci_region=OCI_REGION,
        oci_namespace=OCI_NAMESPACE,
        oci_bucket=OCI_BUCKET,
        oci_object_name=oci_object_name
    )

    try:
        with tempfile.NamedTemporaryFile() as tmp:
            logger.info(f"Downloading from S3: s3://{bucket}/{key}")
            s3.download_file(bucket, key, tmp.name)

            logger.info(f"Uploading to OCI object: {oci_object_name}")
            put_file_to_oci(tmp.name, oci_url)

        emit_audit_event(
            "FILE_TRANSFER_COMPLETED",
            lambda_request_id=request_id,
            status="SUCCESS",
            source_bucket=bucket,
            source_key=key,
            source_size_bytes=size,
            source_etag=etag,
            source_last_modified=last_modified,
            destination_type="OCI_OBJECT_STORAGE",
            oci_region=OCI_REGION,
            oci_namespace=OCI_NAMESPACE,
            oci_bucket=OCI_BUCKET,
            oci_object_name=oci_object_name
        )

        return {
            "status": "uploaded",
            "source_key": key,
            "oci_object_name": oci_object_name
        }

    except Exception as exc:
        emit_audit_event(
            "FILE_TRANSFER_FAILED",
            lambda_request_id=request_id,
            status="FAILED",
            source_bucket=bucket,
            source_key=key,
            source_size_bytes=size,
            source_etag=etag,
            source_last_modified=last_modified,
            destination_type="OCI_OBJECT_STORAGE",
            oci_region=OCI_REGION,
            oci_namespace=OCI_NAMESPACE,
            oci_bucket=OCI_BUCKET,
            oci_object_name=oci_object_name,
            error_message=str(exc),
            error_trace=traceback.format_exc()
        )

        return {
            "status": "failed",
            "source_key": key,
            "oci_object_name": oci_object_name,
            "error": str(exc)
        }


# -----------------------------
# Lambda handler
# -----------------------------
def lambda_handler(event, context):
    AUDIT_EVENTS.clear()

    if event is None:
        event = {}

    request_id = context.aws_request_id if context else "unknown"

    # EventBridge can override these values in the JSON payload.
    lookback_hours = int(event.get("lookback_hours", LOOKBACK_HOURS))
    process_all = to_bool(event.get("process_all", PROCESS_ALL))

    emit_audit_event(
        "LAMBDA_RUN_STARTED",
        lambda_request_id=request_id,
        source_bucket=SOURCE_BUCKET,
        source_prefix=SOURCE_PREFIX,
        destination_type="OCI_OBJECT_STORAGE",
        oci_region=OCI_REGION,
        oci_namespace=OCI_NAMESPACE,
        oci_bucket=OCI_BUCKET,
        oci_destination_prefix=DEST_PREFIX if DEST_PREFIX else "[none - bucket root]",
        lookback_hours=lookback_hours,
        process_all=process_all
    )

    uploaded = 0
    failed = 0
    results = []

    try:
        candidates = list_candidate_objects(
            lookback_hours=lookback_hours,
            process_all=process_all
        )

        if not candidates:
            emit_audit_event(
                "LAMBDA_RUN_COMPLETED",
                lambda_request_id=request_id,
                status="SUCCESS",
                message="No candidate .csv.gz files found",
                uploaded=0,
                failed=0,
                total_files=0
            )

            return {
                "status": "success",
                "message": "No candidate .csv.gz files found",
                "uploaded": 0,
                "failed": 0
            }

        for candidate in candidates:
            result = process_object(candidate, request_id)
            results.append(result)

            if result["status"] == "uploaded":
                uploaded += 1
            else:
                failed += 1

        final_status = "SUCCESS" if failed == 0 else "PARTIAL_FAILURE"

        emit_audit_event(
            "LAMBDA_RUN_COMPLETED",
            lambda_request_id=request_id,
            status=final_status,
            uploaded=uploaded,
            failed=failed,
            total_files=len(candidates)
        )

        return {
            "status": final_status.lower(),
            "uploaded": uploaded,
            "failed": failed,
            "results": results
        }

    except Exception as exc:
        emit_audit_event(
            "LAMBDA_RUN_FAILED",
            lambda_request_id=request_id,
            status="FAILED",
            uploaded=uploaded,
            failed=failed,
            error_message=str(exc),
            error_trace=traceback.format_exc()
        )

        raise

    finally:
        write_monthly_audit_log_to_s3()
