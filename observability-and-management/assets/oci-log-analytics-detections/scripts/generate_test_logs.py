"""
Generate realistic test log files for all 201 detection rules + 15 hunting queries.

Produces NDJSON (JSON Lines) files in test_data/ for each log source category:
  - oci_audit.jsonl          OCI Audit events (80 rules + hunting)
  - cloud_guard.jsonl        OCI Cloud Guard events (12 rules)
  - linux_syslog.jsonl       Linux syslog/auth events (65 rules + hunting)
  - windows_sysmon.jsonl     Windows Sysmon events (55 rules + hunting)
  - manifest.json            Maps rules to generated events

Each log entry is crafted to trigger detection rules when queried.
Hunting-specific events generate higher volumes with consistent source
attributes (same IP, same host) to support aggregation-based queries.

This module is a thin CLI orchestrator. The per-log-source synthetic-event
builders live in the ``testlogs`` package (behavior-preserving split); this file
imports them and keeps the ``main()`` dispatch + file-writing loop.

Usage:
  python3 scripts/generate_test_logs.py
  python3 scripts/generate_test_logs.py --validate
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_data_manifest import rebuild_manifest

# Shared constants + helpers (BASE_TIME, OUTPUT_DIR, QUERIES_DIR, COMPARTMENT_ID,
# ts, expand_events_over_days, write_jsonl, shift_event_window, ...).
from testlogs.common import *  # noqa: F401,F403
# Per-log-source builders. Re-exported here so existing imports
# (``from generate_test_logs import generate_xxx_events``) keep working.
from testlogs.oci_audit import *  # noqa: F401,F403
from testlogs.cloud_guard import *  # noqa: F401,F403
from testlogs.linux import *  # noqa: F401,F403
from testlogs.linux_secure import *  # noqa: F401,F403
from testlogs.windows_sysmon import *  # noqa: F401,F403
from testlogs.windows_event_logs import *  # noqa: F401,F403
from testlogs.sysmon_operational import *  # noqa: F401,F403
from testlogs.network import *  # noqa: F401,F403
from testlogs.sysmon_network import *  # noqa: F401,F403
from testlogs.web import *  # noqa: F401,F403
from testlogs.application import *  # noqa: F401,F403
from testlogs.genai_gateway import *  # noqa: F401,F403


def main():
    parser = argparse.ArgumentParser(description="Generate test detection logs")
    parser.add_argument("--days", type=int, default=1,
                        help="Replicate the generated detection datasets across N daily windows")
    parser.add_argument("--validate", action="store_true",
                        help="Validate that all query files have matching test events")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Generating Attack Simulation Test Logs (NDJSON)")
    print("=" * 60)

    # Generate events — original SOC detection rule sources
    oci_events = generate_oci_audit_events()
    cg_events = generate_cloud_guard_events()
    cgis_events = generate_cloud_guard_instance_security_events()
    linux_events = generate_linux_events()
    windows_events = generate_windows_events()

    # Generate events — multicloudoperations widget-compatible sources
    winsec_events = generate_windows_event_security()
    winsys_events = generate_windows_event_system()
    winps_events = generate_windows_powershell_operational()
    windef_events = generate_windows_defender_operational()
    linsec_events = generate_linux_secure()
    sysmon_events = generate_sysmon_operational()

    # Generate events — Sysmon network connection (dedicated parser)
    sysmon_net_events = generate_sysmon_network_events()

    # Generate events — Web application security (OWASP attacks)
    waf_events = generate_waf_events()
    lb_events = generate_lb_access_events()
    webapp_events = generate_webapp_events()
    application_events = generate_application_events()
    genai_gateway_events = generate_genai_gateway_events()
    vcn_flow_events = generate_vcn_flow_events()
    network_firewall_events = generate_network_firewall_events()

    generated_sets = {
        "oci_audit.jsonl": oci_events,
        "cloud_guard.jsonl": cg_events,
        "cloud_guard_instance_security.jsonl": cgis_events,
        "linux_syslog.jsonl": linux_events,
        "windows_sysmon.jsonl": windows_events,
        "windows_event_security.jsonl": winsec_events,
        "windows_event_system.jsonl": winsys_events,
        "windows_powershell_operational.jsonl": winps_events,
        "windows_defender_operational.jsonl": windef_events,
        "linux_secure.jsonl": linsec_events,
        "sysmon_operational.jsonl": sysmon_events,
        "sysmon_network.jsonl": sysmon_net_events,
        "waf_security.jsonl": waf_events,
        "lb_access.jsonl": lb_events,
        "webapp_security.jsonl": webapp_events,
        "application_logs.jsonl": application_events,
        "genai_gateway.jsonl": genai_gateway_events,
        "vcn_flow.jsonl": vcn_flow_events,
        "network_firewall.jsonl": network_firewall_events,
    }

    # Write NDJSON files
    results = {}
    for filename, events in generated_sets.items():
        expanded_events = expand_events_over_days(events, args.days)
        filepath = OUTPUT_DIR / filename
        count = write_jsonl(filepath, expanded_events)
        results[filename] = count
        print(f"  {count:>5} events -> {filepath}")

    manifest = rebuild_manifest(OUTPUT_DIR)
    manifest_path = OUTPUT_DIR / "manifest.json"

    print(f"\n  Total: {manifest['total_events']} events across {len(manifest['files'])} files")
    print(f"  Manifest: {manifest_path}")
    print(f"  Detection window: {args.days} day(s)")

    if args.validate:
        print("\n  Validating query coverage...")
        from query_artifacts import is_saved_search_query_file

        query_files = [
            path for path in QUERIES_DIR.rglob("*.json")
            if is_saved_search_query_file(path)
        ]
        print(f"  Found {len(query_files)} query files")
        print("  (Full validation requires OCI LA to parse and match fields)")

    print(f"\nNext: python3 scripts/ingest_test_data.py")


if __name__ == "__main__":
    main()
