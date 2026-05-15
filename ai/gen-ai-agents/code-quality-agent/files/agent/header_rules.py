"""
File name: header_rules.py
Author: Luigi Saetta
Date last modified: 2025-12-16
Python Version: 3.11

License:
    MIT

Description:
    Header template rules and a checker for Python source files.
"""

from __future__ import annotations

from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
import re


# Simple, practical header requirements:
# - Must contain these keys in the first N lines
REQUIRED_KEYS = [
    "File name:",
    "Author:",
    "Date last modified:",
    "Python Version:",
    "Description:",
    "License:",
]

HEADER_TEMPLATE = '''"""
File name: {file_name}
Author: {author}
Date last modified: {date_last_modified}
Python Version: {python_version}
License: {license}

Description:
{description_block}
"""
'''

DATE_RE = re.compile(r"^Date last modified:\s*(.+)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class HeaderCheckResult:
    ok: bool
    missing_keys: list[str]
    message: str
    date_mismatch: bool = False


def check_header(
    source: str, *, path: Path | None = None, top_lines: int = 40
) -> HeaderCheckResult:
    head = "\n".join(source.splitlines()[:top_lines])
    missing = [k for k in REQUIRED_KEYS if k not in head]

    if missing:
        return HeaderCheckResult(
            ok=False,
            missing_keys=missing,
            message=f"Missing header keys in first {top_lines} lines: {missing}",
        )

    # Description sanity check
    m = re.search(r"Description:\s*(.+)", head)
    if not m or not m.group(1).strip():
        return HeaderCheckResult(
            ok=False,
            missing_keys=[],
            message="Description field is present but empty.",
        )

    # Date alignment check (only if we got a path)
    if path is not None:
        hm = DATE_RE.search(head)
        if not hm:
            return HeaderCheckResult(
                ok=False,
                missing_keys=["Date last modified:"],
                message="Date last modified field not found or not parseable.",
            )

        header_date_raw = hm.group(1).strip()

        # Accept either 'YYYY-MM-DD' or full ISO datetime; normalize to date
        try:
            if (
                len(header_date_raw) >= 10
                and header_date_raw[4] == "-"
                and header_date_raw[7] == "-"
            ):
                header_day = header_date_raw[:10]  # YYYY-MM-DD
            else:
                raise ValueError("Unsupported date format")
        except Exception:
            return HeaderCheckResult(
                ok=False,
                missing_keys=[],
                message=f"Date last modified is not in YYYY-MM-DD (or ISO starting with it): {header_date_raw}",
            )

        file_day = (
            datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            .date()
            .isoformat()
        )

        if header_day != file_day:
            return HeaderCheckResult(
                ok=False,
                missing_keys=[],
                message=f"Date last modified mismatch: header={header_day}, file_mtime_utc={file_day}",
                date_mismatch=True,
            )

    return HeaderCheckResult(ok=True, missing_keys=[], message="Header looks OK.")
