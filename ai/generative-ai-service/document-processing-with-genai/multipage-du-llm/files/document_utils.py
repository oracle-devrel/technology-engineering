"""
Copyright (c) 2026 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Document Processing Utilities
=============================
Shared functions for OCR and LLM-driven page grouping + classification.
Used by both the CLI (classify_multi_document.py) and Streamlit app.
"""

import base64
import json
import re
from io import BytesIO
from typing import List, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from PIL import Image
import oci

from config import COMPARTMENT_ID, DEFAULT_MODEL_ID
from oci_utils import create_chat_request, create_chat_details


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DocumentSegment:
    """Represents a detected document within a bundle"""
    start_page: int
    end_page: int
    category: Optional[str] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    is_sensitive: bool = False
    first_page_text: Optional[str] = None


# Sensitive document categories (for flagging)
SENSITIVE_CATEGORIES = {
    "Bank Details",
    "Passport",
    "Driving License",
    "ID",
    "Birth Certificate",
    "Marriage Certificate",
    "BPSS",
    "Security check responses",
    "Screening report",
    "Health Declaration",
    "Employee medical reports from Occupational Health",
    "Fit Notes",
    "Disclosure Statements",
    "Compromise Agreements",
}


# ============================================================================
# Image Processing Functions
# ============================================================================

def image_to_jpeg_bytes(image: Image.Image, quality: int = 85) -> bytes:
    """Convert PIL Image to JPEG bytes"""
    if image.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[-1])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


def is_blank_page(image: Image.Image, threshold: float = 0.995) -> bool:
    """
    Detect if a page is truly blank or almost blank.
    Uses multiple checks to avoid false positives on emails/letters with lots of whitespace.
    
    Args:
        image: PIL Image to check
        threshold: Minimum white pixel ratio to consider blank (default 0.995 = 99.5% white)
    
    Returns:
        True only if page is truly blank
    """
    gray = np.array(image.convert('L'))
    
    # Check 1: Overall white pixel ratio (very strict - 99.5% white)
    white_ratio = np.sum(gray > 240) / gray.size
    if white_ratio <= threshold:
        return False  # Has enough content to not be blank
    
    # Check 2: Standard deviation - blank pages have very low variance
    # Even a small amount of text creates variation in pixel values
    std_dev = np.std(gray)
    if std_dev > 15:  # Empirically, typed text usually creates std > 20
        return False
    
    # Check 3: Edge detection - real content has edges
    # Simple gradient magnitude check
    grad_x = np.abs(np.diff(gray.astype(np.int16), axis=1))
    grad_y = np.abs(np.diff(gray.astype(np.int16), axis=0))
    edge_intensity = np.mean(grad_x) + np.mean(grad_y)
    if edge_intensity > 3:  # Real documents have more edge content
        return False
    
    return True


# ============================================================================
# OCR Functions
# ============================================================================

def ocr_page(doc_client, image: Image.Image, page_num: int = 0, max_chars: int = 2000) -> str:
    """
    Run OCR on a single page image using OCI Document Understanding.
    
    Args:
        doc_client: OCI Document Understanding client
        image: PIL Image to OCR
        page_num: Page number (for error messages)
        max_chars: Maximum characters to extract
    
    Returns:
        Extracted text as string
    """
    from oci.ai_document.models import (
        AnalyzeDocumentDetails,
        InlineDocumentDetails,
        DocumentTextExtractionFeature,
    )
    
    # Convert image to JPEG bytes
    img_bytes = image_to_jpeg_bytes(image)
    encoded_image = base64.b64encode(img_bytes).decode("utf-8")
    
    inline_doc = InlineDocumentDetails(data=encoded_image, source="INLINE")
    analyze_details = AnalyzeDocumentDetails(
        compartment_id=COMPARTMENT_ID,
        features=[DocumentTextExtractionFeature()],
        document=inline_doc,
        language="en",
    )
    
    try:
        response = doc_client.analyze_document(analyze_details)
        du_dict = oci.util.to_dict(response.data)
        
        # Extract text from all pages
        text_parts = []
        total_chars = 0
        
        for page in du_dict.get("pages", []):
            for line in page.get("lines", []):
                line_text = line.get("text", "").strip()
                if line_text:
                    text_parts.append(line_text)
                    total_chars += len(line_text) + 1
                    if total_chars >= max_chars:
                        break
            if total_chars >= max_chars:
                break
        
        return "\n".join(text_parts)
    
    except Exception as e:
        print(f"  ⚠️ OCR error on page {page_num}: {e}")
        return ""


# ============================================================================
# Classification Functions
# ============================================================================

