"""Static log-source/parser/field definitions (WAF / Load Balancer / Web application source + parser definitions).

Auto-extracted from setup_log_sources.py (behavior-preserving). Pure data — no
logic, no OCI calls.
"""


WAF_PARSER_NAME = "socWafSecurityJsonParser"
WAF_PARSER_DISPLAY = "SOC WAF Security JSON Parser"
WAF_PARSER_DESC = (
    "Parses OCI WAF security event JSON for OWASP attack detection. "
    "Maps action, request URL, HTTP method, client IP, user agent, rule details."
)
WAF_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                1),
    ("time",                 "$.timeCreated",        2),
    ("Action",               "$.action",             3),
    ("HTTP Method",          "$.httpMethod",         4),
    ("Request URL",          "$.requestUrl",         5),
    ("URI Path",             "$.requestUrl",         6),
    ("Query String",         "$.queryString",        7),
    ("Client IP",            "$.clientAddress",      8),
    ("Country Code",         "$.countryCode",        9),
    ("User Agent",           "$.userAgent",         10),
    ("Response Code",        "$.responseCode",      11),
    ("Rule Type",            "$.type",              12),
    ("Rule Key",             "$.protectionRuleKey", 13),
    ("Rule Action",          "$.protectionRuleAction", 14),
    ("Request Body",         "$.bodyData",          15),
    ("Content Type",         "$.contentType",       16),
    ("Referrer",             "$.referer",           17),
    ("Request Headers",      "$.requestHeaders",    18),
    ("WAF Policy",           "$.wafPolicy",         19),
    ("Fingerprint",          "$.fingerprint",       20),
    ("Host Name",            "$.hostname",          21),
    ("Trace ID",             "$.traceId",           22),
    ("Service Name",         "$.wafPolicy",         23),
    ("WAF Action",           "$.action",            24),
]
WAF_EXAMPLE = {
    "timeCreated": "2026-02-15T14:30:00.000Z",
    "action": "BLOCK",
    "httpMethod": "GET",
    "requestUrl": "/vulnerable/search?q=1' OR '1'='1",
    "queryString": "q=1' OR '1'='1",
    "clientAddress": "xxx",
    "countryCode": "RU",
    "userAgent": "sqlmap/1.7",
    "responseCode": "403",
    "type": "PROTECTION_RULES",
    "protectionRuleKey": "941100",
    "protectionRuleAction": "BLOCK",
    "bodyData": "",
    "contentType": "text/html",
    "referer": "",
    "requestHeaders": "Host: sevenkingdoms.example.com",
    "wafPolicy": "seven-kingdoms-portal-waf",
    "fingerprint": "abc123def456",
    "hostname": "sevenkingdoms.example.com",
    "msg": "WAF BLOCK: SQL Injection attempt in /vulnerable/search",
}

WAF_SOURCE_INTERNAL = "socWafSecuritySource"
WAF_SOURCE_DISPLAY = "SOC WAF Security Logs"
WAF_SOURCE_DESC = (
    "OCI WAF security events in JSON format for OWASP attack detection and threat hunting."
)


# ─── OCI Load Balancer Access Log Parser ──────────────────────

LB_PARSER_NAME = "socLbAccessJsonParser"
LB_PARSER_DISPLAY = "SOC Load Balancer Access JSON Parser"
LB_PARSER_DESC = (
    "Parses OCI Load Balancer access log JSON for web traffic analysis. "
    "Maps HTTP method, request URL, status code, client IP, user agent, timing."
)
LB_FIELD_MAPPINGS = [
    ("msg",                      "$.msg",                     1),
    ("time",                     "$.timeCreated",             2),
    ("HTTP Method",              "$.httpMethod",              3),
    ("Request URL",              "$.requestUrl",              4),
    ("URI Path",                 "$.uriPath",                 5),
    ("Query String",             "$.queryString",             6),
    ("Client IP",                "$.clientAddress",           7),
    ("User Agent",               "$.userAgent",               8),
    ("Response Code",            "$.statusCode",              9),
    ("Backend Status Code",      "$.backendStatusCode",      10),
    ("Backend Address",          "$.backendAddress",         11),
    ("Bytes Received",           "$.bytesReceived",          12),
    ("Bytes Sent",               "$.bytesSent",              13),
    ("Request Processing Time",  "$.requestProcessingTime",  14),
    ("Host Name",                "$.hostname",               15),
    ("Load Balancer Name",       "$.lbName",                 16),
    ("Listener Name",            "$.listenerName",           17),
    ("Content Type",             "$.contentType",            18),
    ("Referrer",                 "$.referer",                19),
    ("Trace ID",                 "$.traceId",                20),
]
LB_EXAMPLE = {
    "timeCreated": "2026-02-15T14:30:00.000Z",
    "httpMethod": "POST",
    "requestUrl": "/vulnerable/login",
    "uriPath": "/vulnerable/login",
    "queryString": "",
    "clientAddress": "xxx",
    "userAgent": "Mozilla/5.0 (compatible; Hydra/9.0)",
    "statusCode": "401",
    "backendStatusCode": "401",
    "backendAddress": "10.0.1.50:9010",
    "bytesReceived": "1024",
    "bytesSent": "256",
    "requestProcessingTime": "15",
    "hostname": "sevenkingdoms.example.com",
    "lbName": "seven-kingdoms-portal-lb",
    "listenerName": "http-listener",
    "contentType": "application/x-www-form-urlencoded",
    "referer": "https://sevenkingdoms.example.com/vulnerable/login",
    "traceId": "trace_demo_lb_001",
    "msg": "POST /vulnerable/login 401 - Hydra/9.0",
}

