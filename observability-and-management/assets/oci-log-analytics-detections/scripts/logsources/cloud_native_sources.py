"""Static log-source/parser/field definitions (Azure / VCN flow / Network Firewall / health source definitions).

Auto-extracted from setup_log_sources.py (behavior-preserving). Pure data — no
logic, no OCI calls.
"""


AZURE_CUSTOM_SOURCE_INTERNAL = "azureLogAnalyticsCustomSource"
AZURE_CUSTOM_SOURCE_DISPLAY = "Azure Log Analytics Custom Logs"
AZURE_CUSTOM_SOURCE_DESC = (
    "Azure Log Analytics custom-table records migrated from Microsoft Sentinel "
    "workspaces for Phase A Azure-as-is detection validation."
)


# ─── OCI VCN Flow Log Parser ──────────────────────────────────

VCN_PARSER_NAME = "socVcnFlowJsonParser"
VCN_PARSER_DISPLAY = "SOC VCN Flow JSON Parser"
VCN_PARSER_DESC = (
    "Parses OCI VCN Flow Log JSON for network egress, C2, and exfiltration hunting. "
    "Maps vendor nested data fields plus SOC aliases for source/destination and byte counts."
)
VCN_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                         1),
    ("time",                 "$.time",                        2),
    ("Source IP",            "$.data.sourceAddress",          3),
    ("Destination IP",       "$.data.destinationAddress",     4),
    ("Source Port",          "$.data.sourcePort",             5),
    ("Destination Port",     "$.data.destinationPort",        6),
    ("Protocol",             "$.data.protocol",               7),
    ("Action",               "$.data.action",                 8),
    ("Network Action",       "$.data.action",                 9),
    ("Bytes Sent",           "$.data.bytesOut",              10),
    ("Bytes Received",       "$.data.bytesIn",               11),
    ("Packets",              "$.data.packetsOut",            12),
    ("Flow ID",              "$.data.flowId",                13),
    ("Resource ID",          "$.data.vnicId",                14),
    ("Trace ID",             "$.Trace ID",                   15),
    ("Log Type",             "$.type",                       16),
]
VCN_EXAMPLE = {
    "time": "2026-05-04T10:15:00.000Z",
    "type": "com.oraclecloud.vcn.flowlogs.DataEvent",
    "data": {
        "sourceAddress": "10.0.1.50",
        "destinationAddress": "198.51.100.77",
        "sourcePort": 45010,
        "destinationPort": 443,
        "protocol": "6",
        "action": "ACCEPT",
        "bytesOut": 73400320,
        "bytesIn": 2048,
        "packetsOut": 4200,
        "flowId": "flow-w2c-c2-004",
        "vnicId": "ocid1.vnic.oc1..example",
    },
    "Trace ID": "trace_w2c_entry_001",
    "msg": "VCN Flow ACCEPT: 10.0.1.50:45010 -> 198.51.100.77:443",
}

VCN_SOURCE_INTERNAL = "socVcnFlowSource"
VCN_SOURCE_DISPLAY = "SOC VCN Flow Logs"
VCN_SOURCE_DESC = (
    "OCI VCN Flow Log records in JSON format for network egress and exfiltration drilldowns."
)


# ─── OCI Network Firewall Log Parser ───────────────────────────

FW_PARSER_NAME = "socNetworkFirewallJsonParser"
FW_PARSER_DISPLAY = "SOC Network Firewall JSON Parser"
FW_PARSER_DESC = (
    "Parses OCI Network Firewall traffic and threat logs. Maps session, rule, action, "
    "byte volume, and threat fields for web-to-cloud attack drilldowns."
)
FW_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                         1),
    ("time",                 "$.logContent.time",             2),
    ("Log Type",             "$.logContent.data.log_type",    3),
    ("Action",               "$.logContent.data.action",      4),
    ("Network Action",       "$.logContent.data.action",      5),
    ("Source IP",            "$.logContent.data.src",         6),
    ("Destination IP",       "$.logContent.data.dst",         7),
    ("Source Port",          "$.logContent.data.sport",       8),
    ("Destination Port",     "$.logContent.data.dport",       9),
    ("Protocol",             "$.logContent.data.proto",      10),
    ("Bytes Sent",           "$.logContent.data.bytes_sent", 11),
    ("Bytes Received",       "$.logContent.data.bytes_received", 12),
    ("Firewall Rule",        "$.logContent.data.rule",       13),
    ("Threat Name",          "$.logContent.data.threatid",   14),
    ("Threat Category",      "$.logContent.data.category",   15),
    ("Severity Level",       "$.logContent.data.severity",   16),
    ("Direction",            "$.logContent.data.direction",  17),
    ("Session ID",           "$.logContent.data.sessionid",  18),
    ("Trace ID",             "$.Trace ID",                   19),
]
FW_EXAMPLE = {
    "datetime": 1777890300000,
    "logContent": {
        "time": "2026-05-04T10:25:00.000Z",
        "type": "com.oraclecloud.networkfirewall.logs",
        "data": {
            "log_type": "threat",
            "src": "10.0.1.50",
            "dst": "198.51.100.77",
            "sport": "45010",
            "dport": "443",
            "proto": "tcp",
            "action": "alert",
            "rule": "inspect-app-egress",
            "bytes_sent": "73400320",
            "bytes_received": "2048",
            "threatid": "Suspicious Data Exfiltration",
            "category": "data-theft",
            "severity": "critical",
            "sessionid": "1234567890",
        },
    },
    "Trace ID": "trace_w2c_entry_001",
    "msg": "Network Firewall threat alert: 10.0.1.50 -> 198.51.100.77",
}

