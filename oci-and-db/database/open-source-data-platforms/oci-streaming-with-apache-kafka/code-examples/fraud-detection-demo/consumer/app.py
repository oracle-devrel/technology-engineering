import csv
import io
import json
import logging
import math
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import oci
import requests
import yaml
from confluent_kafka import Consumer, KafkaException, Producer
from flask import Flask, jsonify
from oci.monitoring.models import Datapoint, MetricDataDetails, PostMetricDataDetails
from oci.signer import Signer


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s service=scoring-consumer %(message)s",
)
logger = logging.getLogger("scoring-consumer")

app = Flask(__name__)
state_lock = threading.Lock()

# Shared in-memory runtime status exposed by Flask endpoints.
state: Dict[str, Any] = {
    "running": False,
    "stop_requested": False,
    "messages_consumed": 0,
    "messages_scored": 0,
    "fraud_published": 0,
    "non_fraud_count": 0,
    "model_failures": 0,
    "fraud_publish_failures": 0,
    "object_storage_failures": 0,
    "metrics_publish_failures": 0,
    "last_score": None,
    "last_error": None,
    "last_object_storage_write": None,
    "last_metrics_publish_time": None,
    "thread": None,
}

MODEL_INPUT_FIELDS = [
    "Unnamed: 0",
    "trans_date_trans_time",
    "cc_num",
    "merchant",
    "category",
    "amt",
    "first",
    "last",
    "gender",
    "street",
    "city",
    "state",
    "zip",
    "lat",
    "long",
    "city_pop",
    "job",
    "dob",
    "trans_num",
    "unix_time",
    "merch_lat",
    "merch_long",
    "merch_zipcode",
]

CSV_COLUMNS = [
    "trans_date_trans_time",
    "cc_num",
    "merchant",
    "category",
    "amt",
    "gender",
    "city",
    "state",
    "zip",
    "lat",
    "long",
    "city_pop",
    "job",
    "dob",
    "trans_num",
    "unix_time",
    "merch_lat",
    "merch_long",
    "merch_zipcode",
    "is_fraud",
    "simulation_id",
    "simulation_ts",
    "score",
    "predicted_fraud",
    "scored_at",
]

BASE_METRIC_NAMES = [
    "scored_event_count",
    "fraud_event_count",
    "non_fraud_event_count",
    "high_value_fraud_count",
    "model_failure_count",
    "fraud_publish_failure_count",
    "object_storage_failure_count",
]


# Thread-safe bulk update for runtime state.
def update_state(**kwargs: Any) -> None:
    with state_lock:
        state.update(kwargs)


# Thread-safe counter increment for runtime metrics in /status.
def increment_state(key: str, amount: int = 1) -> None:
    with state_lock:
        state[key] = int(state.get(key, 0)) + amount


# Return a required config section or fail with a clear message.
def require_section(cfg: Dict[str, Any], section_name: str) -> Dict[str, Any]:
    # Fail fast with a friendly message instead of a raw KeyError later.
    section = cfg.get(section_name)
    if not isinstance(section, dict):
        raise ValueError(f"Missing or invalid config section: {section_name}")
    return section


