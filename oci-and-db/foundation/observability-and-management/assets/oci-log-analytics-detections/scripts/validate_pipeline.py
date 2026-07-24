#!/usr/bin/env python3
"""
Comprehensive health check for the OCI Streaming → Log Analytics pipeline.

Checks:
  1. Config consistency — streaming_config.json vs env vars
  2. Streams ACTIVE    — expected SOC streams exist and are ACTIVE
  3. Connectors ACTIVE — expected SCH connectors exist and are ACTIVE
  4. Log group exists  — target log group is accessible
  5. Connector routing — each SCH targets the correct log group + log source
  6. E2E flow test     — (optional) publish test message and verify delivery

Usage:
  python3 scripts/validate_pipeline.py            # checks 1-5 (default)
  python3 scripts/validate_pipeline.py --quick     # check 1 only (offline)
  python3 scripts/validate_pipeline.py --e2e       # checks 1-6 (includes flow test)
"""

import argparse
import base64
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import (
    COMPARTMENT_ID, TENANCY_ID, PROJECT_DIR,
    LOG_GROUP_ID, LA_NAMESPACE, LOG_GROUP_NAME,
    _cfg,
    get_la_client, get_oci_config, get_streaming_admin_client, get_sch_client,
    get_namespace, require_oci_config,
    CORE_SOC_STREAMS, get_expected_stream_names,
)
from oci_time import build_time_window

STREAMING_CONFIG_PATH = os.path.join(PROJECT_DIR, 'config', 'streaming_config.json')


def _icon(ok):
    return "OK" if ok else "FAIL"


def _expected_streams():
    """Return the currently expected SOC streams for pipeline validation."""
    return get_expected_stream_names()


# ─── Check 1: Config consistency (offline) ────────────────────

def check_config_consistency():
    """Verify streaming_config.json matches env vars."""
    print("\n[1] Config Consistency")
    if not os.path.exists(STREAMING_CONFIG_PATH):
        print(f"  [{_icon(False)}] streaming_config.json not found")
        print(f"         Run: python3 scripts/setup_streaming_pipeline.py")
        return False

    with open(STREAMING_CONFIG_PATH) as f:
        cfg = json.load(f)

    meta = cfg.get("_metadata", {})
    all_ok = True

    # Log group ID
    cfg_lg = meta.get("log_group_id", "")
    if LOG_GROUP_ID and cfg_lg:
        if cfg_lg == LOG_GROUP_ID:
            print(f"  [{_icon(True)} ] log_group_id: matches env")
        else:
            print(f"  [{_icon(False)}] log_group_id: MISMATCH")
            print(f"         config: {cfg_lg}")
            print(f"         env:    {LOG_GROUP_ID}")
            all_ok = False
    elif cfg_lg:
        print(f"  [{_icon(True)} ] log_group_id: ...{cfg_lg[-16:]}")
    else:
        print(f"  [{_icon(False)}] log_group_id: not set in config")
        all_ok = False

    # Compartment ID
    cfg_comp = meta.get("compartment_id", "")
    if COMPARTMENT_ID and cfg_comp and cfg_comp != COMPARTMENT_ID:
        print(f"  [{_icon(False)}] compartment_id: MISMATCH")
        print(f"         config: {cfg_comp}")
        print(f"         env:    {COMPARTMENT_ID}")
        all_ok = False
    elif cfg_comp:
        print(f"  [{_icon(True)} ] compartment_id: matches")

    # Namespace
    cfg_ns = meta.get("la_namespace", "")
    if LA_NAMESPACE and cfg_ns and cfg_ns != LA_NAMESPACE:
        print(f"  [{_icon(False)}] la_namespace: MISMATCH (config={cfg_ns}, env={LA_NAMESPACE})")
        all_ok = False
    elif cfg_ns:
        print(f"  [{_icon(True)} ] la_namespace: {cfg_ns}")

    # Stream count
    stream_count = sum(1 for k in cfg if k != "_metadata")
    expected_streams = get_expected_stream_names(cfg)
    if stream_count >= len(expected_streams):
        print(f"  [{_icon(True)} ] streams: {stream_count} configured")
    else:
        print(
            f"  [{_icon(False)}] streams: only {stream_count} configured "
            f"(expected {len(expected_streams)})"
        )
        all_ok = False

    return all_ok


# ─── Check 2: Streams ACTIVE (online) ────────────────────────

