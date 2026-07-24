"""Tests for Windows Security + Sysmon schema split.

Pins two distinct event shapes:
    Security (Channel: Security, Provider: Microsoft-Windows-Security-Auditing)
    Sysmon   (Channel: Microsoft-Windows-Sysmon/Operational)

Both include source-native PascalCase fields (what Windows emits) plus OCI
Log Analytics display-name parallel columns (what OCL queries reference).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


class TestWindowsSecuritySchema:
    @pytest.fixture
    def logon_failure(self):
        from schemas.windows_audit_schema import build_windows_security_event
        return build_windows_security_event(
            4625,
            event_time="2026-04-24T12:00:00.000Z",
            computer="DC01.test.local",
            user="arya.stark",
            target_user_name="admin",
            source_address="203.0.113.1",
            logon_type=10,
            failure_reason="0xC000006D",
        )

    @pytest.fixture
    def process_creation(self):
        from schemas.windows_audit_schema import build_windows_security_event
        return build_windows_security_event(
            4688,
            event_time="2026-04-24T12:00:00.000Z",
            computer="WS01.test.local",
            user="eddard.stark",
            new_process_name=r"C:\Windows\System32\powershell.exe",
            command_line="powershell.exe -enc SQBFAFgA",
        )

    def test_security_channel_and_provider(self, logon_failure):
        assert logon_failure["Channel"] == "Security"
        assert logon_failure["Provider"] == "Microsoft-Windows-Security-Auditing"

    def test_security_core_fields(self, logon_failure):
        required = {"EventID", "TimeCreated", "Computer", "User", "Channel", "Provider"}
        assert required.issubset(logon_failure.keys())
        assert logon_failure["EventID"] == 4625

    def test_security_native_pascalcase_fields(self, logon_failure):
        # When the builder is called with snake_case kwargs, it must still
        # emit the PascalCase field names that real Windows events use.
        assert logon_failure["TargetUserName"] == "admin"
        assert logon_failure["SourceAddress"] == "203.0.113.1"
        assert logon_failure["LogonType"] == 10
        assert logon_failure["FailureReason"] == "0xC000006D"

    def test_security_ocl_display_columns(self, logon_failure):
        required = {
            "Log Source", "Event ID", "Host Name (Server)", "Host Name",
            "User Name", "Target User Name", "Source IP", "Logon Type",
        }
        assert required.issubset(logon_failure.keys())
        assert logon_failure["Log Source"] == "Windows Security Events"
        assert logon_failure["Event ID"] == 4625

    def test_process_creation_name_fields(self, process_creation):
        # Process name should appear under both native + display forms
        assert process_creation["NewProcessName"].endswith("powershell.exe")
        assert process_creation["Process Name"].endswith("powershell.exe")
        assert process_creation["Command Line"].startswith("powershell.exe")

    def test_sysmon_fields_absent_from_security(self, logon_failure):
        # Sysmon-only fields must not leak into Security events
        for f in ("PipeName", "QueryName", "Hashes", "ParentImage"):
            assert f not in logon_failure


class TestWindowsSysmonSchema:
    @pytest.fixture
    def pipe_create(self):
        from schemas.windows_audit_schema import build_windows_sysmon_event
        return build_windows_sysmon_event(
            17,
            event_time="2026-04-24T12:00:00.000Z",
            computer="SRV01.test.local",
            user="eddard.stark",
            image=r"C:\Windows\System32\svchost.exe",
            pipe_name=r"\msagent_1234",
        )

    @pytest.fixture
    def dns_query(self):
        from schemas.windows_audit_schema import build_windows_sysmon_event
        return build_windows_sysmon_event(
            22,
            event_time="2026-04-24T12:00:00.000Z",
            computer="WS01.test.local",
            user="arya.stark",
            image=r"C:\Windows\System32\svchost.exe",
            query_name="evil-c2.example.invalid",
            query_results="203.0.113.9",
        )

    def test_sysmon_channel_and_provider(self, pipe_create):
        assert pipe_create["Channel"] == "Microsoft-Windows-Sysmon/Operational"
        assert pipe_create["Provider"] == "Microsoft-Windows-Sysmon"

    def test_sysmon_utctime_field(self, pipe_create):
        # Real Sysmon events include UtcTime; Security events do not
        assert "UtcTime" in pipe_create

    def test_sysmon_native_fields(self, pipe_create, dns_query):
        assert pipe_create["Image"].endswith("svchost.exe")
        assert pipe_create["PipeName"] == r"\msagent_1234"
        assert dns_query["QueryName"] == "evil-c2.example.invalid"

    def test_sysmon_ocl_display_columns(self, pipe_create, dns_query):
        for evt in (pipe_create, dns_query):
            required = {
                "Log Source", "Event ID", "Host Name (Server)",
                "User Name", "Process Name",
            }
            assert required.issubset(evt.keys())
            assert evt["Log Source"] == "Windows Sysmon Events"
        assert pipe_create["Pipe Name"] == r"\msagent_1234"
        assert dns_query["DNS Query"] == "evil-c2.example.invalid"


class TestGeneratedLogsSplit:
    def test_security_file_only_has_security_events(self):
        path = ROOT / "detection_logs" / "windows_security.jsonl"
        if not path.exists():
            pytest.skip("windows_security.jsonl not generated yet")
        events = [json.loads(l) for l in path.open()]
        assert len(events) > 0
        for e in events:
            assert e["Channel"] == "Security", \
                f"Non-security event leaked into windows_security.jsonl: EventID={e.get('EventID')}"
            assert e["Provider"] == "Microsoft-Windows-Security-Auditing"

    def test_sysmon_file_only_has_sysmon_events(self):
        path = ROOT / "detection_logs" / "windows_sysmon.jsonl"
        if not path.exists():
            pytest.skip("windows_sysmon.jsonl not generated yet")
        events = [json.loads(l) for l in path.open()]
        assert len(events) > 0
        for e in events:
            assert e["Channel"] == "Microsoft-Windows-Sysmon/Operational", \
                f"Non-sysmon event leaked into windows_sysmon.jsonl: EventID={e.get('EventID')}"
            assert e["Provider"] == "Microsoft-Windows-Sysmon"

    def test_ocl_columns_on_every_event(self):
        for filename in ("windows_security.jsonl", "windows_sysmon.jsonl"):
            path = ROOT / "detection_logs" / filename
            if not path.exists():
                continue
            for e in (json.loads(l) for l in path.open()):
                assert "Log Source" in e
                assert "Event ID" in e
                assert "Host Name (Server)" in e
                assert "User Name" in e
