"""Aggregated static log-source definitions for setup_log_sources.

Re-exports every per-family data module so callers can ``from logsources.definitions
import *``. Defines the cross-family ``NATIVE_SOURCE_ALTERNATIVES`` map last, after
all referenced ``*_SOURCE_DISPLAY`` names are imported.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logsources.field_catalog import *  # noqa: F401,F403
from logsources.endpoint_sources import *  # noqa: F401,F403
from logsources.web_sources import *  # noqa: F401,F403
from logsources.application_sources import *  # noqa: F401,F403
from logsources.genai_gateway_sources import *  # noqa: F401,F403
from logsources.cloud_native_sources import *  # noqa: F401,F403


NATIVE_SOURCE_ALTERNATIVES = {
    CG_SOURCE_DISPLAY: ["OCI Cloud Guard Problems", "OCI Cloud Guard Logs"],
    CGIS_SOURCE_DISPLAY: ["OCI Cloud Guard Instance Security Logs"],
    OSQUERY_SOURCE_DISPLAY: [],
    WINDOWS_SOURCE_DISPLAY: ["Windows Sysmon Events", "Windows Sysmon Operational Logs"],
    LINUX_SOURCE_DISPLAY: [],
    WINSEC_SOURCE_DISPLAY: [],
    WINSYS_SOURCE_DISPLAY: [],
    LINSEC_SOURCE_DISPLAY: [],
    SYSMON_SOURCE_DISPLAY: [],
    SYSNET_SOURCE_DISPLAY: [],
    WAF_SOURCE_DISPLAY: ["OCI WAF Logs"],
    LB_SOURCE_DISPLAY: ["OCI Load Balancer Access Logs"],
    WEBAPP_SOURCE_DISPLAY: [],
    APP_SOURCE_DISPLAY: [],
    GENAI_SOURCE_DISPLAY: [],
    AZURE_CUSTOM_SOURCE_DISPLAY: [],
    VCN_SOURCE_DISPLAY: ["OCI VCN Flow Logs", "VCN Flow Logs"],
    FW_SOURCE_DISPLAY: ["OCI Network Firewall Logs", "Network Firewall Logs"],
    HEALTH_SOURCE_DISPLAY: [],
}