def fix_invalid_json_escapes(s: str) -> str:
    """
    Fix invalid escape sequences in JSON string.
    Valid JSON escapes: \\", \\\\, \\/, \\b, \\f, \\n, \\r, \\t, \\uXXXX
    """
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            next_char = s[i + 1]
            # Check if it's a valid escape sequence
            if next_char in ('"', '\\', '/', 'b', 'f', 'n', 'r', 't'):
                result.append(s[i:i+2])
                i += 2
            elif next_char == 'u' and i + 5 < len(s):
                # Unicode escape \uXXXX
                result.append(s[i:i+6])
                i += 6
            else:
                # Invalid escape - double the backslash
                result.append('\\\\')
                i += 1
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)


def parse_json_array(response_text: str) -> list:
    """Extract and parse the first JSON array in an LLM response."""
    if response_text.startswith("```"):
        response_text = response_text.strip("`").strip()
        if response_text.lower().startswith("json"):
            response_text = response_text[4:].strip()
    match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if match:
        response_text = match.group()
    return json.loads(fix_invalid_json_escapes(response_text))


def segment_and_classify_pages(
    client,
    compartment_id: str,
    page_texts: List[str],
    categories: List[str],
    max_chars_per_page: int = 600,
    verbose: bool = False,
) -> List[DocumentSegment]:
    """
    Group consecutive pages into documents and classify each one in a single LLM call.

    Visual heuristics cannot tell page 2 of a letter from a new document, so the
    model reads the OCR text of every page and decides where documents start.

    Args:
        client: OCI Generative AI client
        compartment_id: OCI compartment ID
        page_texts: OCR text per page, in order (empty string = blank page)
        categories: List of allowed category names
        max_chars_per_page: Characters of each page sent to the model
        verbose: Print progress

    Returns:
        List of classified DocumentSegment objects (1-indexed page ranges)
    """
    if verbose:
        print("\n🤖 Grouping and classifying pages with Llama 3.3...")

    categories_list = "\n".join(f"- {cat}" for cat in categories)
    pages_text = ""
    for i, text in enumerate(page_texts, start=1):
        preview = text[:max_chars_per_page].strip() if text else "(blank page)"
        pages_text += f"\n--- PAGE {i} ---\n{preview}\n"

    prompt = f"""
You are a document classification expert. A scanned bundle has been OCR'd page by page.
Consecutive pages often belong to the same document (for example page 2 of a letter
continues page 1). First group the pages into documents, then classify each document.

Grouping rules:
- A document is a contiguous page range. Documents never overlap and every non-blank page belongs to exactly one document.
- A page STARTS a new document when it has its own letterhead, title, date, salutation or form header.
- A page CONTINUES the previous document when it carries on a sentence, paragraph, list, table or closing (signature, "Yours sincerely", etc.) without a new heading.
- Pages marked (blank page) are separators and belong to no document.

ALLOWED_CATEGORIES (choose exactly one per document, or "INVALID_CATEGORY" if none fit):
{categories_list}

PAGES:
{pages_text}

OUTPUT FORMAT (JSON array, ordered by start_page):
[
  {{
    "start_page": 1,
    "end_page": 2,
    "category": "Category Name",
    "confidence": "high",
    "confidence_score": 0.95,
    "reasoning": "One sentence, including why these pages were grouped"
  }}
]

Return ONLY the JSON array, no other text.
"""
    chat_request = create_chat_request(prompt=prompt, max_tokens=4000, temperature=0.0)
    chat_detail = create_chat_details(chat_request, model_id=DEFAULT_MODEL_ID, compartment_id=compartment_id)

    try:
        response = client.chat(chat_detail)
        raw = response.data.chat_response.choices[0].message.content[0].text.strip()
        results = parse_json_array(raw)
    except Exception as e:
        print(f"  ❌ Classification error: {e}")
        results = []

    # Validate: keep well-formed, in-order, non-overlapping ranges
    n = len(page_texts)
    segments: List[DocumentSegment] = []
    last_end = 0
    for r in sorted(results, key=lambda r: r.get("start_page", 0)):
        start, end = int(r.get("start_page", 0)), int(r.get("end_page", 0))
        if start <= last_end or start > end or end > n:
            continue
        category = r.get("category", "Unknown")
        segments.append(DocumentSegment(
            start_page=start,
            end_page=end,
            category=category,
            confidence=r.get("confidence", "unknown"),
            confidence_score=float(r.get("confidence_score", 0.0)),
            reasoning=r.get("reasoning", ""),
            is_sensitive=category in SENSITIVE_CATEGORIES,
            first_page_text=page_texts[start - 1],
        ))
        last_end = end

    # Fallback: any non-blank page the model skipped becomes its own unclassified document
    covered = {p for s in segments for p in range(s.start_page, s.end_page + 1)}
    for i, text in enumerate(page_texts, start=1):
        if text and i not in covered:
            segments.append(DocumentSegment(start_page=i, end_page=i, category="Unknown",
                                            confidence="low", confidence_score=0.0,
                                            reasoning="Not grouped by the model", first_page_text=text))
    segments.sort(key=lambda s: s.start_page)
    return segments