# Convert values to finite floats, returning None for invalid numbers.
def normalize_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        parsed = float(value)
        if math.isnan(parsed) or math.isinf(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


# Buffers scored events and writes partitioned CSV objects in batches.
class CsvBatchWriter:
    def __init__(
        self,
        object_storage_client: oci.object_storage.ObjectStorageClient,
        namespace: str,
        bucket_name: str,
        prefix: str,
        flush_every_records: int,
        flush_every_seconds: int,
    ) -> None:
        self.object_storage_client = object_storage_client
        self.namespace = namespace
        self.bucket_name = bucket_name
        self.prefix = prefix.rstrip("/")
        self.flush_every_records = max(1, flush_every_records)
        self.flush_every_seconds = max(1, flush_every_seconds)
        self.buffer: List[Dict[str, Any]] = []
        self.last_flush_epoch = time.time()

    def flush_if_needed(self) -> Optional[Tuple[str, int, float]]:
        # Write the current CSV batch when size or time threshold is reached.
        if not self.buffer:
            return None
        should_flush = (
            len(self.buffer) >= self.flush_every_records
            or (time.time() - self.last_flush_epoch) >= self.flush_every_seconds
        )
        if not should_flush:
            return None
        return self.flush()

    def flush(self) -> Optional[Tuple[str, int, float]]:
        # Write buffered scored events to Object Storage as one CSV object.
        if not self.buffer:
            return None
        now = datetime.now(timezone.utc)
        key = f"{self.prefix}/scored-events-{now:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4().hex}.csv"

        # Serialize once per batch to reduce Object Storage request overhead.
        csv_bytes = self._to_csv_bytes(self.buffer)
        started = time.perf_counter()
        self.object_storage_client.put_object(
            namespace_name=self.namespace,
            bucket_name=self.bucket_name,
            object_name=key,
            put_object_body=csv_bytes,
            content_type="text/csv",
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        rows = len(self.buffer)
        self.buffer.clear()
        self.last_flush_epoch = time.time()
        return key, rows, latency_ms

    def _to_csv_bytes(self, rows: List[Dict[str, Any]]) -> bytes:
        # Convert scored events to CSV bytes using the configured output columns.
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            csv_row = []
            for column in CSV_COLUMNS:
                value = row.get(column)
                if value is None or (isinstance(value, float) and (math.isnan(value) or math.isinf(value))):
                    value = ""
                else:
                    value = str(value)
                csv_row.append(value)
            writer.writerow(csv_row)
        return output.getvalue().encode("utf-8")


# Aggregates per-window counters/latencies before OCI Monitoring publish.
class MetricsAggregator:
    def __init__(
        self,
        compartment_id: str,
        namespace: str,
        environment: str,
        high_value_threshold: float,
    ) -> None:
        self.compartment_id = compartment_id
        self.namespace = namespace
        self.environment = environment
        self.high_value_threshold = high_value_threshold
        self.reset_window()

    def reset_window(self) -> None:
        # Reset per-window counters after metrics are published.
        self.counters = {name: 0 for name in BASE_METRIC_NAMES}
        self.model_latency_sum_ms = 0.0
        self.model_latency_count = 0
        self.object_storage_latency_sum_ms = 0.0
        self.object_storage_latency_count = 0
        self.publish_latency_sum_ms = 0.0
        self.publish_latency_count = 0

    def record_scored(self, predicted_fraud: bool, amount: Optional[float], model_latency_ms: float) -> None:
        # Record one successfully scored event in the current metrics window.
        # Every successfully scored event contributes to scored_event_count.
        self.counters["scored_event_count"] += 1
        self.model_latency_sum_ms += model_latency_ms
        self.model_latency_count += 1
        if predicted_fraud:
            self.counters["fraud_event_count"] += 1
            if amount is not None and amount >= self.high_value_threshold:
                self.counters["high_value_fraud_count"] += 1
        else:
            self.counters["non_fraud_event_count"] += 1

    def _average(self, total: float, count: int) -> Optional[float]:
        # Return a rounded average, or None when no samples were recorded.
        if count <= 0:
            return None
        return round(total / count, 3)

    def build_metric_data(self) -> List[MetricDataDetails]:
        # Build OCI Monitoring payloads from the current metrics window.
        now = datetime.now(timezone.utc)
        dimensions = {
            "environment": self.environment,
            "service": "scoring-consumer",
        }

        metric_data: List[MetricDataDetails] = []
        for metric_name in BASE_METRIC_NAMES:
            metric_data.append(
                MetricDataDetails(
                    namespace=self.namespace,
                    compartment_id=self.compartment_id,
                    name=metric_name,
                    dimensions=dimensions,
                    datapoints=[Datapoint(timestamp=now, value=self.counters[metric_name])],
                )
            )

        optional_metrics = {
            "model_latency_ms_avg": self._average(self.model_latency_sum_ms, self.model_latency_count),
            "object_storage_write_latency_ms_avg": self._average(
                self.object_storage_latency_sum_ms, self.object_storage_latency_count
            ),
            "fraud_publish_latency_ms_avg": self._average(
                self.publish_latency_sum_ms, self.publish_latency_count
            ),
        }
        for name, value in optional_metrics.items():
            if value is None:
                continue
            metric_data.append(
                MetricDataDetails(
                    namespace=self.namespace,
                    compartment_id=self.compartment_id,
                    name=name,
                    dimensions=dimensions,
                    datapoints=[Datapoint(timestamp=now, value=value)],
                )
            )
        return metric_data


# Publish the current metrics window to OCI Monitoring.
def post_metrics(monitoring_client: oci.monitoring.MonitoringClient, metrics: MetricsAggregator) -> None:
    details = PostMetricDataDetails(metric_data=metrics.build_metric_data())
    response = monitoring_client.post_metric_data(details)
    failed_count = getattr(response.data, "failed_metrics_count", None)
    if failed_count not in (None, 0):
        raise RuntimeError(f"OCI Monitoring failed_metrics_count={failed_count}")


# Consume Kafka events, score them, publish results, and write audit output.
def scoring_loop() -> None:
    consumer: Optional[Consumer] = None
    producer: Optional[Producer] = None
    model_session: Optional[requests.Session] = None
    csv_writer: Optional[CsvBatchWriter] = None
    metrics: Optional[MetricsAggregator] = None
    try:
        with open("app_config.yaml", "r", encoding="utf-8") as config_file:
            cfg = yaml.safe_load(config_file) or {}

        kafka_props: Dict[str, str] = {}
        with open("kafka_client.properties", "r", encoding="utf-8") as props_file:
            for line in props_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                kafka_props[key.strip()] = value.strip()

        kafka_cfg = require_section(cfg, "kafka")
        model_cfg = require_section(cfg, "model")
        oci_cfg = require_section(cfg, "oci")
        object_storage_cfg = require_section(cfg, "object_storage")
        monitoring_cfg = cfg.get("monitoring") or {}

        threshold = float(model_cfg["threshold"])
        metrics_flush_seconds = int(monitoring_cfg.get("metrics_flush_seconds", 60))
        # Validate required runtime config values once at startup.
        required_values = {
            "kafka.input_topic": kafka_cfg.get("input_topic"),
            "kafka.output_topic": kafka_cfg.get("output_topic"),
            "model.endpoint": model_cfg.get("endpoint"),
            "oci.compartment_id": oci_cfg.get("compartment_id"),
            "object_storage.bucket_name": object_storage_cfg.get("bucket_name"),
            "oci.metric_namespace": oci_cfg.get("metric_namespace"),
        }
        missing = [name for name, value in required_values.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration values: {', '.join(missing)}")

        oci_config = oci.config.from_file(
            file_location=oci_cfg["config_file"],
            profile_name=oci_cfg["profile"],
        )
        if oci_cfg.get("region"):
            oci_config["region"] = oci_cfg["region"]

        signer = Signer(
            tenancy=oci_config["tenancy"],
            user=oci_config["user"],
            fingerprint=oci_config["fingerprint"],
            private_key_file_location=oci_config["key_file"],
            pass_phrase=oci_config.get("pass_phrase"),
        )
        model_session = requests.Session()
        monitoring_client = oci.monitoring.MonitoringClient(oci_config)
        monitoring_client.base_client.set_region(oci_config["region"])
        # Custom metrics use the telemetry ingestion endpoint, not the normal monitoring endpoint.
        monitoring_client.base_client.endpoint = f"https://telemetry-ingestion.{oci_config['region']}.oraclecloud.com"
        object_storage_client = oci.object_storage.ObjectStorageClient(oci_config)

        bootstrap_servers = kafka_props.get("bootstrap.servers")
        if not bootstrap_servers:
            raise ValueError("Missing required Kafka property: bootstrap.servers")
        kafka_base_conf = {
            "bootstrap.servers": bootstrap_servers,
            "security.protocol": kafka_props.get("security.protocol", "SASL_SSL"),
            "sasl.mechanism": kafka_props.get("sasl.mechanism"),
            "sasl.username": kafka_props.get("sasl.username"),
            "sasl.password": kafka_props.get("sasl.password"),
        }
        consumer = Consumer(
            {
                **kafka_base_conf,
                "group.id": kafka_cfg["group_id"],
                "auto.offset.reset": kafka_cfg.get("auto_offset_reset", "earliest"),
                "enable.auto.commit": False,
            }
        )
        producer = Producer(
            {
                **kafka_base_conf,
                "acks": "all",
                "retries": 10,
            }
        )
        consumer.subscribe([kafka_cfg["input_topic"]])

        # Resolve namespace dynamically from tenancy to avoid hardcoding.
        os_namespace = object_storage_client.get_namespace().data
        csv_writer = CsvBatchWriter(
            object_storage_client=object_storage_client,
            namespace=os_namespace,
            bucket_name=object_storage_cfg["bucket_name"],
            prefix=object_storage_cfg.get("prefix", "scored-events"),
            flush_every_records=int(object_storage_cfg.get("flush_every_records", 500)),
            flush_every_seconds=int(object_storage_cfg.get("flush_every_seconds", 30)),
        )
        metrics = MetricsAggregator(
            compartment_id=oci_cfg["compartment_id"],
            namespace=oci_cfg["metric_namespace"],
            environment=oci_cfg.get("environment", "dev"),
            high_value_threshold=float(monitoring_cfg.get("high_value_threshold", 1000)),
        )

        next_metrics_flush_epoch = time.time() + metrics_flush_seconds
        logger.info(
            "Scoring consumer started input_topic=%s output_topic=%s threshold=%.4f",
            kafka_cfg["input_topic"],
            kafka_cfg["output_topic"],
            threshold,
        )

        # Processing order per event:
        # 1) consume
        # 2) score
        # 3) enrich event
        # 4) publish fraud-only
        # 5) buffer CSV
        # 6) flush object storage as needed
        # 7) update counters
        # 8) commit offset
        while True:
            with state_lock:
                if state["stop_requested"]:
                    break

            # Publish custom metrics on a timer so the hot path does not call OCI on every event.
            now = time.time()
            if now >= next_metrics_flush_epoch:
                try:
                    post_metrics(monitoring_client, metrics)
                    # Metrics are emitted per flush window, not cumulative forever.
                    metrics.reset_window()
                    update_state(last_metrics_publish_time=datetime.now(timezone.utc).isoformat())
                except Exception as exc:
                    increment_state("metrics_publish_failures")
                    update_state(last_error=f"Metrics publish failed: {exc}")
                    logger.exception("Failed publishing custom metrics")
                next_metrics_flush_epoch = now + metrics_flush_seconds

            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                raise KafkaException(msg.error())

            increment_state("messages_consumed")
            try:
                incoming_event = json.loads(msg.value())
            except Exception as exc:
                update_state(last_error=f"Invalid JSON payload: {exc}")
                logger.exception("Invalid JSON payload from Kafka")
                # Bad payloads are committed to avoid poison-message loops.
                consumer.commit(message=msg, asynchronous=False)
                continue

            try:
                payload = {}
                for field in MODEL_INPUT_FIELDS:
                    value = incoming_event.get(field)
                    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                        value = None
                    payload[field] = value
                started = time.perf_counter()
                response = model_session.post(
                    model_cfg["endpoint"],
                    headers={"Content-Type": "application/json", "Accept": "application/json"},
                    json=payload,
                    auth=signer,
                    timeout=30,
                )
                model_latency_ms = (time.perf_counter() - started) * 1000.0
                response.raise_for_status()
                result = response.json()
                prediction = result.get("prediction") if isinstance(result, dict) else None
                score = normalize_float(prediction[0]) if isinstance(prediction, list) and prediction else None
                if score is None:
                    logger.warning("Model response did not include a valid score. response=%s", result)
            except Exception as exc:
                increment_state("model_failures")
                metrics.counters["model_failure_count"] += 1
                update_state(last_error=f"Model scoring failed: {exc}")
                logger.exception("Model scoring failed")
                # Keep the demo moving; record the failure and skip this event.
                consumer.commit(message=msg, asynchronous=False)
                continue

            predicted_fraud = bool(score is not None and score >= threshold)
            scored_event = dict(incoming_event)
            scored_event["score"] = score
            scored_event["predicted_fraud"] = predicted_fraud
            scored_event["scored_at"] = datetime.now(timezone.utc).isoformat()

            publish_latency_ms: Optional[float] = None
            if predicted_fraud:
                try:
                    started = time.perf_counter()
                    key_field = kafka_cfg.get("key_field", "cc_num")
                    key = str(
                        scored_event.get(key_field)
                        or scored_event.get("trans_num")
                        or scored_event.get("simulation_id")
                        or "unknown"
                    )
                    delivery_error: Dict[str, Optional[str]] = {"error": None}

                    def delivery_callback(err: Optional[KafkaException], _msg: Any) -> None:
                        if err is not None:
                            delivery_error["error"] = str(err)

                    # Wait for the delivery result before committing the source Kafka offset.
                    producer.produce(
                        topic=kafka_cfg["output_topic"],
                        key=key,
                        value=json.dumps(scored_event, default=str),
                        callback=delivery_callback,
                    )
                    producer.poll(0)
                    outstanding = producer.flush(10)
                    if outstanding > 0:
                        raise RuntimeError(f"Fraud producer flush timed out with outstanding={outstanding}")
                    if delivery_error["error"]:
                        raise RuntimeError(delivery_error["error"])
                    publish_latency_ms = (time.perf_counter() - started) * 1000.0
                except Exception as exc:
                    increment_state("fraud_publish_failures")
                    metrics.counters["fraud_publish_failure_count"] += 1
                    update_state(last_error=f"Fraud publish failed: {exc}")
                    logger.exception("Fraud publish failed trans_num=%s", scored_event.get("trans_num"))
                    # Keep the demo moving; record the failure and skip this event.
                    consumer.commit(message=msg, asynchronous=False)
                    continue

            csv_writer.buffer.append(scored_event)
            try:
                # Object Storage writes are batched, and successful batches are completed before commit.
                flush_result = csv_writer.flush_if_needed()
                if flush_result is not None:
                    object_name, record_count, os_latency_ms = flush_result
                    metrics.object_storage_latency_sum_ms += os_latency_ms
                    metrics.object_storage_latency_count += 1
                    update_state(
                        last_object_storage_write={
                            "object_name": object_name,
                            "record_count": record_count,
                            "written_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
            except Exception as exc:
                increment_state("object_storage_failures")
                metrics.counters["object_storage_failure_count"] += 1
                if csv_writer.buffer:
                    csv_writer.buffer.pop()
                update_state(last_error=f"Object Storage write failed: {exc}")
                logger.exception("Object Storage batch flush failed")
                # Keep the demo moving; record the failure and skip this event.
                consumer.commit(message=msg, asynchronous=False)
                continue

            increment_state("messages_scored")
            update_state(last_score=score, last_error=None)
            if predicted_fraud:
                increment_state("fraud_published")
            else:
                increment_state("non_fraud_count")

            amount = normalize_float(scored_event.get("amt"))
            metrics.record_scored(
                predicted_fraud=predicted_fraud,
                amount=amount,
                model_latency_ms=model_latency_ms,
            )
            if publish_latency_ms is not None:
                metrics.publish_latency_sum_ms += publish_latency_ms
                metrics.publish_latency_count += 1

            # On success, commit after processing completes.
            consumer.commit(message=msg, asynchronous=False)

        # Graceful shutdown: flush producer, flush any remaining CSV rows, publish final metric window.
        if csv_writer is not None:
            try:
                flush_result = csv_writer.flush()
                if flush_result is not None and metrics is not None:
                    object_name, record_count, os_latency_ms = flush_result
                    metrics.object_storage_latency_sum_ms += os_latency_ms
                    metrics.object_storage_latency_count += 1
                    update_state(
                        last_object_storage_write={
                            "object_name": object_name,
                            "record_count": record_count,
                            "written_at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
            except Exception as exc:
                increment_state("object_storage_failures")
                if metrics is not None:
                    metrics.counters["object_storage_failure_count"] += 1
                update_state(last_error=f"Shutdown Object Storage flush failed: {exc}")
                logger.exception("Shutdown Object Storage flush failed")
        if metrics is not None:
            try:
                post_metrics(monitoring_client, metrics)
                update_state(last_metrics_publish_time=datetime.now(timezone.utc).isoformat())
            except Exception as exc:
                increment_state("metrics_publish_failures")
                update_state(last_error=f"Shutdown metrics publish failed: {exc}")
                logger.exception("Shutdown metrics publish failed")

    except Exception as exc:
        update_state(last_error=f"Fatal scoring loop error: {exc}")
        logger.exception("Fatal scoring loop error")
    finally:
        if producer is not None:
            try:
                producer.flush(10)
            except Exception:
                logger.exception("Producer flush during shutdown failed")
        if consumer is not None:
            try:
                consumer.close()
            except Exception:
                logger.exception("Consumer close during shutdown failed")
        if model_session is not None:
            model_session.close()
        update_state(running=False, stop_requested=False)


@app.route("/start", methods=["POST"])
# Start the background scoring consumer.
def start() -> Any:
    if state["running"]:
        return jsonify({"message": "Scoring consumer already running"}), 400

    update_state(
        running=True,
        stop_requested=False,
        messages_consumed=0,
        messages_scored=0,
        fraud_published=0,
        non_fraud_count=0,
        model_failures=0,
        fraud_publish_failures=0,
        object_storage_failures=0,
        metrics_publish_failures=0,
        last_score=None,
        last_error=None,
        last_object_storage_write=None,
        last_metrics_publish_time=None,
    )
    worker = threading.Thread(target=scoring_loop, daemon=True)
    update_state(thread=worker)
    worker.start()

    return jsonify(
        {
            "message": "Scoring consumer started",
        }
    )


@app.route("/stop", methods=["POST"])
# Request a graceful stop and wait briefly for final flushes.
def stop() -> Any:
    if not state["running"]:
        return jsonify({"message": "Scoring consumer is not running"}), 400
    update_state(stop_requested=True)
    # Wait for worker shutdown to complete normal flush path.
    worker = state.get("thread")
    if isinstance(worker, threading.Thread):
        worker.join(timeout=30)
        if worker.is_alive():
            return jsonify({"message": "Stop requested, worker still shutting down"}), 202
    return jsonify({"message": "Stopped"})


@app.route("/status", methods=["GET"])
# Return current consumer counters and last write/error details.
def status() -> Any:
    with state_lock:
        return jsonify({
            key: state[key]
            for key in (
                "running", "messages_consumed", "messages_scored", "fraud_published",
                "non_fraud_count", "model_failures", "fraud_publish_failures",
                "object_storage_failures", "metrics_publish_failures", "last_score",
                "last_error", "last_object_storage_write", "last_metrics_publish_time",
            )
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
