"""
File name: secrets_scan.py
Author: Luigi Saetta
Date last modified: 2025-12-15
Python Version: 3.11

License:
    MIT

Description:
    Basic secrets scanning (heuristic). This is not a full secret-scanner replacement.
"""

from __future__ import annotations

from dataclasses import dataclass
import re


SENSITIVE_NAME_RE = re.compile(
    r"""(?ix)
    \b(
        pass(word|wd)? |
        pwd |
        secret |
        token |
        api[_-]?key |
        client[_-]?secret |
        private[_-]?key |
        bearer |
        auth |
        session |
        cookie |
        oauth |
        key
    )\b
    """
)

ASSIGNMENT_STR_RE = re.compile(
    r"""(?x)
    ^\s*
    (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    \s*=\s*
    (?P<quote>['"])(?P<value>.*?)(?P=quote)
    \s*(?:\#.*)?$
    """
)

DICT_KV_STR_RE = re.compile(
    r"""(?x)
    ^\s*
    (?P<keyquote>['"])(?P<key>[^'"]+)(?P=keyquote)
    \s*:\s*
    (?P<valquote>['"])(?P<value>.*?)(?P=valquote)
    \s*,?\s*(?:\#.*)?$
    """
)

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    (
        "AWS Secret (loose)",
        re.compile(
            r"(?i)\baws(.{0,20})?(secret|access)?.{0,20}['\"][A-Za-z0-9/+=]{30,}['\"]"
        ),
    ),
    ("OCI OCID (resource id)", re.compile(r"\bocid1\.[a-z0-9._-]+\b", re.IGNORECASE)),
    ("GitHub token", re.compile(r"\bghp_[A-Za-z0-9]{30,}\b")),
    ("GitHub fine-grained token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    (
        "Private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)?PRIVATE KEY-----"),
    ),
    (
        "Bearer token header (loose)",
        re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9\-_\.=]{10,}"),
    ),
]

PLACEHOLDER_VALUES = {
    "changeme",
    "change_me",
    "your_token_here",
    "your-key-here",
    "xxx",
    "xxxx",
    "dummy",
    "placeholder",
}


@dataclass(frozen=True)
class SecretFinding:
    kind: str
    line: int
    name_or_key: str
    excerpt: str


def _redact_value(value: str) -> str:
    v = value.strip()
    if not v:
        return "***"
    if len(v) <= 4:
        return "***"
    return f"{v[0]}***{v[-1]}"


def _redact_line_keep_structure(line: str, value: str) -> str:
    red = _redact_value(value)
    return line.replace(value, red, 1)


def _is_probably_secret(name_or_key: str, value: str) -> bool:
    v = value.strip()
    if not v:
        return False
    if v.lower() in PLACEHOLDER_VALUES:
        return False

    if SENSITIVE_NAME_RE.search(name_or_key):
        return True

    if len(v) >= 20 and re.fullmatch(r"[A-Za-z0-9_\-\.=+/]+", v):
        return True

    return False


def scan_for_secrets(source: str, *, max_findings: int = 200) -> list[SecretFinding]:
    findings: list[SecretFinding] = []
    lines = source.splitlines()

    for i, line in enumerate(lines, start=1):
        for kind, pat in PATTERNS:
            m = pat.search(line)
            if m:
                matched = m.group(0)
                redacted = line.replace(matched, _redact_value(matched), 1)
                findings.append(
                    SecretFinding(
                        kind=kind,
                        line=i,
                        name_or_key="(pattern)",
                        excerpt=redacted.strip(),
                    )
                )
                if len(findings) >= max_findings:
                    return findings

        m = ASSIGNMENT_STR_RE.match(line)
        if m:
            name = m.group("name")
            value = m.group("value")
            if _is_probably_secret(name, value):
                findings.append(
                    SecretFinding(
                        kind="Sensitive assignment",
                        line=i,
                        name_or_key=name,
                        excerpt=_redact_line_keep_structure(line, value).strip(),
                    )
                )
                if len(findings) >= max_findings:
                    return findings
            continue

        m = DICT_KV_STR_RE.match(line)
        if m:
            key = m.group("key")
            value = m.group("value")
            if _is_probably_secret(key, value):
                findings.append(
                    SecretFinding(
                        kind="Sensitive dict value",
                        line=i,
                        name_or_key=key,
                        excerpt=_redact_line_keep_structure(line, value).strip(),
                    )
                )
                if len(findings) >= max_findings:
                    return findings

    return findings
