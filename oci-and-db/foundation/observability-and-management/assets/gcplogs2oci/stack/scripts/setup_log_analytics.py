#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# setup_log_analytics.py
#
# Create OCI Log Analytics custom fields (40), JSON parser
# (44 field mappings), and source for GCP Cloud Logging.
#
# This script handles the Log Analytics resources that have no
# Terraform provider support.  Run it after `terraform apply`
# (or `setup_oci.sh` steps 1–4) to complete the pipeline.
#
# Auth (tried in order):
#   1. OCI Resource Principal  (OCI_RESOURCE_PRINCIPAL_VERSION set)
#   2. OCI config file         (~/.oci/config)
#   3. Environment variables   (OCI_USER_OCID, OCI_KEY_FILE, etc.)
#
# Required environment variables:
#   LA_NAMESPACE        – Log Analytics namespace
#   OCI_COMPARTMENT_ID  – Compartment OCID (for source creation)
#
# Optional (only for env-var auth):
#   OCI_REGION, OCI_USER_OCID, OCI_FINGERPRINT,
#   OCI_TENANCY_OCID, OCI_KEY_FILE or OCI_KEY_CONTENT
#
# Usage:
#   export LA_NAMESPACE="mynamespace"
#   export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxx"
#   python3 stack/scripts/setup_log_analytics.py
# ─────────────────────────────────────────────────────────────
import json
import os
import sys

import oci
from oci.log_analytics.models import (
    LogAnalyticsField,
    LogAnalyticsParserField,
    UpsertLogAnalyticsFieldDetails,
    UpsertLogAnalyticsParserDetails,
)


# ── Authentication ────────────────────────────────────────────

def get_client():
    """Build LogAnalyticsClient with auto-detected auth."""

    # 1. Resource Principal (OCI Resource Manager / Container Instances)
    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        signer = oci.auth.signers.get_resource_principals_signer()
        return oci.log_analytics.LogAnalyticsClient({}, signer=signer)

    # 2. OCI config file (~/.oci/config)
    try:
        config = oci.config.from_file()
        oci.config.validate_config(config)
        return oci.log_analytics.LogAnalyticsClient(config)
    except Exception:
        pass

    # 3. Environment variables
    key_file = os.environ.get("OCI_KEY_FILE")
    key_content = os.environ.get("OCI_KEY_CONTENT")
    if key_file:
        with open(os.path.expanduser(key_file)) as f:
            key_pem = f.read()
    elif key_content:
        key_pem = key_content
    else:
        print("ERROR: No OCI credentials found.")
        print("  Set OCI config file (~/.oci/config), OCI_KEY_FILE, or")
        print("  run inside OCI Resource Manager.")
        sys.exit(1)

    config = {
        "user": os.environ["OCI_USER_OCID"],
        "key_content": key_pem,
        "pass_phrase": os.environ.get("OCI_KEY_PASSPHRASE", ""),
        "fingerprint": os.environ["OCI_FINGERPRINT"],
        "tenancy": os.environ["OCI_TENANCY_OCID"],
        "region": os.environ.get("OCI_REGION", ""),
    }
    return oci.log_analytics.LogAnalyticsClient(config)


# ── Field Definitions (40 custom fields) ─────────────────────

FIELD_DISPLAY_NAMES = [
    # Multicloud
    "Cloud Provider",
    # Core GCP LogEntry
    "GCP Insert ID",
    "GCP Log Name",
    "GCP Resource Type",
    "GCP Project ID",
    "GCP Service Name",
    "GCP Method Name",
    "GCP Principal Email",
    "GCP Zone",
    "GCP Instance ID",
    "GCP Trace ID",
    "GCP Span ID",
    "GCP Text Payload",
    # HTTP request (Cloud Run, Load Balancer)
    "GCP HTTP Method",
    "GCP HTTP URL",
    "GCP HTTP Status",
    "GCP HTTP Latency",
    "GCP HTTP Protocol",
    "GCP HTTP Remote IP",
    "GCP HTTP Request Size",
    "GCP HTTP Response Size",
    "GCP HTTP Server IP",
    "GCP HTTP User Agent",
    # Source location & operation
    "GCP Operation ID",
    "GCP Source File",
    "GCP Source Line",
    "GCP Source Function",
    # Cloud Run resource labels
    "GCP Configuration Name",
    "GCP Location",
    "GCP Cloud Run Service",
    "GCP Revision Name",
    # Audit log extended
    "GCP Resource Name",
    "GCP Caller IP",
    "GCP Caller User Agent",
    # Metadata
    "GCP Receive Timestamp",
    # Resource labels (multi-type)
    "GCP Subscription ID",
    "GCP Topic ID",
    "GCP Sink Name",
    "GCP Sink Destination",
    # Labels
    "GCP Label Instance ID",
]


