"""
File name: pii_scan.py
Author: Luigi Saetta
Date last modified: 2026-01-08
Python Version: 3.11

License:
    MIT

Description:
    Deterministic PII scanner.

    Policy:
    - HARD FAIL: direct identifiers (email, phone, IBAN, credit card, IT tax id)
    - WARN: structured names/addresses (heuristic, conservative)

    All excerpts are masked to avoid leaking PII in logs/artifacts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ----------------------------
# Findings
# ----------------------------


@dataclass(frozen=True)
class PiiFinding:
    kind: str  # email | phone | iban | credit_card | tax_id_it | name_structured | address_structured
    severity: str  # "fail" | "warn"
    line: int  # 1-based
    excerpt: str  # masked snippet
    confidence: str = "medium"  # low | medium | high


# ----------------------------
# Helpers
# ----------------------------

_EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)

# phone is tricky; keep it conservative but useful
_PHONE_RE = re.compile(
    r"""
    (?<!\w)
    (?:\+?\d{1,3}[\s\-\.]?)?          # optional country code
    (?:\(?\d{2,4}\)?[\s\-\.]?)?       # optional area code
    \d{3,4}[\s\-\.]?\d{3,4}           # local number blocks
    (?!\w)
    """,
    re.VERBOSE,
)

# IBAN: country + 2 digits + up to 30 alnum
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b", re.IGNORECASE)

# Credit card candidates: 13-19 digits with separators
_CC_CANDIDATE_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")

# Italian Codice Fiscale (16 chars)
# This regex is a common approximation; not full validation.
_CF_RE = re.compile(r"\b[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]\b", re.IGNORECASE)

# Structured "Name: John Doe" etc. (conservative)
_STRUCT_NAME_RE = re.compile(
    r"\b(?:name|full\s*name|first\s*name|last\s*name)\s*[:=]\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b"
)

# Structured "Address: ..." (conservative)
_STRUCT_ADDR_RE = re.compile(
    r"\b(?:address|street|via|viale|piazza|road|rd\.?|st\.?|avenue|ave\.?)\s*[:=]\s*.+\b",
    re.IGNORECASE,
)

# Common "clearly fake" hints to reduce noisy false positives
_FAKE_HINTS = (
    "example.com",
    "test@example",
    "dummy",
    "lorem",
    "sample",
    "example",
    "xxx",
    "0000",
    "1111",
    "555-0100",
    "5550100",
)


def _mask_email(s: str) -> str:
    def repl(m: re.Match) -> str:
        val = m.group(0)
        parts = val.split("@", 1)
        user = parts[0]
        dom = parts[1]
        user_mask = (user[:2] + "***") if len(user) > 2 else "***"
        dom_parts = dom.split(".")
        dom_mask = "***." + dom_parts[-1] if len(dom_parts) >= 2 else "***"
        return f"{user_mask}@{dom_mask}"

    return _EMAIL_RE.sub(repl, s)


def _mask_digits(s: str) -> str:
    # Keep last 2 digits only
    digits = re.sub(r"\D", "", s)
    if len(digits) <= 2:
        return "***"
    return "***" + digits[-2:]


def _mask_iban(s: str) -> str:
    # Keep country + last 2 chars
    s2 = re.sub(r"\s+", "", s)
    if len(s2) < 6:
        return "IBAN:***"
    return s2[:2].upper() + "**" + "***" + s2[-2:]


def _mask_taxid(s: str) -> str:
    s2 = s.strip()
    if len(s2) < 4:
        return "***"
    return s2[:2].upper() + "***" + s2[-2:].upper()


def _mask_excerpt(kind: str, excerpt: str) -> str:
    if kind == "email":
        return _mask_email(excerpt)
    if kind == "iban":
        return _mask_iban(excerpt)
    if kind == "tax_id_it":
        return _mask_taxid(excerpt)
    if kind in ("credit_card", "phone"):
        return _mask_digits(excerpt)
    # For warn kinds, keep as-is but truncate
    return excerpt[:120]


def _looks_fake(line: str) -> bool:
    line = line.lower()
    return any(h in line for h in _FAKE_HINTS)


def _luhn_ok(number: str) -> bool:
    digits = [int(ch) for ch in number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


# ----------------------------
# Public API
# ----------------------------


def scan_for_pii(text: str) -> list[PiiFinding]:
    """
    Returns a list of masked findings.
    Deterministic, line-based.
    """
    findings: list[PiiFinding] = []
    lines = text.splitlines()

    for idx, line in enumerate(lines, start=1):
        # Skip super-noisy lines that are clearly placeholders
        fake = _looks_fake(line)

        # ---- HARD FAIL: email ----
        for m in _EMAIL_RE.finditer(line):
            if fake:
                continue
            raw = m.group(0)
            findings.append(
                PiiFinding(
                    kind="email",
                    severity="fail",
                    line=idx,
                    excerpt=_mask_excerpt("email", raw),
                    confidence="high",
                )
            )

        # ---- HARD FAIL: IBAN ----
        for m in _IBAN_RE.finditer(line.replace(" ", "")):
            if fake:
                continue
            raw = m.group(0)
            findings.append(
                PiiFinding(
                    kind="iban",
                    severity="fail",
                    line=idx,
                    excerpt=_mask_excerpt("iban", raw),
                    confidence="high",
                )
            )

        # ---- HARD FAIL: IT tax id (codice fiscale) ----
        for m in _CF_RE.finditer(line):
            if fake:
                continue
            raw = m.group(0)
            findings.append(
                PiiFinding(
                    kind="tax_id_it",
                    severity="fail",
                    line=idx,
                    excerpt=_mask_excerpt("tax_id_it", raw),
                    confidence="medium",
                )
            )

        # ---- HARD FAIL: credit card (candidate + Luhn) ----
        for m in _CC_CANDIDATE_RE.finditer(line):
            if fake:
                continue
            raw = m.group(0)
            if _luhn_ok(raw):
                findings.append(
                    PiiFinding(
                        kind="credit_card",
                        severity="fail",
                        line=idx,
                        excerpt=_mask_excerpt("credit_card", raw),
                        confidence="high",
                    )
                )

        # ---- HARD FAIL: phone (conservative) ----
        # To avoid too many false positives, require >= 9 digits total
        for m in _PHONE_RE.finditer(line):
            raw = m.group(0)
            digits = re.sub(r"\D", "", raw)
            if len(digits) < 9:
                continue
            if fake:
                continue
            findings.append(
                PiiFinding(
                    kind="phone",
                    severity="fail",
                    line=idx,
                    excerpt=_mask_excerpt("phone", raw),
                    confidence="medium",
                )
            )

        # ---- WARN: structured names / addresses ----
        # Conservative: only if explicitly structured with a label.
        if _STRUCT_NAME_RE.search(line):
            findings.append(
                PiiFinding(
                    kind="name_structured",
                    severity="warn",
                    line=idx,
                    excerpt=_mask_excerpt("name_structured", line.strip()),
                    confidence="low",
                )
            )
        if _STRUCT_ADDR_RE.search(line):
            # Avoid flagging generic config lines like "address = localhost"
            if not re.search(
                r"\blocalhost\b|\b127\.0\.0\.1\b", line, flags=re.IGNORECASE
            ):
                findings.append(
                    PiiFinding(
                        kind="address_structured",
                        severity="warn",
                        line=idx,
                        excerpt=_mask_excerpt("address_structured", line.strip()),
                        confidence="low",
                    )
                )

    # Deduplicate same kind+line+excerpt to reduce noise
    uniq: dict[tuple[str, int, str, str], PiiFinding] = {}
    for f in findings:
        key = (f.kind, f.line, f.excerpt, f.severity)
        uniq[key] = f
    return list(uniq.values())
