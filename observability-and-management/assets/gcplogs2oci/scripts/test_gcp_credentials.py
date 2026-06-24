#!/usr/bin/env python3
"""
Validate GCP credentials and Pub/Sub access without running the full bridge.

Usage:
    python scripts/test_gcp_credentials.py
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridge.config import load_env, mask


def test_gcp_credentials():
    print("=" * 72)
    print("  GCP Credentials Test")
    print("=" * 72)
    print()

    env_file = load_env()
    if env_file:
        print(f"  Loaded environment from: {env_file}")
    else:
        print("  No .env.local / .env found; using system environment")

    # ── Check required variables ──────────────────────────────
    required = ["GCP_PROJECT_ID", "GCP_PUBSUB_SUBSCRIPTION"]
    print("\n  Environment Variables:")
    all_ok = True
    for var in required:
        val = os.getenv(var)
        if val:
            print(f"    OK  {var}: {mask(val)}")
        else:
            print(f"    MISSING  {var}")
            all_ok = False

    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path:
        exists = os.path.isfile(creds_path)
        print(f"    {'OK' if exists else 'MISSING FILE'}  GOOGLE_APPLICATION_CREDENTIALS: {creds_path}")
        if not exists:
            all_ok = False
    else:
        print("    INFO  GOOGLE_APPLICATION_CREDENTIALS not set (will use ADC)")

    if not all_ok:
        print("\n  FAILED: Missing required GCP environment variables.")
        return False

    # ── Test Pub/Sub client ───────────────────────────────────
    try:
        from google.cloud import pubsub_v1

        project_id = os.environ["GCP_PROJECT_ID"]
        subscription_id = os.environ["GCP_PUBSUB_SUBSCRIPTION"]
        sub_path = f"projects/{project_id}/subscriptions/{subscription_id}"

        print(f"\n  Testing Pub/Sub subscriber client...")
        subscriber = pubsub_v1.SubscriberClient()
        sub = subscriber.get_subscription(request={"subscription": sub_path})
        print(f"    OK  Subscription found: {sub.name}")
        print(f"    OK  Topic: {sub.topic}")
        print(f"    OK  Ack deadline: {sub.ack_deadline_seconds}s")
        subscriber.close()

    except Exception as e:
        print(f"    FAILED  {e}")
        return False

    # ── Optionally test the topic ─────────────────────────────
    topic = os.getenv("GCP_PUBSUB_TOPIC")
    if topic:
        try:
            publisher = pubsub_v1.PublisherClient()
            topic_path = f"projects/{project_id}/topics/{topic}"
            t = publisher.get_topic(request={"topic": topic_path})
            print(f"    OK  Topic exists: {t.name}")
        except Exception as e:
            print(f"    WARN  Could not verify topic: {e}")

    print("\n" + "=" * 72)
    print("  GCP CREDENTIALS TEST PASSED")
    print("=" * 72)
    return True


if __name__ == "__main__":
    success = test_gcp_credentials()
    sys.exit(0 if success else 1)
