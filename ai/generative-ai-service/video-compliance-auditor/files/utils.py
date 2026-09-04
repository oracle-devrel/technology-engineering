"""Helpers for video encoding, SOP extraction, and response parsing."""
import base64
import json
import re
from typing import Optional

import fitz


# Encode video bytes as an inline base64 data URI for direct LLM input
def encode_video_inline(video_bytes: bytes, mime_type: str) -> dict:
    b64 = base64.b64encode(video_bytes).decode("utf-8")
    return {
        "type": "video_url",
        "video_url": {
            "url": f"data:{mime_type};base64,{b64}",
        },
    }


# Encode a video by URL reference
def encode_video_by_url(video_uri: str, mime_type: str) -> dict:
    return {
        "type": "video_url",
        "video_url": {
            "url": f"data:{mime_type};uri,{video_uri}",
        },
    }


# Map filename extension to a MIME type recognized by the model
def detect_video_mime(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower()
    mapping = {
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mov": "video/quicktime",
        "mkv": "video/x-matroska",
    }
    return mapping.get(ext, "video/mp4")


# Extract text from an uploaded PDF SOP
def extract_pdf_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n\n".join(pages).strip()


# Locate and parse the JSON object in raw model output, tolerating fences or stray text
def parse_json_response(raw: str) -> Optional[dict]:
    if not raw:
        return None

    text = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None

    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None