# ── Parser Field Mappings (44 total) ─────────────────────────
# (display_name_or_builtin, json_path, sequence)

FIELD_MAPPINGS = [
    # Built-in LA fields
    ("msg",                      "$.jsonPayload.message",                                         1),
    ("sevlvl",                   "$.severity",                                                    2),
    ("time",                     "$.timestamp",                                                   3),
    ("method",                   "$.protoPayload.methodName",                                     4),
    # Multicloud
    ("Cloud Provider",           "$.cloudProvider",                                                5),
    # Core GCP LogEntry
    ("GCP Insert ID",            "$.insertId",                                                    6),
    ("GCP Log Name",             "$.logName",                                                     7),
    ("GCP Resource Type",        "$.resource.type",                                               8),
    ("GCP Project ID",           "$.resource.labels.project_id",                                  9),
    ("GCP Service Name",         "$.protoPayload.serviceName",                                   10),
    ("GCP Method Name",          "$.protoPayload.methodName",                                    11),
    ("GCP Principal Email",      "$.protoPayload.authenticationInfo.principalEmail",             12),
    ("GCP Zone",                 "$.resource.labels.zone",                                       13),
    ("GCP Instance ID",          "$.resource.labels.instance_id",                                14),
    ("GCP Trace ID",             "$.trace",                                                      15),
    ("GCP Span ID",              "$.spanId",                                                     16),
    ("GCP Text Payload",         "$.textPayload",                                                17),
    # HTTP request (full)
    ("GCP HTTP Method",          "$.httpRequest.requestMethod",                                   18),
    ("GCP HTTP URL",             "$.httpRequest.requestUrl",                                      19),
    ("GCP HTTP Status",          "$.httpRequest.status",                                         20),
    ("GCP HTTP Latency",         "$.httpRequest.latency",                                        21),
    ("GCP HTTP Protocol",        "$.httpRequest.protocol",                                       22),
    ("GCP HTTP Remote IP",       "$.httpRequest.remoteIp",                                       23),
    ("GCP HTTP Request Size",    "$.httpRequest.requestSize",                                    24),
    ("GCP HTTP Response Size",   "$.httpRequest.responseSize",                                   25),
    ("GCP HTTP Server IP",       "$.httpRequest.serverIp",                                       26),
    ("GCP HTTP User Agent",      "$.httpRequest.userAgent",                                      27),
    # Source location & operation
    ("GCP Operation ID",         "$.operation.id",                                               28),
    ("GCP Source File",          "$.sourceLocation.file",                                        29),
    ("GCP Source Line",          "$.sourceLocation.line",                                        30),
    ("GCP Source Function",      "$.sourceLocation.function",                                    31),
    # Cloud Run resource labels
    ("GCP Configuration Name",   "$.resource.labels.configuration_name",                         32),
    ("GCP Location",             "$.resource.labels.location",                                   33),
    ("GCP Cloud Run Service",    "$.resource.labels.service_name",                               34),
    ("GCP Revision Name",        "$.resource.labels.revision_name",                              35),
    # Audit log extended
    ("GCP Resource Name",        "$.protoPayload.resourceName",                                  36),
    ("GCP Caller IP",            "$.protoPayload.requestMetadata.callerIp",                      37),
    ("GCP Caller User Agent",    "$.protoPayload.requestMetadata.callerSuppliedUserAgent",       38),
    # Metadata
    ("GCP Receive Timestamp",    "$.receiveTimestamp",                                           39),
    # Resource labels (multi-type)
    ("GCP Subscription ID",      "$.resource.labels.subscription_id",                            40),
    ("GCP Topic ID",             "$.resource.labels.topic_id",                                   41),
    ("GCP Sink Name",            "$.resource.labels.name",                                       42),
    ("GCP Sink Destination",     "$.resource.labels.destination",                                43),
    # Labels
    ("GCP Label Instance ID",    "$.labels.instanceId",                                          44),
]


