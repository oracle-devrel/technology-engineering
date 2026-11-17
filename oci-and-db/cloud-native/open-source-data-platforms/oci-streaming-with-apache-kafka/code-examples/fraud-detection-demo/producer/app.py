import io
import json
import math
import threading
import time
import oci
import pandas as pd
import yaml
from flask import Flask, jsonify, request
from confluent_kafka import Producer

app = Flask(__name__)
state_lock = threading.Lock()

state = {
    "running": False,
    "stop_requested": False,
    "records_sent": 0,
    "last_error": None,
    "thread": None
}


# Update shared runtime state while holding the lock.
def update_state(**kwargs):
    with state_lock:
        state.update(kwargs)


# Read one value from shared runtime state.
def get_state(key, default=None):
    with state_lock:
        return state.get(key, default)


# Increment the producer's sent-record counter.
def increment_records_sent():
    with state_lock:
        state["records_sent"] += 1
        return state["records_sent"]


# Load the producer YAML config from the current service directory.
def load_config():
    with open("app_config.yaml", "r") as f:
        return yaml.safe_load(f)


# Read rows from Object Storage and publish them to Kafka.
def simulator_loop(delay_seconds, loop_forever):
    try:
        cfg = load_config()

        oci_cfg = cfg["oci"]
        oci_config = oci.config.from_file(
            file_location=oci_cfg["config_file"],
            profile_name=oci_cfg["profile"]
        )
        object_storage_client = oci.object_storage.ObjectStorageClient(oci_config)
        namespace = object_storage_client.get_namespace().data
        response = object_storage_client.get_object(
            namespace_name=namespace,
            bucket_name=oci_cfg["bucket_name"],
            object_name=oci_cfg["object_name"]
        )
        df = pd.read_csv(io.BytesIO(response.data.content))
        df = df.where(pd.notnull(df), None)

        kafka_props = {}
        with open("kafka_client.properties", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                kafka_props[key.strip()] = value.strip()

        producer = Producer({
            "bootstrap.servers": kafka_props["bootstrap.servers"],
            "security.protocol": kafka_props["security.protocol"],
            "sasl.mechanism": kafka_props["sasl.mechanism"],
            "sasl.username": kafka_props["sasl.username"],
            "sasl.password": kafka_props["sasl.password"],
            "acks": "all",
            "retries": 10,
        })
        topic = cfg["kafka"]["topic"]

        flush_every = cfg["simulator"].get("flush_every", 500)
        key_field = cfg["kafka"].get("key_field", "cc_num")

        def delivery_report(err, msg):
            if err is not None:
                update_state(last_error=str(err))

        while True:
            # Replay the same CSV rows; /start controls whether this runs once or loops forever.
            for idx, row in df.iterrows():
                if get_state("stop_requested"):
                    producer.flush()
                    update_state(running=False, stop_requested=False)
                    return

                record = row.to_dict()
                record.pop("Unnamed: 0", None)

                for field, value in record.items():
                    if isinstance(value, float) and math.isnan(value):
                        record[field] = None

                record["simulation_id"] = f"run-{int(time.time())}-{idx}"
                record["simulation_ts"] = time.time()
                key = str(record.get(key_field) or record.get("trans_num") or idx)

                producer.produce(
                    topic=topic,
                    key=key,
                    value=json.dumps(record),
                    callback=delivery_report
                )
                producer.poll(0)
                records_sent = increment_records_sent()

                # Flush periodically so delivery errors surface while the simulator is running.
                if records_sent % flush_every == 0:
                    producer.flush()

                time.sleep(delay_seconds)

            producer.flush()

            if not loop_forever:
                break

        update_state(running=False)

    except Exception as e:
        update_state(last_error=str(e), running=False, stop_requested=False)

@app.route("/start", methods=["POST"])
# Start the background producer simulator.
def start():
    if get_state("running"):
        with state_lock:
            snapshot = dict(state)
        return jsonify({"message": "Simulator already running", **snapshot}), 400

    body = request.get_json(silent=True) or {}
    cfg = load_config()
    delay_seconds = float(body.get("delay_seconds", cfg["simulator"]["delay_seconds"]))
    loop_value = body.get("loop", cfg["simulator"]["loop"])
    if isinstance(loop_value, bool):
        loop_forever = loop_value
    elif isinstance(loop_value, str):
        loop_forever = loop_value.strip().lower() in ("true", "1", "yes", "y", "on")
    else:
        loop_forever = bool(loop_value)

    update_state(running=True, stop_requested=False, last_error=None, records_sent=0)

    t = threading.Thread(target=simulator_loop, args=(delay_seconds, loop_forever), daemon=True)
    update_state(thread=t)
    t.start()

    return jsonify({
        "message": "Simulator started",
        "delay_seconds": delay_seconds,
        "loop": loop_forever
    })


@app.route("/stop", methods=["POST"])
# Ask the simulator loop to stop after its current record.
def stop():
    if not get_state("running"):
        return jsonify({"message": "Simulator is not running"}), 400

    update_state(stop_requested=True)
    return jsonify({"message": "Stop requested"})


@app.route("/status", methods=["GET"])
# Return current producer progress and last error.
def status():
    with state_lock:
        return jsonify({
            "running": state["running"],
            "stop_requested": state["stop_requested"],
            "records_sent": state["records_sent"],
            "last_error": state["last_error"]
        })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
