#!/usr/bin/env python3
"""
Event Hub Consumer - Drain all messages from Azure Event Hub and forward to OCI Streaming

Features:
- Drain mode: start from-beginning or specific ISO timestamp
- Inactivity timeout: stop automatically after N seconds without new events
- Batching: respect OCI 1MB batch size; configurable max messages per batch
- No-intervention: reads configuration from env or CLI flags

Environment variables (fallbacks for CLI flags):
- EVENTHUB_CONNECTION_STRING
- EVENTHUB_NAME
- EVENTHUB_CONSUMER_GROUP (default: $Default)
- OCI_MESSAGE_ENDPOINT  (e.g. https://cell-1.streaming.eu-frankfurt-1.oci.oraclecloud.com)
- OCI_STREAM_OCID

Usage examples:
  python eventhub_consumer.py --from-beginning
  python eventhub_consumer.py --start-iso "2025-12-01T00:00:00Z" --inactivity-timeout 30
  python eventhub_consumer.py --connection-string "..." --eventhub-name "ocitests" --from-beginning
"""

import os
import sys
import json
import time
import threading
from typing import List, Tuple, Optional
from base64 import b64encode

# Azure Event Hub (sync client to simplify draining logic)
try:
    from azure.eventhub import EventHubConsumerClient, EventData
    AZURE_EH_OK = True
except Exception as e:
    print("⚠️  Missing Azure Event Hub SDK. Install with: pip install azure-eventhub")
    AZURE_EH_OK = False

# OCI Streaming SDK
try:
    import oci
    from oci.streaming.models import PutMessagesDetails, PutMessagesDetailsEntry
    OCI_OK = True
except Exception as e:
    print("⚠️  Missing OCI SDK. Install with: pip install oci")
    OCI_OK = False

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


# ---------- OCI Sender ----------

class OciStreamSender:
    def __init__(self, endpoint: Optional[str], stream_ocid: Optional[str], profile: Optional[str] = None):
        if not OCI_OK:
            raise RuntimeError("OCI SDK not available")
        if not endpoint or not stream_ocid:
            raise RuntimeError("OCI_MESSAGE_ENDPOINT and OCI_STREAM_OCID are required")

        # Load config from ~/.oci/config
        cfg = oci.config.from_file(profile_name=profile) if profile else oci.config.from_file()
        # Build client with message endpoint
        self.client = oci.streaming.StreamClient(cfg, service_endpoint=endpoint)
        self.stream_ocid = stream_ocid

    @staticmethod
    def estimate_batch_bytes(messages: List[str]) -> int:
        # Rough estimate: sum base64-encoded payload bytes + small per-message overhead
        return sum(len(b64encode(m.encode("utf-8"))) for m in messages) + len(messages) * 50

    def send_batch(self, payloads: List[str]) -> Tuple[int, int]:
        """
        Send a batch of messages to OCI Streaming. Returns (sent, failed).
        """
        if not payloads:
            return (0, 0)

        entries = [PutMessagesDetailsEntry(value=b64encode(p.encode("utf-8")).decode("utf-8")) for p in payloads]
        req = PutMessagesDetails(messages=entries)
        resp = self.client.put_messages(self.stream_ocid, req)
        sent = 0
        failed = 0
        results = resp.data.entries or []
        for r in results:
            if r.error:
                failed += 1
            else:
                sent += 1
        return (sent, failed)

    def send_with_size_limit(self, payloads: List[str], max_bytes: int = 1024 * 1024, max_count: int = 100) -> Tuple[int, int, int]:
        """
        Chunk messages by size/count to respect OCI limits. Returns (total_sent, total_failed, batches).
        """
        total_sent = total_failed = batches = 0
        batch: List[str] = []
        for p in payloads:
            candidate = batch + [p]
            if len(candidate) > max_count or self.estimate_batch_bytes(candidate) > max_bytes:
                # flush current batch
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

# ---------- Consumer ----------

