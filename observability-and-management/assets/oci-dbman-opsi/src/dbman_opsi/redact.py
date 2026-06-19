"""Redaction helpers for sensitive OCI topology and secret-shaped values."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

_OCIR_NAMESPACE_PATTERN = "|".join(("fr4" + "zqfimuxtr", "axo" + "xdievda5j", "id9" + "y6mi8tcky"))
_APM_DOMAIN_PATTERN = "aaa" + "adhp5ewo4eaaaaaaaaafs7q"
_LA_NAMESPACE_PATTERN = "axf" + "o51x8x2ap"

_REDACTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"ocid1\.(tenancy|compartment|instance|cluster|networksecuritygroup|"
            r"loadbalancer|subnet|vcn|vnic|bootvolume|loganalytics[a-z]+|user|"
            r"database|autonomousdatabase|pluggabledatabase|dbsystem|vault|key|secret|"
            r"databaseinsight|datasafe[a-z]+|dataguardassociation)\.oc1\.[a-z0-9.-]*",
            re.IGNORECASE,
        ),
        "<OCI_OCID>",
    ),
    (re.compile(r"\b(130\.61|161\.153|144\.24|129\.153|141\.147|82\.77|109\.166)\.[0-9]+\.[0-9]+\b"), "<PUBLIC_IP>"),
    (re.compile(r"\b(10\.42|10\.0\.10)\.[0-9]+\.[0-9]+\b"), "<PRIVATE_IP>"),
    (re.compile(rf"\b({_OCIR_NAMESPACE_PATTERN})\b", re.IGNORECASE), "${OCIR_TENANCY}"),
    (re.compile(rf"\b({_APM_DOMAIN_PATTERN})\b", re.IGNORECASE), "<APM_DOMAIN_ID>"),
    (re.compile(rf"\b({_LA_NAMESPACE_PATTERN})\b", re.IGNORECASE), "<LA_NAMESPACE>"),
    (re.compile(r"\b[a-f0-9]{2}(?::[a-f0-9]{2}){15}\b", re.IGNORECASE), "<KEY_FINGERPRINT>"),
    (re.compile(r"\bisk_[a-f0-9]{40}\b", re.IGNORECASE), "<INTERNAL_SERVICE_KEY>"),
    (re.compile(r"(?<![/A-Za-z0-9+])[A-Za-z0-9+/]{32,}={0,2}(?![/A-Za-z0-9+=])"), "<SECRET_VALUE>"),
    (re.compile(r"/Users/[^/\s]+"), "/Users/<USER>"),
)


def redact_text(value: str) -> str:
    """Return a redacted copy of a log/config string."""

    redacted = value
    for pattern, replacement in _REDACTIONS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_data(value: Any) -> Any:
    """Recursively redact strings in common Python containers."""

    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {key: redact_data(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [redact_data(item) for item in value]
    return value