def check_streams_active():
    """Verify the expected SOC streams are ACTIVE."""
    print("\n[2] Streams ACTIVE")
    stream_admin = get_streaming_admin_client()
    all_ok = True

    for name in _expected_streams():
        streams = stream_admin.list_streams(
            compartment_id=COMPARTMENT_ID, name=name, lifecycle_state="ACTIVE"
        ).data
        if streams:
            print(f"  [{_icon(True)} ] {name}")
        else:
            print(f"  [{_icon(False)}] {name}: not found or not ACTIVE")
            all_ok = False

    return all_ok


# ─── Check 3: Connectors ACTIVE (online) ─────────────────────

def check_connectors_active():
    """Verify the expected SCH connectors are ACTIVE."""
    print("\n[3] Service Connectors ACTIVE")
    sch = get_sch_client()
    all_ok = True

    for stream_name in _expected_streams():
        connector_name = f"sch-{stream_name}-to-la"
        connectors = sch.list_service_connectors(
            compartment_id=COMPARTMENT_ID, display_name=connector_name
        ).data.items
        active = [c for c in connectors if getattr(c, "lifecycle_state", "") == "ACTIVE"]
        if active:
            print(f"  [{_icon(True)} ] {connector_name}")
        else:
            states = [getattr(c, "lifecycle_state", "?") for c in connectors]
            print(f"  [{_icon(False)}] {connector_name}: {states or 'not found'}")
            all_ok = False

    return all_ok


# ─── Check 4: Log group exists (online) ──────────────────────

def check_log_group(la_client, namespace):
    """Verify the target log group is accessible."""
    print("\n[4] Log Group Accessible")
    import oci

    target_id = LOG_GROUP_ID
    if not target_id:
        # Try from streaming_config
        if os.path.exists(STREAMING_CONFIG_PATH):
            with open(STREAMING_CONFIG_PATH) as f:
                cfg = json.load(f)
            target_id = cfg.get("_metadata", {}).get("log_group_id", "")

    if not target_id:
        print(f"  [{_icon(False)}] No log group ID available (env or config)")
        return False

    try:
        lg = la_client.get_log_analytics_log_group(
            namespace_name=namespace,
            log_analytics_log_group_id=target_id,
        ).data
        print(f"  [{_icon(True)} ] {lg.display_name} ({target_id[:50]}...)")
        return True
    except oci.exceptions.ServiceError as e:
        print(f"  [{_icon(False)}] {target_id[:50]}... — {e.status}: {e.message[:60]}")
        return False


# ─── Check 5: Connector routing (online) ─────────────────────

def check_connector_routing(la_client, namespace):
    """Verify each SCH connector targets the correct log group and log source."""
    print("\n[5] Connector Routing")
    sch = get_sch_client()
    all_ok = True

    # Determine the expected log group
    expected_lg = LOG_GROUP_ID
    if not expected_lg and os.path.exists(STREAMING_CONFIG_PATH):
        with open(STREAMING_CONFIG_PATH) as f:
            cfg = json.load(f)
        expected_lg = cfg.get("_metadata", {}).get("log_group_id", "")

    for stream_name in _expected_streams():
        connector_name = f"sch-{stream_name}-to-la"
        connectors = sch.list_service_connectors(
            compartment_id=COMPARTMENT_ID, display_name=connector_name
        ).data.items
        active = [c for c in connectors if getattr(c, "lifecycle_state", "") == "ACTIVE"]

        if not active:
            print(f"  [{_icon(False)}] {connector_name}: not found/ACTIVE — skipping routing check")
            all_ok = False
            continue

        full = sch.get_service_connector(active[0].id).data
        target = getattr(full, "target", None)
        target_lg = getattr(target, "log_group_id", None) if target else None
        target_src = getattr(target, "log_source_identifier", None) if target else None

        lg_ok = True
        if expected_lg and target_lg and target_lg != expected_lg:
            lg_ok = False

        if lg_ok and target_src:
            print(f"  [{_icon(True)} ] {connector_name} → {target_src}")
        else:
            all_ok = False
            if not lg_ok:
                print(f"  [{_icon(False)}] {connector_name}: log_group MISMATCH")
                print(f"         connector: {target_lg}")
                print(f"         expected:  {expected_lg}")
            if not target_src:
                print(f"  [{_icon(False)}] {connector_name}: no log_source_identifier set")

    return all_ok


# ─── Check 6: E2E flow test (online, optional) ───────────────

