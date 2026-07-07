#!/usr/bin/env python3
"""Contract tests for the OKE/Kubernetes attack-chain, eBPF rootkit, and
APM SQL-injection detection families.

These families were added alongside the Windows OOTB and Cloud Guard Instance
Security expansions but lacked a dedicated regression fence. The tests assert
that every new detection query:

1. exists and is a detection surface (carries a query, MITRE mapping, and a log
   source candidate list),
2. is field-backed by the generated field dictionary,
3. is registered in the catalog, and
4. is matchable against the synthetic event streams produced by
   ``generate_test_logs`` so the queries can actually fire on test data.
"""

from __future__ import annotations

import json
import os
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import field_dictionary
from generate_test_logs import generate_application_events, generate_linux_events


ROOT = Path(__file__).resolve().parents[1]
QUERIES_DIR = ROOT / "queries"
APPS_DIR = QUERIES_DIR / "apps"
CATALOG_PATH = QUERIES_DIR / "catalog.json"


# App-surface OKE queries (must stay on SOC Application Logs per CLAUDE.md #5).
OKE_APP_QUERIES = {
    "oke_kubernetes_attack_overview.json",
    "oke_kubernetes_attack_path_link.json",
    "oke_boopkit_attack_timeline.json",
    "oke_ebpf_rootkit_activity.json",
    "oke_exec_and_node_escape.json",
    "oke_privileged_workload_creation.json",
    "oke_secrets_and_rbac_abuse.json",
    "oke_rule_boopkit_ebpf_rootkit_count.json",
    "oke_rule_privileged_workload_count.json",
}

# Endpoint-surface detection queries that ship with the same expansion.
ENDPOINT_QUERIES = {
    "linux_boopkit_ebpf_rootkit_activity.json",
    "apm_sql_injection_attack_in_request.json",
}

# Full Stream B detection surface (Windows OOTB + Cloud Guard Instance Security +
# OKE attack chain + endpoint). Used to fence the catalog against drift so every
# newly added detection family stays registered.
WINDOWS_OOTB_QUERIES = {
    "windows_audit_policy_changed.json",
    "windows_security_log_cleared_event.json",
    "windows_scheduled_task_created_or_updated_event.json",
    "windows_service_installed_event_log.json",
    "windows_kerberos_pre_authentication_failures.json",
    "windows_ntlm_authentication_failures.json",
    "windows_admin_share_access_spike_event.json",
    "windows_privileged_group_membership_change_event.json",
    "windows_account_or_group_enumeration_spike.json",
    "windows_powershell_script_block_suspicious_content.json",
    "windows_defender_malware_or_remediation_event.json",
    "sysmon_executable_file_created_or_detected.json",
    "clickfix_fake_captcha_powershell_execution.json",
}

CLOUD_GUARD_QUERIES = {
    "cloud_guard_instance_security_findings_by_host.json",
    "cloud_guard_instance_security_findings_by_pack_query.json",
    "cloud_guard_instance_security_high_severity_pivots.json",
    "cloud_guard_instance_security_instance_to_query_link.json",
    "cloud_guard_instance_security_pack_coverage.json",
    "cloud_guard_instance_security_raw_result_detail.json",
}


