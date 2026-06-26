import json
import logging
import os
import time
from base64 import b64encode
from typing import List, Tuple

import azure.functions as func

# Azure Event Hubs (sync client)
try:
    from azure.eventhub import EventHubConsumerClient
    EH_SDK_OK = True
except Exception as e:
    EH_SDK_OK = False
    logging.error("Azure Event Hubs SDK missing. Add 'azure-eventhub' to requirements.txt")

# OCI SDK
try:
    import oci
    from oci.streaming.models import PutMessagesDetails, PutMessagesDetailsEntry
    OCI_SDK_OK = True
except Exception as e:
    OCI_SDK_OK = False
    logging.error("OCI SDK missing. Add 'oci' to requirements.txt")

logging.getLogger('azure.core.pipeline.policies.http_logging_policy').setLevel(logging.ERROR)

# Batch defaults
DEFAULT_MAX_BATCH_COUNT = int(os.getenv('MaxBatchSize', 100))
DEFAULT_MAX_BATCH_BYTES = int(os.getenv('MaxBatchBytes', 1024 * 1024))  # 1MB
DEFAULT_INACTIVITY_TIMEOUT = int(os.getenv('InactivityTimeout', 10))


def parse_key(key_input: str) -> str:
    """Parse OCI private key from single-line format into PEM, tolerating trailing text"""
    try:
        import re
        import textwrap

        # Normalize escaped newlines and strip outer whitespace
        normalized = (key_input or "").replace("\\n", "\n").strip()

        begin_match = re.search(r"-----BEGIN [A-Z ]+-----", normalized)
        end_match = re.search(r"-----END [A-Z ]+-----", normalized)
        if not begin_match or not end_match:
            raise ValueError("BEGIN/END markers not found")

        begin_line = begin_match.group()
        end_line = end_match.group()

        # Only keep content between the markers, discard anything after the end marker
        key_block = normalized[begin_match.end() : end_match.start()]

        # Handle encrypted keys if present
        encr_lines = ""
        proc_type_line = re.search(r"Proc-Type: [^\n]+", key_block)
        dec_info_line = re.search(r"DEK-Info: [^\n]+", key_block)
        if proc_type_line:
            encr_lines += proc_type_line.group().strip() + "\n"
            key_block = key_block.replace(proc_type_line.group(), "")
        if dec_info_line:
            encr_lines += dec_info_line.group().strip() + "\n"
            key_block = key_block.replace(dec_info_line.group(), "")

        # Remove whitespace and wrap to PEM-friendly line lengths
        body_compact = re.sub(r"\s+", "", key_block)
        wrapped_body = "\n".join(textwrap.wrap(body_compact, 64))

        parts = [begin_line]
        if encr_lines:
            parts.append(encr_lines.rstrip("\n"))
        parts.append(wrapped_body)
        parts.append(end_line)
        return "\n".join(parts)
    except Exception:
        raise Exception("Error while reading private key.")


def get_oci_config_from_env() -> dict:
    """Build OCI config dict from environment variables (Function App settings)"""
    cfg = {
        "user": os.environ['user'],
        "key_content": parse_key(os.environ['key_content']),
        "pass_phrase": os.environ.get('pass_phrase', ''),
        "fingerprint": os.environ['fingerprint'],
        "tenancy": os.environ['tenancy'],
        "region": os.environ['region']
    }
    return cfg


class OciStreamSender:
    """Minimal OCI Stream sender with base64 encoding and size-aware batching"""

    def __init__(self, config: dict, message_endpoint: str, stream_ocid: str):
        oci.config.validate_config(config)
        self.client = oci.streaming.StreamClient(config, service_endpoint=message_endpoint)
        self.stream_ocid = stream_ocid

    @staticmethod
    def estimate_batch_bytes(messages: List[str]) -> int:
        # Estimate based on base64-encoded payloads + small overhead
        return sum(len(b64encode(m.encode('utf-8'))) for m in messages) + len(messages) * 50

    def send_batch(self, payloads: List[str]) -> Tuple[int, int]:
        if not payloads:
            return (0, 0)
        entries = [PutMessagesDetailsEntry(value=b64encode(p.encode('utf-8')).decode('utf-8')) for p in payloads]
        req = PutMessagesDetails(messages=entries)
        resp = self.client.put_messages(self.stream_ocid, req)
        sent = failed = 0
        for entry in (resp.data.entries or []):
            if getattr(entry, 'error', None):
                failed += 1
            else:
                sent += 1
        return (sent, failed)

    def send_with_limits(self, payloads: List[str], max_bytes: int, max_count: int) -> Tuple[int, int, int]:
        total_sent = total_failed = batches = 0
        batch: List[str] = []
        for p in payloads:
            candidate = batch + [p]
            if len(candidate) > max_count or self.estimate_batch_bytes(candidate) > max_bytes:
                s, f = self.send_batch(batch)
                total_sent += s
                total_failed += f
                batches += 1
                batch = [p]
            else:
                batch = candidate
        if batch:
            s, f = self.send_batch(batch)
            total_sent += s
            total_failed += f
            batches += 1
        return (total_sent, total_failed, batches)


