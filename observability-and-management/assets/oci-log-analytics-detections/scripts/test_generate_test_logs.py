#!/usr/bin/env python3
"""Regression tests for expanding synthetic attack datasets across days."""

import os
import random
import sys
import unittest
from collections import defaultdict
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_test_logs import (
    BASE_TIME,
    expand_events_over_days,
    generate_application_events,
    generate_lb_access_events,
    generate_linux_secure,
    generate_network_firewall_events,
    generate_oci_audit_events,
    generate_sysmon_network_events,
    generate_sysmon_operational,
    generate_vcn_flow_events,
    generate_waf_events,
    generate_webapp_events,
    generate_windows_event_security,
    generate_windows_events,
    shift_event_window,
)


class TestGenerateTestLogs(unittest.TestCase):
    """Ensure the demo datasets can be extended to a full-week window."""

    def test_shift_event_window_recursively_updates_timestamps(self):
        payload = {
            "timestamp": "2026-04-20T10:15:30.000Z",
            "nested": {
                "eventTime": "2026-04-20T10:16:30.000Z",
                "note": "not-a-timestamp",
            },
            "items": [
                {"Timestamp": "2026-04-20T10:17:30.000Z"},
                "still-not-a-timestamp",
            ],
        }

        shifted = shift_event_window(payload, timedelta(days=2))

        self.assertEqual(shifted["timestamp"], "2026-04-22T10:15:30.000Z")
        self.assertEqual(shifted["nested"]["eventTime"], "2026-04-22T10:16:30.000Z")
        self.assertEqual(shifted["items"][0]["Timestamp"], "2026-04-22T10:17:30.000Z")
        self.assertEqual(shifted["nested"]["note"], "not-a-timestamp")

    def test_expand_events_over_days_repeats_scenarios_per_day(self):
        events = [
            {"timestamp": "2026-04-20T10:15:30.000Z", "value": 1},
            {"timestamp": "2026-04-20T11:15:30.000Z", "value": 2},
        ]

        expanded = expand_events_over_days(events, 3)

        self.assertEqual(len(expanded), 6)
        self.assertEqual(expanded[0]["timestamp"], "2026-04-18T10:15:30.000Z")
        self.assertEqual(expanded[2]["timestamp"], "2026-04-19T10:15:30.000Z")
        self.assertEqual(expanded[4]["timestamp"], "2026-04-20T10:15:30.000Z")

    def test_windows_security_process_creation_events_include_detection_commandlines(self):
        random.seed(7)
        events = generate_windows_event_security()

        process_events = [
            event for event in events
            if str(event.get("Event ID") or event.get("EventID")) == "4688"
        ]
        command_lines = " ".join(
            (event.get("Command Line") or event.get("CommandLine") or "")
            for event in process_events
        )

        self.assertTrue(process_events)
        self.assertIn("whoami /all", command_lines)
        self.assertIn("Invoke-WebRequest", command_lines)
        self.assertIn("sekurlsa::logonpasswords", command_lines)

    def test_oci_audit_events_include_dashboard_status_labels_and_policy_keywords(self):
        random.seed(17)
        events = generate_oci_audit_events()

        console_successes = [
            event for event in events
            if event.get("eventType") == "com.oraclecloud.consolesignon.login"
            and event.get("Status") == "Success"
            and event.get("data", {}).get("response", {}).get("status") == "200"
        ]
        admin_policy_events = [
            event for event in events
            if event.get("eventType") == "com.oraclecloud.identitycontrolplane.createpolicy"
            and "manage all-resources" in event.get("data", {}).get("resourceName", "")
        ]

        self.assertGreaterEqual(len(console_successes), 8)
        self.assertGreaterEqual(len(admin_policy_events), 3)

    def test_linux_secure_events_mirror_messages_to_command_line_fields(self):
        random.seed(19)
        events = generate_linux_secure()

        crontab_events = [
            event for event in events
            if event.get("Process") == "crontab"
            and any(pattern in event.get("Command Line", "") for pattern in ("crontab -e", "/tmp/", "/dev/shm/"))
        ]

        self.assertTrue(crontab_events)
        for event in crontab_events:
            self.assertEqual(event["msg"], event["CommandLine"])
            self.assertEqual(event["msg"], event["Command Line"])

    def test_windows_events_include_rare_process_hunting_tail(self):
        random.seed(23)
        events = generate_windows_events()

        command_lines = {
            event.get("Command Line") or event.get("CommandLine")
            for event in events
            if str(event.get("Event ID") or event.get("EventID")) == "1"
        }

        self.assertIn("rare_recon.exe -enum users", command_lines)
        self.assertIn("anomaly_dropper.exe stage", command_lines)

    def test_sysmon_operational_includes_named_pipe_iocs(self):
        random.seed(29)
        events = generate_sysmon_operational()

        pipe_names = {
            event.get("Pipe Name") or event.get("PipeName")
            for event in events
            if str(event.get("Event ID") or event.get("EventID")) == "17"
        }

        self.assertIn(r"\\.\pipe\PSEXESVC", pipe_names)
        self.assertIn(r"\\.\pipe\MSSE-1234-server", pipe_names)
        self.assertIn(r"\\.\pipe\mimikatz_lsass", pipe_names)

    def test_sysmon_operational_includes_dns_exfiltration_query_names(self):
        random.seed(41)
        events = generate_sysmon_operational()

        long_query_events = [
            event for event in events
            if str(event.get("Event ID") or event.get("EventID")) == "22"
            and len(event.get("Query Name") or event.get("QueryName") or "") > 30
        ]

        self.assertTrue(long_query_events)
        for event in long_query_events:
            self.assertEqual(event["Query Name"], event["QueryName"])
            self.assertIn("dnsexfil", event["Query Name"])

    def test_sysmon_network_includes_dns_tunnel_processes(self):
        random.seed(31)
        events = generate_sysmon_network_events()

        dns_processes = {
            event.get("Process Name") or event.get("Image")
            for event in events
            if str(event.get("Destination Port") or event.get("DestinationPort")) == "53"
            and str(event.get("Initiated")).lower() == "true"
        }

        self.assertIn(r"C:\Tools\iodine.exe", dns_processes)
        self.assertIn(r"C:\Tools\dnscat2.exe", dns_processes)
        self.assertIn(r"C:\Tools\dns2tcp.exe", dns_processes)

    def test_freelabfriday_network_and_http_patterns_are_present(self):
        random.seed(33)

        sysmon_network = generate_sysmon_network_events()
        lb_events = generate_lb_access_events()
        application_events = generate_application_events()
        vcn_events = generate_vcn_flow_events()
        firewall_events = generate_network_firewall_events()

        self.assertTrue(any(
            event.get("Destination Hostname", "").endswith("cloudfront.net")
            and event.get("Process Name", "").endswith("powershell.exe")
            for event in sysmon_network
        ))

        self.assertTrue(any(
            event.get("userAgent") == "vsagent/1.0"
            and event.get("requestUrl") == "/beacon"
            and event.get("httpMethod") == "GET"
            for event in lb_events + application_events
        ))
        self.assertTrue(any(
            event.get("userAgent") == "vsagent/1.0"
            and event.get("requestUrl") == "/beacon"
            and event.get("httpMethod") == "POST"
            for event in lb_events + application_events
        ))

        vcn_knock_ports = [
            event.get("Destination Port")
            for event in vcn_events
            if event.get("Source IP") == "10.42.0.7"
            and event.get("Destination IP") == "192.0.2.55"
        ]
        firewall_knock_ports = [
            event.get("Destination Port")
            for event in firewall_events
            if event.get("Source IP") == "10.42.0.7"
            and event.get("Destination IP") == "192.0.2.55"
        ]

        self.assertEqual(vcn_knock_ports[:4], ["7000", "8000", "9000", "22"])
        self.assertEqual(firewall_knock_ports[:4], ["7000", "8000", "9000", "22"])

    def test_octo_apm_demo_events_include_logs_spans_and_metrics(self):
        random.seed(35)
        events = generate_application_events()

        octo_events = [
            event for event in events
            if event.get("serviceName") == "octo-apm-demo"
            and not str(event.get("traceId", "")).startswith("trace_oke_")
        ]
        oke_events = [
            event for event in events
            if str(event.get("traceId", "")).startswith("trace_oke_")
        ]
        self.assertGreaterEqual(len(octo_events), 8)
        self.assertGreaterEqual(len(oke_events), 4)

        traces = defaultdict(set)
        for event in octo_events:
            self.assertTrue(event.get("traceId", "").startswith("trace_octo_apm_"))
            self.assertEqual(event.get("trace_id"), event.get("traceId"))
            self.assertEqual(event.get("oracleApmTraceId"), event.get("traceId"))
            self.assertTrue(event.get("spanId", "").startswith("span_"))
            self.assertEqual(event.get("span_id"), event.get("spanId"))
            self.assertEqual(event.get("oracleApmSpanId"), event.get("spanId"))
            self.assertEqual(event.get("service.namespace"), "octo")
            self.assertEqual(event.get("service.name"), event.get("serviceName"))
            self.assertIn("request_id", event)
            self.assertIn("workflow_id", event)
            self.assertIn("workflow_step", event)
            self.assertIn("http.method", event)
            self.assertIn("http.request.method", event)
            self.assertIn("http.url.path", event)
            self.assertIn("http.status_code", event)
            self.assertIn("http.response_time_ms", event)
            self.assertIn("apmDomain", event)
            traces[event["traceId"]].add(event["spanId"])

        for event in oke_events:
            self.assertEqual(event.get("serviceName"), "octo-apm-demo")
            self.assertTrue(event.get("traceId", "").startswith("trace_oke_"))
            self.assertEqual(event.get("service.namespace"), "octo")
            self.assertEqual(event.get("security.attack.type"), "oke_kubernetes_attack")

        self.assertTrue(any(len(span_ids) >= 3 for span_ids in traces.values()))
        self.assertTrue(any(event.get("parentSpanId") for event in octo_events))
        self.assertTrue(any(event.get("metricName") for event in octo_events))
        self.assertTrue(any(event.get("level") == "ERROR" for event in octo_events))
        self.assertTrue(any(event.get("dbTarget") == "oracle_atp" for event in octo_events))
        self.assertTrue(any(event.get("db.statement") for event in octo_events))

        java_sidecar_events = [
            event for event in events
            if event.get("java_apm.path") == "/api/java-apm/payment/authorize"
        ]
        self.assertGreaterEqual(len(java_sidecar_events), 1)
        self.assertTrue(any(event.get("java_apm.error_type") for event in java_sidecar_events))

    def test_octo_attack_lab_events_are_huntable_and_card_safe(self):
        random.seed(36)
        events = generate_application_events()

        attack_events = [
            event for event in events
            if event.get("security.attack.id") == "attack-octo-demo-001"
        ]

        self.assertGreaterEqual(len(attack_events), 6)
        self.assertEqual({event.get("run_id") for event in attack_events}, {"run-octo-attack-lab-001"})
        self.assertEqual({event.get("request_id") for event in attack_events}, {"req_octo_attack_001"})
        self.assertTrue(any(event.get("vm.compromised") is True for event in attack_events))
        self.assertTrue(any(event.get("payment.interception.detected") is True for event in attack_events))
        self.assertTrue(any(event.get("payment.redirect.detected") is True for event in attack_events))
        self.assertTrue(any(event.get("payment.redirect.url") for event in attack_events))
        self.assertTrue(any(event.get("cloud.instance.id", "").startswith("ocid1.instance.") for event in attack_events))
        self.assertTrue(any(event.get("osquery.query") for event in attack_events))
        self.assertTrue(any(event.get("oci.api_gateway.request_id") == "gw-req_octo_attack_001" for event in attack_events))
        self.assertTrue(any(event.get("oci.api_gateway.action") == "allow" for event in attack_events))
        self.assertTrue(any(event.get("oci.api_gateway.policy.decision") == "suspicious_burst_observed" for event in attack_events))
        self.assertNotIn("4242424242424242", str(attack_events))

    def test_waf_events_include_cors_and_allowed_sqli_cases(self):
        random.seed(37)
        events = generate_waf_events()

        cors_blocks = [
            event for event in events
            if event.get("action") == "BLOCK"
            and "Origin:" in event.get("requestHeaders", "")
        ]
        allowed_sqli = [
            event for event in events
            if event.get("action") == "DETECT"
            and event.get("responseCode") == "200"
            and any(token in event.get("requestUrl", "") for token in ("UNION SELECT", "sleep(5)", "'--"))
        ]

        self.assertGreaterEqual(len(cors_blocks), 5)
        self.assertGreaterEqual(len(allowed_sqli), 3)

    def test_waf_events_include_recent_sqli_block_showcase_cases(self):
        random.seed(39)
        events = generate_waf_events()

        recent_sqli_blocks = [
            event for event in events
            if event.get("action") == "BLOCK"
            and event.get("protectionRuleKey", "").startswith("942")
            and event.get("timeCreated", "") >= (
                BASE_TIME + timedelta(hours=20)
            ).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            and any(
                token in event.get("requestUrl", "")
                for token in ("OR 1=1", "UNION%20SELECT", "SLEEP(5)")
            )
        ]

        self.assertGreaterEqual(len(recent_sqli_blocks), 3)

    def test_web_to_cloud_chain_correlates_entry_point_to_cloud_exfiltration(self):
        random.seed(43)
        trace_id = "trace_w2c_entry_001"
        attacker_ip = "185.220.101.1"
        compromised_host = "app-prod-02"
        compromised_private_ip = "10.0.1.50"
        c2_ip = "198.51.100.77"

        datasets = {
            "waf": generate_waf_events(),
            "lb": generate_lb_access_events(),
            "webapp": generate_webapp_events(),
            "application": generate_application_events(),
            "linux": generate_linux_secure(),
            "oci": generate_oci_audit_events(),
            "sysmon_network": generate_sysmon_network_events(),
            "vcn": generate_vcn_flow_events(),
            "firewall": generate_network_firewall_events(),
        }

        self.assertTrue(any(
            event.get("traceId") == trace_id
            and event.get("clientAddress") == attacker_ip
            and event.get("action") == "DETECT"
            and "169.254.169.254" in event.get("requestUrl", "")
            for event in datasets["waf"]
        ))
        self.assertTrue(any(
            event.get("traceId") == trace_id
            and event.get("clientAddress") == attacker_ip
            and event.get("backendAddress", "").startswith(compromised_private_ip)
            for event in datasets["lb"]
        ))
        self.assertTrue(any(
            event.get("traceId") == trace_id
            and event.get("hostname") == compromised_host
            and event.get("securityAttackType") == "ssrf_metadata_access"
            for event in datasets["application"]
        ))
        self.assertTrue(any(
            event.get("Hostname") == compromised_host
            and "169.254.169.254" in event.get("Command Line", "")
            for event in datasets["linux"]
        ))
        self.assertTrue(any(
            event.get("eventType") == "com.oraclecloud.objectstorage.getobject"
            and event.get("data", {}).get("identity", {}).get("principalName") == "compromised-svc@corp.example.com"
            and "prod-customer-backups" in event.get("data", {}).get("resourceName", "")
            for event in datasets["oci"]
        ))
        self.assertTrue(any(
            event.get("Host Name (Server)") == "SRV01.sevenkingdoms.local"
            and event.get("Destination IP") == c2_ip
            for event in datasets["sysmon_network"]
        ))
        self.assertTrue(any(
            event.get("Trace ID") == trace_id
            and event.get("data", {}).get("srcaddr") == compromised_private_ip
            and event.get("data", {}).get("dstaddr") == c2_ip
            and int(event.get("data", {}).get("bytesOut", 0)) > 50000000
            for event in datasets["vcn"]
        ))
        self.assertTrue(any(
            event.get("Trace ID") == trace_id
            and event.get("logContent", {}).get("data", {}).get("src_ip") == compromised_private_ip
            and event.get("logContent", {}).get("data", {}).get("dst_ip") == c2_ip
            and event.get("Threat Name") == "Suspicious Data Exfiltration"
            for event in datasets["firewall"]
        ))

    def test_2025_2026_attack_scenarios_have_cross_source_pivots(self):
        random.seed(49)
        datasets = {
            "windows": generate_windows_events(),
            "winsec": generate_windows_event_security(),
            "sysmon_network": generate_sysmon_network_events(),
            "waf": generate_waf_events(),
            "lb": generate_lb_access_events(),
            "webapp": generate_webapp_events(),
            "application": generate_application_events(),
            "oci": generate_oci_audit_events(),
            "vcn": generate_vcn_flow_events(),
            "firewall": generate_network_firewall_events(),
        }

        clickfix_commands = [
            event.get("Command Line") or event.get("CommandLine") or ""
            for event in datasets["windows"] + datasets["winsec"]
        ]
        self.assertTrue(any("ClickFix" in command and "powershell" in command.lower() for command in clickfix_commands))
        self.assertTrue(any("mshta.exe" in command.lower() and "captcha" in command.lower() for command in clickfix_commands))
        self.assertTrue(any("crashfix" in command.lower() and "python" in command.lower() for command in clickfix_commands))

        self.assertTrue(any(
            "spinstall0.aspx" in event.get("requestUrl", "").lower()
            and event.get("traceId") == "trace_toolshell_sp_001"
            for event in datasets["waf"] + datasets["lb"] + datasets["webapp"]
        ))
        self.assertTrue(any(
            event.get("traceId") == "trace_toolshell_sp_001"
            and "ToolShell" in (event.get("securityAttackType") or "")
            for event in datasets["application"]
        ))

        self.assertTrue(any(
            event.get("Process Name", "").endswith(("ScreenConnect.ClientService.exe", "AnyDesk.exe", "AteraAgent.exe"))
            for event in datasets["windows"]
        ))
        self.assertTrue(any(
            event.get("Destination Hostname") in {"relay.screenconnect.example", "rmm-sync.atera.example"}
            for event in datasets["sysmon_network"]
        ))

        self.assertTrue(any(
            event.get("data", {}).get("identity", {}).get("principalName") == "codeofconduct-reader@corp.example.com"
            and event.get("Attack Stage") == "aitm_token_abuse"
            for event in datasets["oci"]
        ))

        self.assertTrue(any(
            event.get("Trace ID") == "trace_clickfix_2026_001"
            and event.get("Attack Stage") == "exfiltration"
            and int(event.get("Bytes Sent", "0")) > 25000000
            for event in datasets["vcn"] + datasets["firewall"]
        ))

    def test_network_datasets_use_vendor_envelopes_and_detection_aliases(self):
        random.seed(47)
        vcn_events = generate_vcn_flow_events()
        firewall_events = generate_network_firewall_events()

        self.assertTrue(vcn_events)
        self.assertTrue(firewall_events)

        vcn_event = vcn_events[0]
        self.assertIn("specversion", vcn_event)
        self.assertIn("oracle", vcn_event)
        self.assertIn("data", vcn_event)
        for field in ("srcaddr", "dstaddr", "srcport", "dstport", "protocol", "action", "bytesOut"):
            self.assertIn(field, vcn_event["data"])
        self.assertEqual(vcn_event["Log Source"], "SOC VCN Flow Logs")
        self.assertIn("Source IP", vcn_event)
        self.assertIn("Bytes Sent", vcn_event)

        firewall_event = firewall_events[0]
        self.assertIn("datetime", firewall_event)
        self.assertIn("logContent", firewall_event)
        self.assertIn("data", firewall_event["logContent"])
        for field in ("log_type", "action", "src_ip", "dst_ip", "src_port", "dst_port", "bytes_sent"):
            self.assertIn(field, firewall_event["logContent"]["data"])
        self.assertEqual(firewall_event["Log Source"], "SOC Network Firewall Logs")
        self.assertIn("Source IP", firewall_event)
        self.assertIn("Bytes Sent", firewall_event)

    def test_sysmon_operational_includes_screen_capture_burst(self):
        random.seed(11)
        events = generate_sysmon_operational()

        buckets = defaultdict(int)
        for event in events:
            if str(event.get("Event ID") or event.get("EventID")) != "11":
                continue
            target_filename = event.get("Target Filename", "")
            if not target_filename.lower().endswith(".jpg"):
                continue
            minute_bucket = (event.get("TimeCreated") or "")[:16]
            buckets[(minute_bucket, event.get("Process Name"))] += 1

        self.assertTrue(buckets)
        self.assertGreaterEqual(max(buckets.values()), 4)

    def test_bluelight_kill_chain_has_multi_stage_host_coverage(self):
        random.seed(13)
        stage_hits = defaultdict(set)
        datasets = (
            generate_windows_events()
            + generate_sysmon_operational()
            + generate_sysmon_network_events()
        )

        for event in datasets:
            host = event.get("Host Name (Server)") or event.get("Computer")
            event_id = str(event.get("Event ID") or event.get("EventID"))
            process_name = (event.get("Process Name") or event.get("Image") or "").lower()
            parent_name = (event.get("Parent Process Name") or event.get("ParentImage") or "").lower()
            target_process = (event.get("Target Process") or event.get("TargetImage") or "").lower()
            source_process = (event.get("Source Process") or event.get("SourceImage") or "").lower()
            destination = (event.get("Destination Hostname") or event.get("DestinationHostname") or "").lower()
            command_line = (event.get("Command Line") or event.get("CommandLine") or "").lower()

            if event_id == "1" and "iexplore.exe" in parent_name and any(
                binary in process_name for binary in ("cmd.exe", "powershell.exe", "wscript.exe")
            ):
                stage_hits[host].add("initial_access")
            if event_id == "3" and "graph.microsoft.com" in destination and not any(
                allowed in process_name for allowed in ("onedrive.exe", "teams.exe", "outlook.exe")
            ):
                stage_hits[host].add("graph_c2")
            if event_id == "10" and any(browser in target_process for browser in ("chrome.exe", "firefox.exe")) and not any(
                browser in source_process for browser in ("chrome.exe", "firefox.exe")
            ):
                stage_hits[host].add("credential_access")
            if "win32_computersystem" in command_line or "win32_operatingsystem" in command_line:
                stage_hits[host].add("discovery")
            if "frombase64string" in command_line or "-bxor" in command_line:
                stage_hits[host].add("obfuscation")

        self.assertTrue(
            any(len(stages) >= 3 for stages in stage_hits.values()),
            stage_hits,
        )


if __name__ == "__main__":
    unittest.main()