# ── Example Log (exercises all 44 field mappings) ────────────

EXAMPLE_LOG = {
    "cloudProvider": "GCP",
    "insertId": "abc123def456-0",
    "timestamp": "2026-01-15T10:30:00.000Z",
    "receiveTimestamp": "2026-01-15T10:30:00.500Z",
    "severity": "INFO",
    "logName": "projects/my-project/logs/cloudaudit.googleapis.com%2Factivity",
    "resource": {
        "type": "cloud_run_revision",
        "labels": {
            "project_id": "my-project",
            "zone": "us-central1-a",
            "instance_id": "1234567890",
            "configuration_name": "my-service",
            "location": "europe-west1",
            "service_name": "my-service",
            "revision_name": "my-service-00001-abc",
            "subscription_id": "my-subscription",
            "topic_id": "my-topic",
            "name": "my-log-sink",
            "destination": "pubsub.googleapis.com/projects/my-project/topics/export",
        },
    },
    "protoPayload": {
        "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
        "methodName": "v1.compute.instances.start",
        "serviceName": "compute.googleapis.com",
        "authenticationInfo": {"principalEmail": "user@example.com"},
        "resourceName": "projects/my-project/zones/us-central1-a/instances/my-instance",
        "requestMetadata": {
            "callerIp": "203.0.113.50",
            "callerSuppliedUserAgent": "google-cloud-sdk gcloud/450.0.0",
        },
        "status": {},
    },
    "jsonPayload": {"message": "Instance started successfully"},
    "textPayload": "Container started on port 8080",
    "httpRequest": {
        "requestMethod": "GET",
        "requestUrl": "https://my-service.europe-west1.run.app/api/health",
        "status": 200,
        "latency": "0.025s",
        "protocol": "HTTP/1.1",
        "remoteIp": "203.0.113.50",
        "requestSize": "256",
        "responseSize": "1024",
        "serverIp": "10.0.0.1",
        "userAgent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
    },
    "trace": "projects/my-project/traces/abc123def456789",
    "spanId": "000000000000004a",
    "operation": {"id": "operation-12345"},
    "sourceLocation": {"file": "handler.py", "line": "42", "function": "handleRequest"},
    "labels": {"instanceId": "00a1b2c3d4e5f6"},
}


# ── Field Creation ────────────────────────────────────────────

def create_fields(client, namespace):
    """Create or upsert all 40 custom fields.

    Returns a dict mapping display_name -> internal_name.
    """
    field_map = {}
    for display_name in FIELD_DISPLAY_NAMES:
        details = UpsertLogAnalyticsFieldDetails()
        details.display_name = display_name
        details.data_type = "String"
        details.is_multi_valued = False
        try:
            resp = client.upsert_field(namespace, details)
            field_map[display_name] = resp.data.name
            print(f"  Field OK     {resp.data.name:12s} -> {display_name}")
        except oci.exceptions.ServiceError:
            # Field may already exist; look it up
            try:
                fields = client.list_fields(
                    namespace, display_name_contains=display_name
                ).data.items
                for f in fields:
                    if f.display_name == display_name:
                        field_map[display_name] = f.name
                        print(f"  Field EXISTS {f.name:12s} -> {display_name}")
                        break
            except Exception as exc:
                print(f"  Field ERR: {display_name}: {exc}")
    return field_map


# ── Parser Creation ───────────────────────────────────────────

PARSER_NAME = "gcpCloudLoggingJsonParser"