class HubBuffer:
    """Buffer messages and flush to OCI by count/size or on-demand"""

    def __init__(self, sender: OciStreamSender, max_count: int, max_bytes: int):
        self.sender = sender
        self.max_count = max_count
        self.max_bytes = max_bytes
        self.buf: List[str] = []
        self.sent = 0
        self.failed = 0
        self.batches = 0

    def add(self, payload: str):
        self.buf.append(payload)
        self._flush_if_needed()

    def _flush_if_needed(self, force: bool = False):
        if not self.buf:
            return
        if force or len(self.buf) >= self.max_count or OciStreamSender.estimate_batch_bytes(self.buf) >= self.max_bytes:
            s, f, b = self.sender.send_with_limits(self.buf, self.max_bytes, self.max_count)
            self.sent += s
            self.failed += f
            self.batches += b
            self.buf.clear()
            logging.info(f"Flushed to OCI: sent={s}, failed={f}, batches={b}")

    def flush(self):
        self._flush_if_needed(force=True)


# Removed unused polling functions - Event Hub trigger handles this automatically


def _enrich(body: str) -> List[str]:
    """Unwrap Azure Event Hub records envelope and inject cloud-provider tag.

    Azure diagnostic settings wrap log entries in {"records": [...]}.
    This function unwraps the array so each record is a standalone JSON
    object with cloudProvider injected, matching the OCI LA parser paths.
    """
    try:
        obj = json.loads(body)
        # Azure Event Hub diagnostic settings envelope
        if isinstance(obj, dict) and "records" in obj and isinstance(obj["records"], list):
            results = []
            for record in obj["records"]:
                if isinstance(record, dict):
                    record["cloudProvider"] = "Azure"
                    results.append(json.dumps(record, separators=(",", ":")))
            return results if results else [body]
        # Single record (no envelope)
        obj["cloudProvider"] = "Azure"
        return [json.dumps(obj, separators=(",", ":"))]
    except (json.JSONDecodeError, TypeError):
        return [body]


def mask(value: str, keep: int = 6) -> str:
    """Mask secrets for logging."""
    if not value:
        return ""
    if len(value) <= keep:
        return "***"
    return f"{value[:keep]}...***"


def validate_env() -> Tuple[str, str]:
    """Validate OCI environment variables only (Event Hub binding is handled by trigger)"""
    endpoint = os.getenv("MessageEndpoint") or os.getenv("OCI_MESSAGE_ENDPOINT")
    stream_ocid = os.getenv("StreamOcid") or os.getenv("OCI_STREAM_OCID")
    if not endpoint or not stream_ocid:
        raise RuntimeError("Missing MessageEndpoint/StreamOcid (or OCI_MESSAGE_ENDPOINT/OCI_STREAM_OCID) application settings")
    if "streampool" in stream_ocid:
        raise RuntimeError("StreamOcid points to a Stream Pool. Use the Stream OCID (ocid1.stream...) instead.")

    return endpoint, stream_ocid