class EventHubDrainer:
    def __init__(
        self,
        connection_string: str,
        eventhub_name: str,
        consumer_group: str,
        starting_position: str,
        inactivity_timeout: int = 30,
        oci_sender: Optional[OciStreamSender] = None,
        max_batch_bytes: int = 1024 * 1024,
        max_batch_count: int = 100
    ):
        if not AZURE_EH_OK:
            raise RuntimeError("Azure Event Hub SDK not available")

        self.client = EventHubConsumerClient.from_connection_string(
            conn_str=connection_string,
            consumer_group=consumer_group or "$Default",
            eventhub_name=eventhub_name
        )
        self.starting_position = starting_position
        self.inactivity_timeout = inactivity_timeout
        self.oci_sender = oci_sender
        self.max_batch_bytes = max_batch_bytes
        self.max_batch_count = max_batch_count

        self._lock = threading.Lock()
        self._last_event_ts = time.time()
        self._stop_flag = False

        self._buffer: List[str] = []
        self.messages_processed = 0
        self.messages_sent = 0
        self.messages_failed = 0
        self.batches = 0

    def _flush_if_needed(self, force: bool = False):
        if self.oci_sender is None:
            # Print and clear buffer when forced
            if force and self._buffer:
                print(f"📦 Would send {len(self._buffer)} messages to OCI (logging only)")
                self._buffer.clear()
            return

        if not self._buffer:
            return

        if force:
            to_send = self._buffer[:]
            self._buffer.clear()
            s, f, b = self.oci_sender.send_with_size_limit(
                to_send, max_bytes=self.max_batch_bytes, max_count=self.max_batch_count
            )
            self.messages_sent += s
            self.messages_failed += f
            self.batches += b
            print(f"  ✅ Flushed {s} msgs to OCI (batches={b}, failed={f})")
            return

        # Non-forced: flush if size/count over threshold
        est = OciStreamSender.estimate_batch_bytes(self._buffer)
        if len(self._buffer) >= self.max_batch_count or est >= self.max_batch_bytes:
            to_send = self._buffer[:]
            self._buffer.clear()
            s, f, b = self.oci_sender.send_with_size_limit(
                to_send, max_bytes=self.max_batch_bytes, max_count=self.max_batch_count
            )
            self.messages_sent += s
            self.messages_failed += f
            self.batches += b
            print(f"  ✅ Flushed {s} msgs to OCI (batches={b}, failed={f})")

    def on_event(self, partition_context, event):
        if event is None:
            return
        try:
            body = event.body_as_str(encoding="utf-8")
            # Unwrap records envelope and enrich with cloud provider tag
            records = _enrich(body)
            self._last_event_ts = time.time()
            self.messages_processed += len(records)

            # Add each unwrapped record to buffer
            with self._lock:
                self._buffer.extend(records)
                # Flush opportunistically if thresholds exceeded
                self._flush_if_needed(force=False)

            # Update checkpoint
            partition_context.update_checkpoint(event)

            if self.messages_processed % 100 == 0:
                print(f"📊 Progress: processed={self.messages_processed}, sent={self.messages_sent}, failed={self.messages_failed}")

        except Exception as e:
            print(f"❌ Error processing event: {e}")
            # Try to checkpoint to avoid re-reading bad message
            try:
                partition_context.update_checkpoint(event)
            except Exception:
                pass

    def on_error(self, partition_context, error):
        if partition_context:
            print(f"❌ Partition {partition_context.partition_id} error: {error}")
        else:
            print(f"❌ General error: {error}")

    def on_partition_initialize(self, partition_context):
        print(f"🔄 Start partition {partition_context.partition_id}")

    def on_partition_close(self, partition_context, reason):
        print(f"🛑 Close partition {partition_context.partition_id}: {reason}")

    def _watchdog(self):
        # Stop receiving after inactivity_timeout seconds with no new events
        while not self._stop_flag:
            time.sleep(2)
            if time.time() - self._last_event_ts >= self.inactivity_timeout:
                print(f"⏰ No events for {self.inactivity_timeout}s, stopping receive...")
                self._stop_flag = True
                try:
                    self.client.close()
                except Exception:
                    pass
                break

    def drain(self):
        print("🔧 Consumer configuration")
        print(f"   starting_position: {self.starting_position}")
        print(f"   inactivity_timeout: {self.inactivity_timeout}s")
        print(f"   batching: max_count={self.max_batch_count}, max_bytes={self.max_batch_bytes}")
        print(f"   OCI: {'enabled' if self.oci_sender else 'disabled (logging only)'}")
        print()

        # Start watchdog thread
        t = threading.Thread(target=self._watchdog, daemon=True)
        t.start()

        try:
            # Receive blocks until close() invoked or error
            self.client.receive(
                on_event=self.on_event,
                on_error=self.on_error,
                on_partition_initialize=self.on_partition_initialize,
                on_partition_close=self.on_partition_close,
                starting_position=self.starting_position,
                max_wait_time=self.inactivity_timeout
            )
        finally:
            # Force-flush remaining messages
            with self._lock:
                self._flush_if_needed(force=True)

            print()
            print("=" * 80)
            print("✅ Drain complete" if self.messages_processed > 0 else "ℹ️  No messages consumed")
            print("=" * 80)
            print(f"   Messages processed: {self.messages_processed}")
            if self.oci_sender:
                print(f"   Messages sent to OCI: {self.messages_sent}")
                print(f"   Messages failed: {self.messages_failed}")
                print(f"   Batches: {self.batches}")
            print()