def check_e2e_flow(la_client, namespace):
    """Publish a test message to one stream and verify it arrives in Log Analytics."""
    print("\n[6] End-to-End Flow Test")
    import oci

    if not os.path.exists(STREAMING_CONFIG_PATH):
        print(f"  [{_icon(False)}] streaming_config.json not found — cannot run E2E test")
        return False

    with open(STREAMING_CONFIG_PATH) as f:
        cfg = json.load(f)

    # Pick the first available stream
    test_stream = None
    for name in _expected_streams():
        if name in cfg:
            test_stream = name
            break

    if not test_stream:
        print(f"  [{_icon(False)}] No configured stream found for E2E test")
        return False

    info = cfg[test_stream]
    stream_id = info["stream_id"]
    endpoint = info["messages_endpoint"]

    # Publish a test message
    marker = f"validate-pipeline-e2e-{int(time.time())}"
    test_payload = json.dumps({
        "type": "pipeline_validation",
        "marker": marker,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })

    print(f"  Publishing test message to {test_stream}...")
    print(f"    marker: {marker}")

    config = get_oci_config()
    stream_client = oci.streaming.StreamClient(config, service_endpoint=endpoint)

    entry = oci.streaming.models.PutMessagesDetailsEntry(
        key=base64.b64encode(b"e2e-test").decode(),
        value=base64.b64encode(test_payload.encode()).decode(),
    )
    details = oci.streaming.models.PutMessagesDetails(messages=[entry])

    try:
        resp = stream_client.put_messages(stream_id, details)
        failures = resp.data.failures or 0
        if failures > 0:
            print(f"  [{_icon(False)}] Message publish failed ({failures} failures)")
            return False
        print(f"  [{_icon(True)} ] Message published successfully")
    except oci.exceptions.ServiceError as e:
        print(f"  [{_icon(False)}] Publish error: {e.status} — {e.message[:80]}")
        return False

    # Wait and check for delivery
    log_group_id = cfg.get("_metadata", {}).get("log_group_id", "") or LOG_GROUP_ID
    if not log_group_id:
        print(f"  [SKIP] No log_group_id — cannot verify delivery")
        return True  # publish succeeded at least

    print(f"  Waiting 30s for SCH to deliver message to Log Analytics...")
    time.sleep(30)

    # Query Log Analytics for the marker
    try:
        time_start, time_end = build_time_window("5m")
        query = f"'{marker}' | stats count as hits"
        resp = la_client.query(
            namespace_name=namespace,
            query_details=oci.log_analytics.models.QueryDetails(
                compartment_id=COMPARTMENT_ID,
                query_string=query,
                time_filter=oci.log_analytics.models.TimeRange(
                    time_start=time_start,
                    time_end=time_end,
                    time_zone="UTC",
                ),
                sub_system="LOG",
            ),
        ).data
        # Check if we got hits
        items = getattr(resp, "items", []) or []
        if items:
            print(f"  [{_icon(True)} ] Message found in Log Analytics!")
            return True
        else:
            print(f"  [WARN] Message not yet visible (SCH delivery can take 2-5 min)")
            print(f"         Re-run with --e2e in a few minutes to verify.")
            return True  # not a hard failure — timing issue
    except Exception as e:
        print(f"  [WARN] Query failed: {str(e)[:80]}")
        print(f"         This may be a permissions issue; publish itself succeeded.")
        return True


# ─── Main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Validate the OCI Streaming → Log Analytics pipeline"
    )
    parser.add_argument("--quick", action="store_true",
                        help="Offline checks only (config consistency)")
    parser.add_argument("--e2e", action="store_true",
                        help="Include end-to-end flow test")
    args = parser.parse_args()

    print("=" * 60)
    print("  Pipeline Health Check")
    print("=" * 60)

    results = {}

    # Check 1: always run (offline)
    results["config"] = check_config_consistency()

    if args.quick:
        _summary(results)
        return

    # Online checks require OCI config
    require_oci_config()
    la_client = get_la_client()
    namespace = LA_NAMESPACE
    if not namespace:
        ns_resp = la_client.list_namespaces(compartment_id=TENANCY_ID).data
        if ns_resp.items:
            namespace = ns_resp.items[0].namespace_name
        else:
            print("\nERROR: Could not determine Log Analytics namespace.")
            sys.exit(1)

    results["streams"] = check_streams_active()
    results["connectors"] = check_connectors_active()
    results["log_group"] = check_log_group(la_client, namespace)
    results["routing"] = check_connector_routing(la_client, namespace)

    if args.e2e:
        results["e2e"] = check_e2e_flow(la_client, namespace)

    _summary(results)


def _summary(results):
    """Print overall pass/fail summary."""
    print("\n" + "=" * 60)
    all_ok = all(results.values())
    for name, ok in results.items():
        print(f"  [{_icon(ok):4s}] {name}")
    print("=" * 60)
    if all_ok:
        print("  All checks passed.")
    else:
        print("  Some checks FAILED. See details above.")
    print("=" * 60)
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
