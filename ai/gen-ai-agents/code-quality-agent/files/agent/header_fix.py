"""
File name: header_fix.py
Author: L. Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Generate compliant header docstrings for files that fail header checks.
    Outputs patch text (unified diff) to apply externally (repo is read-only).
"""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path
from typing import Any

from agent.docgen_utils import call_llm_normalized
from agent.utils import get_console_logger
from agent.header_rules import REQUIRED_KEYS, HEADER_TEMPLATE
from agent.config import PYTHON_VERSION

#
# The template for the Header is in agent/header_rules.py
#

REQUIRED_HEADER_FIELDS = REQUIRED_KEYS

DESC_GEN_PROMPT = """
You are a senior Python engineer.

Task: write 1-3 short bullet points describing what this Python module does.
Return ONLY the bullet points (each starting with "- ").
Do NOT include secrets or PII. Do NOT quote code. Use generic wording.

Module path: {relpath}

Module structure:
- Classes: {classes}
- Functions: {functions}
- Imports: {imports}
"""


logger = get_console_logger()


def _format_description_block(lines: list[str]) -> str:
    """
    Indent description lines consistently and keep them short.
    """
    cleaned = [ln.strip() for ln in lines if ln.strip()]
    if not cleaned:
        cleaned = ["- Module description unavailable."]

    # Enforce max 3 lines (your policy)
    cleaned = cleaned[:3]

    # Enforce bullet formatting
    bullets = []
    for ln in cleaned:
        if not ln.startswith("-"):
            ln = "- " + ln
        bullets.append(ln)

    # 4-space indentation for block
    return "\n".join("    " + b for b in bullets)


def _render_header(
    *,
    relpath: Path,
    author: str,
    today: str,
    pyver: str,
    license_hint: str,
    description_lines: list[str],
) -> str:
    lic = license_hint if license_hint and license_hint != "Unknown" else "Unknown"
    return (
        HEADER_TEMPLATE.format(
            file_name=relpath.name,
            author=author or "Unknown",
            date_last_modified=today,
            python_version=pyver,
            license=lic,
            description_block=_format_description_block(description_lines),
        ).strip()
        + "\n"
    )


def _extract_structure(source: str) -> dict[str, list[str]]:
    try:
        mod = ast.parse(source)
    except SyntaxError:
        return {"classes": [], "functions": [], "imports": []}

    classes = [n.name for n in mod.body if isinstance(n, ast.ClassDef)]
    funcs = [n.name for n in mod.body if isinstance(n, ast.FunctionDef)]

    imports: list[str] = []
    for n in mod.body:
        if isinstance(n, ast.Import):
            imports.extend(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.append(n.module)

    # keep it short
    return {
        "classes": classes[:10],
        "functions": funcs[:10],
        "imports": imports[:10],
    }


async def generate_header_snippet(
    *,
    llm: Any,
    relpath: Path,
    source: str,
    author: str = "Unknown",
    license_hint: str = "Unknown",
    pyver: str = PYTHON_VERSION,
) -> str:
    """
    Returns ONLY the header docstring text (with trailing newline).
    """
    today = date.today().isoformat()

    # Default description (deterministic) if LLM fails
    struct = _extract_structure(source)
    fallback_desc = []

    if struct["classes"]:
        fallback_desc.append(f"Defines classes: {', '.join(struct['classes'][:5])}.")
    if struct["functions"]:
        fallback_desc.append(
            f"Defines functions: {', '.join(struct['functions'][:5])}."
        )
    if not fallback_desc:
        fallback_desc.append("Provides supporting utilities for this project.")

    # LLM-generated description (optional, safer: only structure is sent)
    description_lines: list[str] = fallback_desc

    try:
        prompt = DESC_GEN_PROMPT.format(
            relpath=str(relpath).replace("\\", "/"),
            classes=", ".join(struct["classes"]) or "None",
            functions=", ".join(struct["functions"]) or "None",
            imports=", ".join(struct["imports"]) or "None",
        )
        text, _ = await call_llm_normalized(llm, prompt)

        # Parse bullet lines
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        # Keep only bullets / normalize
        bullets = []
        for ln in lines:
            if not ln.startswith("-"):
                ln = "- " + ln.lstrip("- ").strip()
            bullets.append(ln)

        if bullets:
            description_lines = bullets[:3]

    except Exception as e:
        logger.warning("LLM description generation failed for %s: %s", relpath, e)

    # Render header using the fixed template
    return _render_header(
        relpath=relpath,
        author=author or "Unknown",
        today=today,
        pyver=pyver,
        license_hint=license_hint or "Unknown",
        description_lines=description_lines,
    )
