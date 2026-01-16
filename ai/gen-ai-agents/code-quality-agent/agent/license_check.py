"""
File name: license_check.py
Author: Luigi Saetta
Date last modified: 2025-12-15
Python Version: 3.11

License:
    MIT

Description:
    Checks that a license file is present and (best-effort) identifies its type,
    then validates it against an allow-list.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional


@dataclass(frozen=True)
class LicenseCheckResult:
    ok: bool
    found_file: str | None
    detected_type: str | None
    message: str


# Common license file names seen in repos
DEFAULT_LICENSE_FILENAMES = (
    "LICENSE",
    "LICENSE.txt",
    "LICENSE.md",
    "COPYING",
    "COPYING.txt",
    "NOTICE",
    "NOTICE.txt",
)


# Very lightweight heuristics (not perfect, but good enough for policy checks)
_LICENSE_PATTERNS: list[tuple[str, str]] = [
    ("MIT", r"\bMIT License\b"),
    ("Apache-2.0", r"\bApache License\b.*\bVersion 2\.0\b"),

    # Universal Permissive License (UPL) v1.0
    ("UPL-1.0", r"\bThe\s+Universal\s+Permissive\s+License\s*\(UPL\)\s*,?\s*Version\s*1\.0\b"),

    (
        "BSD-3-Clause",
        r"\bRedistribution and use in source and binary forms\b.*\bNeither the name\b",
    ),
    ("GPL-3.0", r"\bGNU GENERAL PUBLIC LICENSE\b.*\bVersion 3\b"),
    ("GPL-2.0", r"\bGNU GENERAL PUBLIC LICENSE\b.*\bVersion 2\b"),
]


def _detect_license_type(text: str) -> Optional[str]:
    t = text[:20000]  # cap for speed
    for lic, pat in _LICENSE_PATTERNS:
        if re.search(pat, t, flags=re.IGNORECASE | re.DOTALL):
            return lic
    return None


def check_license(
    *,
    list_files: callable,
    read_text: callable,
    accepted_types: Iterable[str],
    filenames: Iterable[str] = DEFAULT_LICENSE_FILENAMES,
) -> LicenseCheckResult:
    """
    list_files(): () -> list[str]          # repo-relative paths
    read_text(relpath): -> str             # file content
    accepted_types: allow-list of license identifiers
    filenames: license file name candidates
    """
    accepted = set(accepted_types)

    # Normalize to posix-style strings
    repo_files = [str(p) for p in list_files()]

    # Prefer top-level matches first
    candidates: list[str] = []

    for fn in filenames:
        # Exact top-level
        if fn in repo_files:
            candidates.append(fn)

    if not candidates:
        # Any depth (e.g., docs/LICENSE)
        for rf in repo_files:
            base = rf.rsplit("/", 1)[-1]
            if base in set(filenames):
                candidates.append(rf)

    if not candidates:
        return LicenseCheckResult(
            ok=False,
            found_file=None,
            detected_type=None,
            message="No license file found (expected one of: "
            + ", ".join(filenames)
            + ").",
        )

    chosen = candidates[0]
    try:
        content = read_text(chosen)
    except Exception as e:
        return LicenseCheckResult(
            ok=False,
            found_file=chosen,
            detected_type=None,
            message=f"License file found at '{chosen}' but cannot be read: {e}",
        )

    detected = _detect_license_type(content)

    if detected is None:
        # If you want: treat as failure (strict) or warning (lenient)
        return LicenseCheckResult(
            ok=False,
            found_file=chosen,
            detected_type=None,
            message=f"License file '{chosen}' found, but license type could not be identified.",
        )

    if detected not in accepted:
        return LicenseCheckResult(
            ok=False,
            found_file=chosen,
            detected_type=detected,
            message=f"License type '{detected}' detected in '{chosen}', but it is not in the accepted list: {sorted(accepted)}",
        )

    return LicenseCheckResult(
        ok=True,
        found_file=chosen,
        detected_type=detected,
        message=f"License OK: '{detected}' found in '{chosen}'.",
    )
