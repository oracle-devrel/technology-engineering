"""Redact tenancy-specific OCI metadata from live-validation payloads and errors.

OCI SDK ``ServiceError`` payloads carry values that fingerprint a tenancy --
Log Analytics namespaces, ``opc-request-id`` values, request-endpoint URLs, and
OCIDs. These must never be written to committed reports (e.g.
``queries/sentinel_conversion_report.json``) or uploaded as CI artifacts.

Apply :func:`redact_text` (for a single string) or :func:`redact_live_payload`
(for an arbitrary dict/list/str structure) at every sink that records a live
error before it is serialised to disk.

The patterns are *structural* on purpose -- they never hardcode a real tenancy
value, so this module itself stays free of sensitive data.
"""

from __future__ import annotations

import re
from typing import Any

# A bare OCID anywhere in the text.
_OCID_RE = re.compile(r"ocid1\.[a-z0-9]+\.oc1[a-z0-9._-]*", re.IGNORECASE)

# A full OCI service endpoint URL. Matched first so the namespace embedded in the
# path is removed as part of the URL replacement.
_OCI_ENDPOINT_RE = re.compile(
    r"https?://[a-z0-9.-]*\.oci(?:\.oraclecloud)?\.com[^\s'\"]*",
    re.IGNORECASE,
)

# A Log Analytics namespace embedded in a REST path, outside any URL we already
# replaced (e.g. ".../namespaces/<ns>/search/...").
_NAMESPACE_IN_PATH_RE = re.compile(r"(/namespaces/)[a-z0-9]{6,}(/)", re.IGNORECASE)

# An opc-request-id in JSON or single-quoted-dict form. The value is hex with '/'
# separators between the segments.
_OPC_REQUEST_ID_RE = re.compile(
    r"(['\"]?opc-request-id['\"]?\s*[:=]\s*['\"]?)[A-F0-9]{8,}(?:/[A-F0-9]{8,})*(['\"]?)",
    re.IGNORECASE,
)

# Internal-infra public IP ranges from the redaction convention.
_PUBLIC_IP_RE = re.compile(
    r"\b(?:130\.61|161\.153|144\.24|129\.153|141\.147|82\.77|109\.166)\.\d{1,3}\.\d{1,3}\b"
)


def redact_text(value: Any) -> Any:
    """Return ``value`` with tenancy-specific OCI metadata replaced by placeholders.

    Non-string values are returned unchanged so this is safe to call on optional
    error fields that may be ``None``.
    """
    if not isinstance(value, str) or not value:
        return value
    out = _OCI_ENDPOINT_RE.sub("<OCI_ENDPOINT>", value)
    out = _NAMESPACE_IN_PATH_RE.sub(r"\1<LA_NAMESPACE>\2", out)
    out = _OPC_REQUEST_ID_RE.sub(r"\1<OPC_REQUEST_ID>\2", out)
    out = _OCID_RE.sub("<OCID>", out)
    out = _PUBLIC_IP_RE.sub("<PUBLIC_IP>", out)
    return out


def redact_live_payload(obj: Any) -> Any:
    """Recursively redact every string leaf of a dict/list/str structure."""
    if isinstance(obj, str):
        return redact_text(obj)
    if isinstance(obj, dict):
        return {key: redact_live_payload(val) for key, val in obj.items()}
    if isinstance(obj, list):
        return [redact_live_payload(val) for val in obj]
    return obj
