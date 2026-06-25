#!/usr/bin/env python3
"""
Validate OCI credentials and Stream access without running the full bridge.

Usage:
    python scripts/test_oci_credentials.py
"""

import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bridge.config import load_env, mask, oci_config, oci_message_endpoint, oci_stream_ocid


def test_oci_credentials():
    print("=" * 72)
    print("  OCI Credentials Test")
    print("=" * 72)
    print()

    env_file = load_env()
    if env_file:
        print(f"  Loaded environment from: {env_file}")
    else:
        print("  No .env.local / .env found; using system environment")

    # ── Check required variables ──────────────────────────────
    required = [
        "OCI_USER_OCID", "OCI_FINGERPRINT",
        "OCI_TENANCY_OCID", "OCI_REGION",
        "OCI_MESSAGE_ENDPOINT", "OCI_STREAM_OCID",
    ]
    print("\n  Environment Variables:")
    all_ok = True
    for var in required:
        val = os.getenv(var)
        if val:
            print(f"    OK  {var}: {mask(val)}")
        else:
            print(f"    MISSING  {var}")
            all_ok = False

    # Key: either file path or inline content
    key_file = os.getenv("OCI_KEY_FILE")
    key_content = os.getenv("OCI_KEY_CONTENT")
    if key_file:
        exists = os.path.isfile(os.path.expanduser(key_file))
        print(f"    {'OK' if exists else 'MISSING FILE'}  OCI_KEY_FILE: {key_file}")
        if not exists:
            all_ok = False
    elif key_content:
        print(f"    OK  OCI_KEY_CONTENT: {mask(key_content)}")
    else:
        print(f"    MISSING  OCI_KEY_FILE or OCI_KEY_CONTENT")
        all_ok = False

    if not all_ok:
        print("\n  FAILED: Missing required OCI environment variables.")
        return False

    # ── Build and validate OCI config ─────────────────────────
    try:
        import oci

        print("\n  Building OCI configuration...")
        cfg = oci_config()
        oci.config.validate_config(cfg)
        print("    OK  OCI configuration valid")

        endpoint = oci_message_endpoint()
        stream_ocid = oci_stream_ocid()
        print(f"    OK  Endpoint: {mask(endpoint)}")
        print(f"    OK  Stream OCID: {mask(stream_ocid)}")

        # ── Test authentication ───────────────────────────────
        print("\n  Testing OCI authentication (StreamAdminClient.get_stream)...")
        admin_client = oci.streaming.StreamAdminClient(cfg)
        response = admin_client.get_stream(stream_ocid)
        print(f"    OK  Authentication successful")
        print(f"    OK  Stream name: {response.data.name}")
        print(f"    OK  Stream state: {response.data.lifecycle_state}")

    except oci.exceptions.ServiceError as e:
        if e.status == 404:
            print(f"    WARN  Stream not found (auth OK, OCID may be wrong): {e.message}")
        elif e.status == 401:
            print(f"    FAILED  Authentication failed: {e.message}")
            return False
        elif e.status == 403:
            print(f"    FAILED  Authorization failed: {e.message}")
            return False
        else:
            print(f"    FAILED  OCI API error (HTTP {e.status}): {e.message}")
            return False
    except Exception as e:
        print(f"    FAILED  {e}")
        return False

    print("\n" + "=" * 72)
    print("  OCI CREDENTIALS TEST PASSED")
    print("=" * 72)
    return True


if __name__ == "__main__":
    success = test_oci_credentials()
    sys.exit(0 if success else 1)