FW_SOURCE_INTERNAL = "socNetworkFirewallSource"
FW_SOURCE_DISPLAY = "SOC Network Firewall Logs"
FW_SOURCE_DESC = (
    "OCI Network Firewall traffic and threat logs in JSON format for C2 and exfiltration analysis."
)


# ─── Multicloud Health Parser ──────────────────────────────────

HEALTH_PARSER_NAME = "socMulticloudHealthJsonParser"
HEALTH_PARSER_DISPLAY = "SOC Multicloud Health JSON Parser"
HEALTH_PARSER_DESC = (
    "Parses multicloud health heartbeat JSON for geographic map visualization. "
    "Maps cloud provider, region, lat/lon coordinates, instance metadata, and health metrics."
)
HEALTH_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                1),
    ("time",                 "$.Timestamp",           2),
    ("Cloud Provider",       "$.Cloud Provider",      3),
    ("Region",               "$.Region",              4),
    ("Region Display",       "$.Region Display",      5),
    ("Country",              "$.Country",             6),
    ("Latitude",             "$.Latitude",            7),
    ("Longitude",            "$.Longitude",           8),
    ("Instance ID",          "$.Instance ID",         9),
    ("Host Name",            "$.Host Name",          10),
    ("IP Address",           "$.IP Address",         11),
    ("Instance Role",        "$.Instance Role",      12),
    ("Service Name",         "$.Service",            13),
    ("Tier",                 "$.Tier",               14),
    ("Operating System",     "$.Operating System",   15),
    ("Instance Type",        "$.Instance Type",      16),
    ("Status",               "$.Status",             17),
    ("Status Code",          "$.Status Code",        18),
    ("CPU Percent",          "$.CPU Percent",        19),
    ("Memory Percent",       "$.Memory Percent",     20),
    ("Disk Percent",         "$.Disk Percent",       21),
    ("Network In Mbps",      "$.Network In Mbps",    22),
    ("Network Out Mbps",     "$.Network Out Mbps",   23),
    ("Uptime Hours",         "$.Uptime Hours",       24),
    ("Open Connections",     "$.Open Connections",   25),
    ("Response Time Ms",     "$.Response Time Ms",   26),
    ("Heartbeat Sequence",   "$.Heartbeat Sequence", 27),
]
HEALTH_EXAMPLE = {
    "Timestamp": "2026-03-10T09:00:00.000Z",
    "Cloud Provider": "OCI",
    "Region": "eu-frankfurt-1",
    "Region Display": "Germany Central (Frankfurt)",
    "Country": "DE",
    "Latitude": 50.1109,
    "Longitude": 8.6821,
    "Instance ID": "ocid1.instance.oc1.eu-frankfurt-1.example",
    "Host Name": "web-server-eu-001",
    "IP Address": "10.0.1.10",
    "Instance Role": "web-server",
    "Service": "nginx",
    "Tier": "frontend",
    "Operating System": "Oracle Linux 9",
    "Instance Type": "VM.Standard.E4.Flex",
    "Status": "healthy",
    "Status Code": 200,
    "CPU Percent": 35.2,
    "Memory Percent": 48.7,
    "Disk Percent": 42.1,
    "Network In Mbps": 15.3,
    "Network Out Mbps": 8.7,
    "Uptime Hours": 720,
    "Open Connections": 142,
    "Response Time Ms": 12,
    "Heartbeat Sequence": 1,
    "Log Source": "SOC Multicloud Health Logs",
    "msg": "HEARTBEAT OK: web-server-eu-001 (OCI/eu-frankfurt-1) cpu=35.2% mem=48.7% uptime=720h status=healthy",
}

HEALTH_SOURCE_INTERNAL = "socMulticloudHealthSource"
HEALTH_SOURCE_DISPLAY = "SOC Multicloud Health Logs"
HEALTH_SOURCE_DESC = (
    "Multicloud health heartbeat logs from OCI, Azure, and GCP instances "
    "with geographic coordinates for global map visualization."
)


# Native source alternatives used to avoid creating unnecessary SOC sources.