def main(events: List[func.EventHubEvent]) -> None:
    """Event Hub-triggered function: process events in real-time and forward to OCI Streaming"""
    event_count = len(events) if events else 0
    logging.info(f"Event Hub trigger: received {event_count} events")

    if event_count == 0:
        logging.info("No events to process")
        return

    # Debug: Log environment variables (masked for security)
    logging.info(f"Environment check - MessageEndpoint: {'✓' if os.getenv('MessageEndpoint') else '✗'}")
    logging.info(f"Environment check - StreamOcid: {'✓' if os.getenv('StreamOcid') else '✗'}")
    logging.info(f"Environment check - user: {'✓' if os.getenv('user') else '✗'}")
    logging.info(f"Environment check - key_content: {'✓' if os.getenv('key_content') else '✗'}")
    logging.info(f"Environment check - fingerprint: {'✓' if os.getenv('fingerprint') else '✗'}")
    logging.info(f"Environment check - tenancy: {'✓' if os.getenv('tenancy') else '✗'}")
    logging.info(f"Environment check - region: {'✓' if os.getenv('region') else '✗'}")
    logging.info(f"Environment check - EventHubName: {os.getenv('EventHubName', '')}")
    logging.info(f"Environment check - EventHubConsumerGroup: {os.getenv('EventHubConsumerGroup', '')}")

    if not OCI_SDK_OK:
        logging.error("OCI SDK not available. Ensure 'oci' is installed.")
        return

    try:
        # Validate env and build OCI sender
        logging.info("Validating OCI environment configuration...")
        endpoint, stream_ocid = validate_env()
        logging.info(f"OCI config validated - endpoint: {mask(endpoint)}, stream: {mask(stream_ocid)}")

        logging.info("Building OCI configuration...")
        cfg = get_oci_config_from_env()
        logging.info("OCI configuration built successfully")

        logging.info("Initializing OCI Stream sender...")
        sender = OciStreamSender(cfg, endpoint, stream_ocid)
        logging.info("OCI Stream sender initialized successfully")

        max_batch_count = int(os.getenv("MaxBatchSize", DEFAULT_MAX_BATCH_COUNT))
        max_batch_bytes = int(os.getenv("MaxBatchBytes", DEFAULT_MAX_BATCH_BYTES))

        logging.info(
            f"Config summary | endpoint={mask(endpoint)} | stream={mask(stream_ocid)} | "
            f"max_batch_count={max_batch_count} | max_batch_bytes={max_batch_bytes}"
        )

        # Process events with optimized batching
        logging.info(f"Initializing buffer with max_count={max_batch_count}, max_bytes={max_batch_bytes}")
        buffer = HubBuffer(sender, max_count=max_batch_count, max_bytes=max_batch_bytes)
        processed_count = 0
        error_count = 0

        logging.info("Starting event processing...")
        for i, event in enumerate(events):
            try:
                logging.debug(f"Processing event {i+1}/{event_count}")

                # Decode event body as UTF-8 string (Azure Event Hub events contain the log data)
                body = event.get_body().decode('utf-8')
                logging.debug(f"Event {i+1} decoded successfully, size: {len(body)} bytes")

                # Validate the event data is not empty
                if not body or body.isspace():
                    logging.warning(f"Event {i+1}: Received empty event body, skipping")
                    continue

                # Log first few characters for debugging (truncated)
                preview = body[:100].replace('\n', ' ').replace('\r', ' ')
                logging.debug(f"Event {i+1} content preview: {preview}{'...' if len(body) > 100 else ''}")

                # Unwrap records envelope and enrich with cloud provider tag
                records = _enrich(body)

                # Add each unwrapped record to buffer
                for record in records:
                    buffer.add(record)
                processed_count += len(records)

                logging.debug(f"Event {i+1}: {len(records)} record(s) added to buffer. Total processed: {processed_count}")

            except UnicodeDecodeError as e:
                error_count += 1
                logging.error(f"Event {i+1}: Failed to decode event body as UTF-8: {e}")
            except Exception as e:
                error_count += 1
                logging.error(f"Event {i+1}: Error processing individual event: {e}")

        logging.info(f"Event processing complete. Processed: {processed_count}, Errors: {error_count}")

        # Final flush to ensure all messages are sent
        logging.info("Performing final buffer flush...")
        buffer.flush()

        total_sent = buffer.sent
        total_failed = buffer.failed + error_count
        total_batches = buffer.batches

        logging.info(
            f"Event Hub trigger complete: processed={processed_count}, "
            f"sent={total_sent}, failed={total_failed}, batches={total_batches}"
        )

        # Log success/failure summary
        if total_failed == 0 and processed_count > 0:
            logging.info("✅ All events successfully forwarded to OCI Streaming")
        elif total_failed > 0:
            logging.warning(f"⚠️  {total_failed} events failed to send to OCI Streaming")
        else:
            logging.warning("⚠️  No events were successfully processed")

    except Exception as e:
        logging.exception(f"Event Hub function error: {e}")
        raise  # Re-raise to mark function as failed
