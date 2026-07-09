"""
OCI Streaming sender with base64 encoding and size-aware batching.

Adapted from the azurelogs2oci project's OciStreamSender. Sends batches
of JSON strings to an OCI Stream using the PutMessages API, respecting
the 1 MB / 100-message limits imposed by the service.
"""

import logging
from base64 import b64encode
from typing import List, Tuple

import oci
from oci.streaming.models import PutMessagesDetails, PutMessagesDetailsEntry

logger = logging.getLogger(__name__)


class OciStreamSender:
    """Send string payloads to OCI Streaming with automatic batching."""

    def __init__(self, config: dict, message_endpoint: str, stream_ocid: str):
        oci.config.validate_config(config)
        self.client = oci.streaming.StreamClient(
            config, service_endpoint=message_endpoint
        )
        self.stream_ocid = stream_ocid

    # ── helpers ────────────────────────────────────────────────

    @staticmethod
    def estimate_batch_bytes(messages: List[str]) -> int:
        """Estimate wire size of a batch (base64 payload + envelope overhead)."""
        return (
            sum(len(b64encode(m.encode("utf-8"))) for m in messages)
            + len(messages) * 50
        )

    # ── sending ───────────────────────────────────────────────

    def send_batch(self, payloads: List[str]) -> Tuple[int, int]:
        """Send a single batch, return (sent, failed)."""
        if not payloads:
            return (0, 0)
        entries = [
            PutMessagesDetailsEntry(
                value=b64encode(p.encode("utf-8")).decode("utf-8")
            )
            for p in payloads
        ]
        resp = self.client.put_messages(
            self.stream_ocid, PutMessagesDetails(messages=entries)
        )
        sent = failed = 0
        for entry in resp.data.entries or []:
            if getattr(entry, "error", None):
                failed += 1
                logger.warning("OCI put_messages entry error: %s", entry.error)
            else:
                sent += 1
        return (sent, failed)

    def send_with_limits(
        self,
        payloads: List[str],
        max_bytes: int,
        max_count: int,
    ) -> Tuple[int, int, int]:
        """Split *payloads* into batches that respect *max_bytes* / *max_count*."""
        total_sent = total_failed = batches = 0
        batch: List[str] = []
        for p in payloads:
            candidate = batch + [p]
            if (
                len(candidate) > max_count
                or self.estimate_batch_bytes(candidate) > max_bytes
            ):
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


class MessageBuffer:
    """Accumulate messages and auto-flush to OCI when thresholds are hit."""

    def __init__(
        self,
        sender: OciStreamSender,
        max_count: int,
        max_bytes: int,
    ):
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
        if (
            force
            or len(self.buf) >= self.max_count
            or OciStreamSender.estimate_batch_bytes(self.buf) >= self.max_bytes
        ):
            s, f, b = self.sender.send_with_limits(
                self.buf, self.max_bytes, self.max_count
            )
            self.sent += s
            self.failed += f
            self.batches += b
            self.buf.clear()
            logger.info("Flushed to OCI: sent=%d, failed=%d, batches=%d", s, f, b)

    def flush(self):
        self._flush_if_needed(force=True)
