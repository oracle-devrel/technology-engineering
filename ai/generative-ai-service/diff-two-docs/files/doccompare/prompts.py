"""Prompts and JSON schemas for the Qwen 3.x VLM on OCI.

Style rule learned the hard way: the Qwen 3 chat template runs a hidden
reasoning phase before answering. Imperative multi-step framing ("your job is BOTH…"),
words like "carefully" / "step-by-step", and long rule lists inflate that phase
and can exhaust max_tokens with empty content. So: declarative, terse, one
task per call, schema-constrained output.
"""
from __future__ import annotations

# --------------------------------------------------------------- OCR tiles --
FRAME_DESC = {
    "norm1000": "integers 0-1000 relative to the image width and height",
    "pixel": "pixel coordinates of this image",
}

OCR_TILE_PROMPT = """\
Image: one crop of a document page, {w}x{h} pixels.
Output JSON: {{"lines": [{{"text": "<exact characters>", "bbox": [x0, y0, x1, y1]}}]}}
- one entry per text line, reading order, tight box around the line
- bbox frame: {frame_desc}, origin top-left
- characters exactly as printed: keep digits, units, symbols, diacritics; no spelling fixes
- a line cut by the image edge: transcribe the visible part only
- no text: {{"lines": []}}
Return only the JSON."""

OCR_SCHEMA = {
    "type": "object",
    "properties": {
        "lines": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "bbox": {"type": "array", "items": {"type": "number"},
                             "minItems": 4, "maxItems": 4},
                },
                "required": ["text", "bbox"],
            },
        }
    },
    "required": ["lines"],
}

# ----------------------------------------------------------------- verify --
CHANGE_TYPES = [
    "text_edit", "number_change", "addition", "deletion",
    "stamp_or_signature", "handwriting", "layout_only", "none",
]

VERIFY_PROMPT = """\
Two crops of the same region from two versions of one document. Image 1 = OLD version. Image 2 = NEW version.
Automated diff hint, kind={kind}: old="{old_hint}"; new="{new_hint}". The hint comes from OCR and is often wrong on scans; the images are the evidence.
Output JSON:
{{
  "changed": <true|false>,
  "change_type": "<text_edit|number_change|addition|deletion|stamp_or_signature|handwriting|layout_only|none>",
  "old_text": "<exact text in OLD that differs, else empty>",
  "new_text": "<exact text in NEW that differs, else empty>",
  "row_label": "<if the change sits in a table row: the row's name or item label, never a bare row number; else empty>",
  "column_header": "<column header if the change sits in a table column, else empty>",
  "description": "<one factual sentence>",
  "confidence": "<high|medium|low>"
}}
changed=false when both crops carry the same content; scan noise, resolution, blur or a small shift are not changes.
layout_only: same characters, different position or spacing.
Return only the JSON."""

# Hint-free variant: a second opinion for text changes on scanned pages, so an
# OCR misread in the hint cannot talk the model into a change that is not there.
VERIFY_PROMPT_BLIND = VERIFY_PROMPT.replace(
    'Automated diff hint, kind={kind}: old="{old_hint}"; new="{new_hint}". The hint comes from OCR and is often wrong on scans; the images are the evidence.\n',
    "Compare character by character.\n")

VERIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "changed": {"type": "boolean"},
        "change_type": {"type": "string", "enum": CHANGE_TYPES},
        "old_text": {"type": "string"},
        "new_text": {"type": "string"},
        "row_label": {"type": "string"},
        "column_header": {"type": "string"},
        "description": {"type": "string"},
        "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
    },
    "required": ["changed", "change_type", "old_text", "new_text", "confidence"],
}