LB_SOURCE_INTERNAL = "socLbAccessSource"
LB_SOURCE_DISPLAY = "SOC Load Balancer Access Logs"
LB_SOURCE_DESC = (
    "OCI Load Balancer access log events in JSON format for web traffic analysis and threat detection."
)


# ─── Web Application Log Parser ───────────────────────────────

WEBAPP_PARSER_NAME = "socWebAppJsonParser"
WEBAPP_PARSER_DISPLAY = "SOC Web Application JSON Parser"
WEBAPP_PARSER_DESC = (
    "Parses web application security events (Seven Kingdoms Portal) for attack detection. "
    "Maps attack type, OWASP category, request details, and vulnerability context."
)
WEBAPP_FIELD_MAPPINGS = [
    ("msg",                  "$.msg",                1),
    ("time",                 "$.timestamp",          2),
    ("HTTP Method",          "$.httpMethod",         3),
    ("Request URL",          "$.requestUrl",         4),
    ("URI Path",             "$.uriPath",            5),
    ("Query String",         "$.queryString",        6),
    ("Client IP",            "$.clientAddress",      7),
    ("User Agent",           "$.userAgent",          8),
    ("Response Code",        "$.statusCode",         9),
    ("Attack Type",          "$.attackType",        10),
    ("Attack Payload",       "$.attackPayload",     11),
    ("OWASP Category",       "$.owaspCategory",     12),
    ("Vulnerability ID",     "$.vulnerabilityId",   13),
    ("Session ID",           "$.sessionId",         14),
    ("Application Name",     "$.appName",           15),
    ("Request ID",           "$.requestId",         16),
    ("Host Name",            "$.hostname",          17),
    ("Request Body",         "$.requestBody",       18),
    ("Content Type",         "$.contentType",       19),
    ("User",                 "$.user",              20),
    ("Trace ID",             "$.traceId",           21),
]
WEBAPP_EXAMPLE = {
    "timestamp": "2026-02-15T14:30:00.000Z",
    "httpMethod": "POST",
    "requestUrl": "/vulnerable/api/users/1",
    "uriPath": "/vulnerable/api/users/1",
    "queryString": "",
    "clientAddress": "xxx",
    "userAgent": "python-requests/2.28.0",
    "statusCode": "200",
    "attackType": "IDOR",
    "attackPayload": "id=1",
    "owaspCategory": "A01:2021-Broken Access Control",
    "vulnerabilityId": "CVE-2024-DEMO-001",
    "sessionId": "sess_abc123def456",
    "appName": "seven-kingdoms-portal",
    "requestId": "req_789xyz",
    "hostname": "sevenkingdoms.example.com",
    "requestBody": "{\"id\": 1, \"role\": \"admin\"}",
    "contentType": "application/json",
    "user": "anonymous",
    "traceId": "trace_demo_webapp_001",
    "msg": "IDOR: Unauthorized access to user profile id=1",
}

WEBAPP_SOURCE_INTERNAL = "socWebAppSource"
WEBAPP_SOURCE_DISPLAY = "SOC Web Application Logs"
WEBAPP_SOURCE_DESC = (
    "Web application security events from Seven Kingdoms Portal for OWASP attack detection."
)


# ─── Application Telemetry Parser ─────────────────────────────
