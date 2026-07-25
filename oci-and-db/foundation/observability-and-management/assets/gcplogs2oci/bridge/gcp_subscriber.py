"""
GCP Pub/Sub pull subscriber.

Uses the google-cloud-pubsub streaming-pull API to receive messages
asynchronously and forward them to OCI Streaming via *MessageBuffer*.
"""

import json
import logging
import threading
import time

from google.cloud import pubsub_v1

from bridge.config import (
    ack_deadline_seconds,
    gcp_project_id,
    gcp_subscription,
    inactivity_timeout,
    mask,
    max_batch_bytes,
    max_batch_size,
    oci_config,
    oci_message_endpoint,
    oci_stream_ocid,
)
from bridge.oci_stream_sender import MessageBuffer, OciStreamSender

logger = logging.getLogger(__name__)


class PubSubBridge:
    """Subscribe to GCP Pub/Sub and forward messages to OCI Streaming."""

    def __init__(self):
        # OCI side
        cfg = oci_config()
        endpoint = oci_message_endpoint()
        stream_ocid = oci_stream_ocid()
        self.sender = OciStreamSender(cfg, endpoint, stream_ocid)
        self.buffer = MessageBuffer(
            self.sender,
            max_count=max_batch_size(),
            max_bytes=max_batch_bytes(),
        )

        # GCP side
        self.project_id = gcp_project_id()
        self.subscription_id = gcp_subscription()
        self.subscription_path = (
            f"projects/{self.project_id}/subscriptions/{self.subscription_id}"
        )

        # Counters
        self.processed = 0
        self.errors = 0
        self._lock = threading.Lock()
        self._last_message_time = time.time()
        self._timeout = inactivity_timeout()

        logger.info(
            "Bridge initialised | project=%s | subscription=%s | "
            "endpoint=%s | stream=%s",
            self.project_id,
            self.subscription_id,
            mask(endpoint),
            mask(stream_ocid),
        )

    # ── callback ──────────────────────────────────────────────

    @staticmethod
    def _enrich(body: str) -> str:
        """Inject cloud-provider tag so multicloud dashboards can filter by CSP."""
        try:
            obj = json.loads(body)
            obj["cloudProvider"] = "GCP"
            return json.dumps(obj, separators=(",", ":"))
        except (json.JSONDecodeError, TypeError):
            return body

    def _callback(self, message: pubsub_v1.subscriber.message.Message):
        """Handle a single Pub/Sub message."""
        try:
            body = message.data.decode("utf-8")
            if not body or body.isspace():
                logger.warning("Empty Pub/Sub message, skipping")
                message.ack()
                return

            self.buffer.add(self._enrich(body))
            message.ack()

            with self._lock:
                self.processed += 1
                self._last_message_time = time.time()

            if self.processed % 500 == 0:
                logger.info(
                    "Progress: processed=%d, sent=%d, failed=%d",
                    self.processed,
                    self.buffer.sent,
                    self.buffer.failed,
                )

        except UnicodeDecodeError as exc:
            logger.error("Failed to decode message as UTF-8: %s", exc)
            message.nack()
            with self._lock:
                self.errors += 1
        except Exception as exc:
            logger.error("Error processing message: %s", exc)
            message.nack()
            with self._lock:
                self.errors += 1

    # ── run ───────────────────────────────────────────────────

    def run(self, run_forever: bool = True):
        """Start the streaming-pull subscriber.

        If *run_forever* is False the bridge will stop after
        *inactivity_timeout* seconds without messages (useful for
        drain / one-shot scenarios).
        """
        subscriber = pubsub_v1.SubscriberClient()

        flow_control = pubsub_v1.types.FlowControl(
            max_messages=max_batch_size(),
            max_bytes=max_batch_bytes(),
        )

        streaming_pull = subscriber.subscribe(
            self.subscription_path,
            callback=self._callback,
            flow_control=flow_control,
            await_callbacks_on_shutdown=True,
        )

        logger.info(
            "Streaming pull started on %s (run_forever=%s)",
            self.subscription_path,
            run_forever,
        )

        try:
            if run_forever:
                streaming_pull.result()
            else:
                # Drain mode: stop when idle for INACTIVITY_TIMEOUT seconds
                while True:
                    time.sleep(5)
                    with self._lock:
                        idle = time.time() - self._last_message_time
                    if idle >= self._timeout:
                        logger.info(
                            "Inactivity timeout (%ds) reached, stopping",
                            self._timeout,
                        )
                        break
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            streaming_pull.cancel()
            streaming_pull.result(timeout=10)

            # Final flush
            self.buffer.flush()

            logger.info(
                "Bridge stopped | processed=%d | sent=%d | failed=%d | "
                "errors=%d | batches=%d",
                self.processed,
                self.buffer.sent,
                self.buffer.failed,
                self.errors,
                self.buffer.batches,
            )