def create_parser(client, namespace, field_map):
    """Create or upsert the JSON parser with 44 field mappings."""
    parser_field_maps = []
    for name_or_display, json_path, seq in FIELD_MAPPINGS:
        internal = field_map.get(name_or_display, name_or_display)
        parser_field_maps.append(
            LogAnalyticsParserField(
                field=LogAnalyticsField(name=internal),
                parser_field_name=internal,
                parser_field_sequence=seq,
                storage_field_name=internal,
                structured_column_info=json_path,
            )
        )

    example_content = json.dumps(EXAMPLE_LOG, indent=2)

    parser_details = UpsertLogAnalyticsParserDetails(
        name=PARSER_NAME,
        display_name="GCP Cloud Logging JSON Parser",
        description=(
            "Parses all GCP Cloud Logging LogEntry JSON types with "
            "44 field mappings covering audit, Cloud Run, HTTP request, "
            "and metadata fields"
        ),
        type="JSON",
        language="en_US",
        encoding="UTF-8",
        is_default=True,
        is_single_line_content=False,
        is_system=False,
        header_content="$:0",
        content=example_content,
        example_content=example_content,
        field_maps=parser_field_maps,
    )

    # Get existing etag for update (optimistic concurrency)
    etag = None
    try:
        existing = client.get_parser(namespace, PARSER_NAME)
        etag = existing.headers.get("etag")
    except oci.exceptions.ServiceError:
        pass

    kwargs = {"if_match": etag} if etag else {}
    result = client.upsert_parser(namespace, parser_details, **kwargs)
    print(f"  Parser OK: {result.data.name} ({len(result.data.field_maps)} field maps)")


# ── Source Creation ───────────────────────────────────────────

SOURCE_NAME = "GCP Cloud Logging Logs"


def create_source(client, namespace, compartment_id):
    """Create the Log Analytics source referencing the parser."""
    # Check if source already exists
    try:
        existing = client.list_sources(
            namespace, compartment_id,
            name=SOURCE_NAME, is_system="ALL",
        )
        if existing.data.items:
            print(f"  Source EXISTS: {existing.data.items[0].name}")
            return
    except Exception:
        pass

    # Build source JSON for OCI CLI (SDK source upsert is complex)
    import subprocess
    import tempfile

    parsers_json = json.dumps(
        [{"name": PARSER_NAME, "isDefault": True}]
    )
    entity_types_json = json.dumps(
        [{"entityType": "oci_generic_resource",
          "entityTypeCategory": "Undefined",
          "entityTypeDisplayName": "OCI Generic Resource"}]
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as pf:
        pf.write(parsers_json)
        parsers_path = pf.name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as ef:
        ef.write(entity_types_json)
        entity_path = ef.name

    try:
        cmd = [
            "oci", "log-analytics", "source", "upsert-source",
            "--namespace-name", namespace,
            "--name", "gcpCloudLoggingSource",
            "--display-name", SOURCE_NAME,
            "--description",
            "GCP Cloud Logging structured logs from Pub/Sub via OCI Streaming",
            "--type-name", "os_file",
            "--is-system", "false",
            "--is-for-cloud", "false",
            "--parsers", f"file://{parsers_path}",
            "--entity-types", f"file://{entity_path}",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Source created: {SOURCE_NAME}")
        else:
            print(f"  Source warning: {result.stderr[:200]}")
            print("  Source may need manual creation via OCI Console or setup_oci.sh")
    finally:
        os.unlink(parsers_path)
        os.unlink(entity_path)


# ── Main ──────────────────────────────────────────────────────

def main():
    namespace = os.environ.get("LA_NAMESPACE")
    compartment_id = os.environ.get("OCI_COMPARTMENT_ID")

    if not namespace:
        print("ERROR: LA_NAMESPACE environment variable is required")
        sys.exit(1)
    if not compartment_id:
        print("ERROR: OCI_COMPARTMENT_ID environment variable is required")
        sys.exit(1)

    print(f"Log Analytics namespace: {namespace}")
    print(f"Compartment: {compartment_id[:40]}...")
    print()

    client = get_client()

    print("--- Creating custom fields (40) ---")
    field_map = create_fields(client, namespace)
    print(f"  Total: {len(field_map)} fields\n")

    print("--- Creating JSON parser (44 field mappings) ---")
    create_parser(client, namespace, field_map)
    print()

    print("--- Creating Log Analytics source ---")
    create_source(client, namespace, compartment_id)
    print()

    print("Log Analytics custom content setup complete.")


if __name__ == "__main__":
    main()