class TestOkeAttackChainDetections(unittest.TestCase):
    def test_oke_queries_exist_and_stay_on_application_logs(self):
        missing = [name for name in sorted(OKE_APP_QUERIES) if not (APPS_DIR / name).exists()]
        self.assertEqual(missing, [])

        for name in sorted(OKE_APP_QUERIES):
            payload = json.loads((APPS_DIR / name).read_text())
            self.assertIn("query", payload)
            self.assertNotEqual(payload.get("type"), "hunting")
            self.assertEqual(
                payload.get("logsource", {}).get("candidates"),
                ["SOC Application Logs"],
                f"{name} must stay on SOC Application Logs",
            )

    def test_endpoint_queries_exist_and_are_detection_surface(self):
        missing = [name for name in sorted(ENDPOINT_QUERIES) if not (QUERIES_DIR / name).exists()]
        self.assertEqual(missing, [])

        for name in sorted(ENDPOINT_QUERIES):
            payload = json.loads((QUERIES_DIR / name).read_text())
            self.assertIn("query", payload)
            self.assertNotEqual(payload.get("type"), "hunting")
            self.assertTrue(payload.get("mitre_attack", {}).get("techniques"))
            self.assertTrue(payload.get("logsource", {}).get("candidates"))

    def test_all_query_fields_are_backed_by_generated_dictionary(self):
        dictionary = field_dictionary.build_field_dictionary()
        for relpath in sorted(
            [f"queries/apps/{n}" for n in OKE_APP_QUERIES]
            + [f"queries/{n}" for n in ENDPOINT_QUERIES]
        ):
            payload = json.loads((ROOT / relpath).read_text())
            errors = field_dictionary.validate_query_field_coverage(relpath, payload, dictionary)
            self.assertEqual(errors, [], f"{relpath}: {errors}")

    def test_new_detections_are_registered_in_catalog(self):
        catalog = json.loads(CATALOG_PATH.read_text())
        catalog_files = {
            os.path.basename(entry.get("file", ""))
            for group in ("rules", "app_queries", "hunting_queries")
            for entry in catalog.get(group, [])
        }
        for name in sorted(OKE_APP_QUERIES | ENDPOINT_QUERIES):
            self.assertIn(name, catalog_files, f"{name} not registered in catalog.json")

    def test_full_stream_b_detection_surface_registered_in_catalog(self):
        catalog = json.loads(CATALOG_PATH.read_text())
        catalog_files = {
            os.path.basename(entry.get("file", ""))
            for group in ("rules", "app_queries", "hunting_queries")
            for entry in catalog.get(group, [])
        }
        stream_b = (
            OKE_APP_QUERIES
            | ENDPOINT_QUERIES
            | WINDOWS_OOTB_QUERIES
            | CLOUD_GUARD_QUERIES
        )
        missing = sorted(name for name in stream_b if name not in catalog_files)
        self.assertEqual(missing, [], f"new detections missing from catalog: {missing}")

    def test_synthetic_oke_events_cover_attack_chain_tokens(self):
        random.seed(35)
        events = generate_application_events()
        oke = [e for e in events if str(e.get("traceId", "")).startswith("trace_oke_")]

        self.assertGreaterEqual(len(oke), 4)
        # Overview / attack-path-link queries filter on attack-oke-* IDs.
        self.assertTrue(any(str(e.get("security.attack.id", "")).startswith("attack-oke-") for e in oke))
        self.assertEqual({e.get("security.attack.type") for e in oke}, {"oke_kubernetes_attack"})

        blob = json.dumps(oke).lower()
        # boopkit / eBPF rootkit count rule tokens.
        for token in ("boopkit", "bpftool", "ebpf", "/sys/fs/bpf"):
            self.assertIn(token, blob, f"OKE synthetic data missing token: {token}")
        # privileged-workload count rule tokens.
        for token in ("privileged=true", "hostpid=true", "kubectl exec", "subresource=exec"):
            self.assertIn(token, blob, f"OKE synthetic data missing token: {token}")

    def test_synthetic_linux_events_cover_boopkit_rootkit_tokens(self):
        random.seed(1)
        events = generate_linux_events()
        blob = json.dumps(events).lower()
        # Mirror the linux_boopkit query alternation.
        for token in ("boopkit", "bpftool prog load", "/sys/fs/bpf", "xdp_redirect"):
            self.assertIn(token, blob, f"linux synthetic data missing token: {token}")

    def test_synthetic_app_events_cover_apm_sql_injection_tokens(self):
        random.seed(35)
        events = generate_application_events()
        sqli = [
            event
            for event in events
            if any(
                token in str(event.get("requestUrl", ""))
                for token in ("UNION SELECT", "OR 1=1", "'--", "sleep(5)")
            )
        ]
        self.assertGreaterEqual(len(sqli), 3)


if __name__ == "__main__":
    unittest.main()
