#!/usr/bin/env python3
"""
Entry point for the GCP Pub/Sub → OCI Streaming bridge.

Usage:
    # Continuous mode (default) – runs until interrupted
    python -m bridge.main

    # Drain mode – stops after INACTIVITY_TIMEOUT seconds of silence
    python -m bridge.main --drain
"""

import argparse
import logging
import sys

from bridge.config import load_env, mask, oci_message_endpoint, oci_stream_ocid
from bridge.gcp_subscriber import PubSubBridge


def main():
    parser = argparse.ArgumentParser(
        description="GCP Pub/Sub → OCI Streaming bridge"
    )
    parser.add_argument(
        "--drain",
        action="store_true",
        help="Run in drain mode: stop after inactivity timeout",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    env_file = load_env()
    if env_file:
        logging.info("Loaded environment from %s", env_file)
    else:
        logging.info("No .env.local / .env found; using system environment")

    # Quick sanity check before starting
    logging.info(
        "Target: endpoint=%s stream=%s",
        mask(oci_message_endpoint()),
        mask(oci_stream_ocid()),
    )

    bridge = PubSubBridge()
    bridge.run(run_forever=not args.drain)


if __name__ == "__main__":
    main()
