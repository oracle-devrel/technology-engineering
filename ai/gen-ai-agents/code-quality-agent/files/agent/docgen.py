"""
File name: docgen.py
Author: Luigi Saetta
Date last modified: 2026-01-12
Python Version: 3.11

Description:
    Per-file documentation generation using an LLM. Output is written elsewhere.

    - Accepts the Python source as text (read-only input).
    - Produces a Markdown document in an output folder (no in-place edits).
    - Designed to work with an LLM returned by oci.models.get_llm().

    Supported LLM call styles (best-effort):
    - await llm.ainvoke(prompt) -> str or object with .content
    - await llm(prompt) -> str or object with .content

Usage:
    from pathlib import Path
    from oci.models import get_llm
    from agent.docgen import generate_doc_for_file

    llm = get_llm()
    await generate_doc_for_file(
        llm=llm,
        relpath=Path("pkg/module.py"),
        source=python_source_text,
        out_dir=Path("./out_docs"),
        request="Focus on public API and side effects."
    )

License:
    MIT
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import re


from agent.docgen_prompt import DOC_PROMPT
from agent.docgen_utils import call_llm_normalized
from agent.utils import get_console_logger

logger = get_console_logger()

# ----------------------------
# Public API
# ----------------------------


@dataclass(frozen=True)
class DocGenResult:
    out_path: Path
    bytes_written: int
    model_hint: str | None = None


def ensure_dir(p: Path) -> None:
    """Create directory if needed."""
    p.mkdir(parents=True, exist_ok=True)


def safe_doc_filename(relpath: Path) -> str:
    """
    Convert "a/b/c.py" -> "a__b__c.py.md" (safe single-file output namespace).
    """
    return "__".join(relpath.parts) + ".md"


async def generate_doc_for_file(
    *,
    llm: Any,
    relpath: Path,
    source: str,
    out_dir: Path,
    request: str = "",
    prompt_template: str = DOC_PROMPT,
    max_source_chars: int = 120_000,
) -> DocGenResult:
    """
    Generate Markdown documentation for a single Python file.

    Args:
        llm: LLM object (expected to support .ainvoke(prompt) or be awaitable).
        relpath: Path relative to the scanned root (used only for labeling/output naming).
        source: Python source code text.
        out_dir: Output directory (docs will be written here).
        request: User request/goal for the documentation (e.g., "focus on security and public API").
        prompt_template: Prompt template string with {relpath}, {source}, and {request}.
        max_source_chars: Safety limit to avoid sending huge files to the LLM.

    Returns:
        DocGenResult with the output path and bytes written.

    Raises:
        ValueError: if source is empty or too large.
        RuntimeError: if LLM call fails or returns empty content.
    """
    if not source or not source.strip():
        raise ValueError(f"Empty source for {relpath}")

    # Light guardrail to avoid huge prompts; adjust as needed.
    if len(source) > max_source_chars:
        source = _truncate_source(source, max_source_chars)

    ensure_dir(out_dir)

    prompt = prompt_template.format(
        relpath=str(relpath),
        source=source,
        request=(request or "").strip(),
    )

    text, model_hint = await call_llm_normalized(llm, prompt)
    text = _postprocess_markdown(text, relpath)

    if not text.strip():
        raise RuntimeError("LLM returned empty documentation content.")

    out_path = out_dir / safe_doc_filename(relpath)
    data = (text.rstrip() + "\n").encode("utf-8")
    out_path.write_bytes(data)

    return DocGenResult(
        out_path=out_path,
        bytes_written=len(data),
        model_hint=model_hint,
    )


# ----------------------------
# Internals
# ----------------------------


def _truncate_source(source: str, max_chars: int) -> str:
    """
    Truncate source while keeping head + tail to preserve context.
    """
    head = source[: int(max_chars * 0.65)]
    tail = source[-int(max_chars * 0.25) :]
    note = (
        "\n\n# --- TRUNCATED ---\n"
        "# The source file was truncated before being sent to the LLM.\n"
        "# Consider generating docs per-section if you need full coverage.\n"
        "# --- TRUNCATED ---\n\n"
    )
    return head + note + tail


def _postprocess_markdown(text: str, relpath: Path) -> str:
    """
    Minimal cleanup:
    - Ensure it starts with a title
    - Remove stray triple backticks at edges (common formatting glitches)
    """
    t = text.strip()

    # If model returns a fenced block only, unwrap once.
    t = _unwrap_single_fence(t)

    # Ensure title
    if not re.match(r"^\s*#\s+", t):
        t = f"# {relpath}\n\n" + t

    return t


def _unwrap_single_fence(t: str) -> str:
    """If the whole content is wrapped in a single ```...``` fence, unwrap it."""
    if t.startswith("```") and t.endswith("```"):
        lines = t.splitlines()
        if (
            len(lines) >= 3
            and lines[0].startswith("```")
            and lines[-1].startswith("```")
        ):
            return "\n".join(lines[1:-1]).strip()
    return t
