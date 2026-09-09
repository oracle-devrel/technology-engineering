"""Diff rendering for the Project GitOps confirmation preview."""

from __future__ import annotations

import difflib

from .common import MAX_DIFF_BYTES, decode_text, failure


def render_diff(path: str, base_content: bytes, candidate_content: bytes) -> str:
    """Render the bounded, newline-safe diff returned in a semantic preview."""
    base_text = decode_text(base_content, "INVALID_UTF8", "JSON must be valid UTF-8.")
    candidate_text = decode_text(
        candidate_content, "INVALID_UTF8", "JSON must be valid UTF-8."
    )
    generated_lines = difflib.unified_diff(
        base_text.splitlines(keepends=True), candidate_text.splitlines(keepends=True),
        fromfile=f"a/{path}", tofile=f"b/{path}")
    rendered_lines: list[str] = []
    in_hunk = False
    for line in generated_lines:
        if line.startswith("@@"):
            in_hunk = True
        if in_hunk and line[:1] in (" ", "-", "+") and not line.endswith(("\n", "\r")):
            rendered_lines.append(line + "\n")
            rendered_lines.append("\\ No newline at end of file\n")
        else:
            rendered_lines.append(line)
    diff = "".join(rendered_lines)
    if len(diff.encode("utf-8")) > MAX_DIFF_BYTES:
        failure("DIFF_SIZE_LIMIT", "The manifest diff exceeded its size limit.")
    return diff
