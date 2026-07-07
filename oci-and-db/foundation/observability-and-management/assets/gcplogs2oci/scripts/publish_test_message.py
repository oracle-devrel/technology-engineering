#!/usr/bin/env python3
"""
Publish sample GCP log messages to Pub/Sub for end-to-end testing.

Usage:
    # Publish a single test message
    python scripts/publish_test_message.py

    # Publish N messages
    python scripts/publish_test_message.py --count 10

    # Publish a custom JSON payload
    python scripts/publish_test_message.py --payload '{"msg": "hello"}'
"""

import argparse
import json
import os
import sys
import time

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridge.config import gcp_project_id, gcp_topic, load_env


def sample_gcp_audit_log(index: int = 0) -> dict:
    """Generate a realistic GCP audit log entry for testing."""
    return {
        "insertId": f"test-{int(time.time())}-{index}",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
        "severity": "INFO",
        "logName": f"projects/test-project/logs/cloudaudit.googleapis.com%2Factivity",
        "resource": {
            "type": "gce_instance",
            "labels": {
                "instance_id": "1234567890",
                "project_id": "test-project",
                "zone": "us-central1-a",
            },
        },
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "methodName": "v1.compute.instances.start",
            "serviceName": "compute.googleapis.com",
            "authenticationInfo": {
                "principalEmail": "test-user@example.com",
            },
            "status": {},
        },
        "labels": {
            "instanceId": "1234567890",
        },
        "jsonPayload": {
            "message": f"Test audit log entry #{index} from gcplogs2oci publish_test_message.py",
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Publish test messages to GCP Pub/Sub")
    parser.add_argument("--count", type=int, default=1, help="Number of messages (default: 1)")
    parser.add_argument("--payload", type=str, default=None, help="Custom JSON payload (overrides sample)")
    args = parser.parse_args()

    load_env()

    from google.cloud import pubsub_v1

    project_id = gcp_project_id()
    topic_id = gcp_topic()
    topic_path = f"projects/{project_id}/topics/{topic_id}"

    publisher = pubsub_v1.PublisherClient()

    print(f"Publishing {args.count} message(s) to {topic_path}...")

    futures = []
    for i in range(args.count):
        if args.payload:
            data = args.payload.encode("utf-8")
        else:
            data = json.dumps(sample_gcp_audit_log(i)).encode("utf-8")

        future = publisher.publish(topic_path, data=data)
        futures.append(future)

    # Wait for all publishes to complete
    for i, future in enumerate(futures):
        message_id = future.result()
        print(f"  [{i+1}/{args.count}] Published message_id={message_id}")

    print(f"\nDone. Published {args.count} message(s) to {topic_path}")


if __name__ == "__main__":
    main()
