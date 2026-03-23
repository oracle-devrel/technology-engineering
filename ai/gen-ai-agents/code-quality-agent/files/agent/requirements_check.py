"""
File name: requirements_check.py
Author: L.  Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Checks whether requirements.txt exists at repo root.
    Optionally captures a short preview for reporting (no secrets/PII).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RequirementsCheckResult:
    ok: bool
    relpath: str | None
    message: str
    preview: str = ""


def check_requirements_at_root(*, repo_root: Path, fs) -> RequirementsCheckResult:
    """
    repo_root: absolute Path of repository root
    fs: ReadOnlySandboxFS

    Returns:
      ok=True if requirements.txt exists at root.
      ok=False otherwise (strong warning).
    """
    req_name = "requirements.txt"

    # use sandbox read to ensure we're under root
    try:
        text = fs.read_text(req_name)
        # short preview (first ~30 non-empty lines), for reporting only
        lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
        preview = "\n".join(lines[:30])
        return RequirementsCheckResult(
            ok=True,
            relpath=req_name,
            message="requirements.txt found at repository root.",
            preview=preview,
        )
    except FileNotFoundError:
        return RequirementsCheckResult(
            ok=False,
            relpath=None,
            message=(
                "⚠️ STRONG WARNING: requirements.txt NOT found at repository root. "
                "Dependency license/compliance checks may be incomplete or impossible."
            ),
            preview="",
        )
    except Exception as e:
        return RequirementsCheckResult(
            ok=False,
            relpath=None,
            message=(
                "⚠️ STRONG WARNING: requirements.txt check failed. "
                f"Could not read repository root requirements.txt: {e}"
            ),
            preview="",
        )