# ---------- CLI ----------

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Drain Azure Event Hub and forward all messages to OCI Streaming",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--connection-string", type=str, help="Event Hub connection string (or EVENTHUB_CONNECTION_STRING)")
    parser.add_argument("--eventhub-name", type=str, help="Event Hub name (or EVENTHUB_NAME)")
    parser.add_argument("--consumer-group", type=str, default=os.environ.get("EVENTHUB_CONSUMER_GROUP", "$Default"),
                        help="Consumer group (default: $Default)")
    start = parser.add_mutually_exclusive_group()
    start.add_argument("--from-beginning", action="store_true", help="Start from the earliest available event")
    start.add_argument("--start-iso", type=str, help="Start from ISO-8601 timestamp (e.g. 2025-12-01T00:00:00Z)")
    parser.add_argument("--inactivity-timeout", type=int, default=30, help="Stop after N seconds with no events (default 30)")
    parser.add_argument("--batch-max-bytes", type=int, default=1024 * 1024, help="Max total bytes per OCI batch (default 1048576)")
    parser.add_argument("--batch-max-count", type=int, default=100, help="Max messages per OCI batch (default 100)")
    parser.add_argument("--no-oci", action="store_true", help="Disable OCI forwarding (log only)")
    parser.add_argument("--oci-endpoint", type=str, help="OCI message endpoint (or OCI_MESSAGE_ENDPOINT env)")
    parser.add_argument("--oci-stream-ocid", type=str, help="OCI Stream OCID (or OCI_STREAM_OCID env)")
    parser.add_argument("--oci-profile", type=str, help="OCI CLI profile in ~/.oci/config")

    args = parser.parse_args()

    if not AZURE_EH_OK:
        print("❌ Azure Event Hub SDK not installed. Install with: pip install azure-eventhub")
        return 1
    if not OCI_OK and not args.no_oci:
        print("❌ OCI SDK not installed. Install with: pip install oci")
        return 1

    conn = args.connection_string or os.environ.get("EVENTHUB_CONNECTION_STRING")
    eh_name = args.eventhub_name or os.environ.get("EVENTHUB_NAME")
    if not conn or not eh_name:
        print("❌ Missing Event Hub settings. Provide --connection-string/--eventhub-name or use EVENTHUB_CONNECTION_STRING/EVENTHUB_NAME env.")
        return 1

    # Starting position
    starting_position = "@latest"
    if args.from_beginning:
        starting_position = "-1"  # earliest
    elif args.start_iso:
        starting_position = args.start_iso

    # OCI sender
    oci_sender = None
    if not args.no_oci:
        endpoint = args.oci_endpoint or os.environ.get("OCI_MESSAGE_ENDPOINT")
        stream_ocid = args.oci_stream_ocid or os.environ.get("OCI_STREAM_OCID")
        try:
            oci_sender = OciStreamSender(endpoint=endpoint, stream_ocid=stream_ocid, profile=args.oci_profile)
            print("✅ OCI sender initialized")
        except Exception as e:
            print(f"⚠️  OCI sender not initialized: {e}")
            print("    Continuing without OCI (logging only).")
            oci_sender = None

    drainer = EventHubDrainer(
        connection_string=conn,
        eventhub_name=eh_name,
        consumer_group=args.consumer_group,
        starting_position=starting_position,
        inactivity_timeout=args.inactivity_timeout,
        oci_sender=oci_sender,
        max_batch_bytes=args.batch_max_bytes,
        max_batch_count=args.batch_max_count
    )
    drainer.drain()
    return 0

if __name__ == "__main__":
    sys.exit(main())
