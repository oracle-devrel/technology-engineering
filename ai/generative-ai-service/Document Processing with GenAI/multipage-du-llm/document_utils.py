"""
Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Document Processing Utilities
=============================
Shared functions for document boundary detection, OCR, and classification.
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
import imagehash
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


def compute_image_hash(image: Image.Image, size: int = 64) -> imagehash.ImageHash:
    """Compute perceptual hash for an image"""
    img_gray = image.convert('L').resize((size, size))
    return imagehash.phash(img_gray)


# ============================================================================
# Document Boundary Detection
# ============================================================================

def detect_document_boundaries(
    images: List[Image.Image], 
    hash_threshold: int = 15,
    verbose: bool = False
) -> Tuple[List[Tuple[int, int]], List[int]]:
    """
    Detect document boundaries using visual analysis.
    
    Args:
        images: List of PIL Images (pages)
        hash_threshold: Threshold for visual hash difference to detect boundary
        verbose: Print detection details
    
    Returns:
        Tuple of:
        - List of (start_page, end_page) tuples (1-indexed)
        - List of blank page indices (0-indexed)
    """
    if verbose:
        print("\n🔍 Detecting document boundaries...")
    
    n_pages = len(images)
    boundaries = [0]  # First page is always start of a document
    
    # Compute hashes for all pages
    hashes = []
    blank_pages = []
    
    for i, img in enumerate(images):
        page_num = i + 1
        
        # Check if blank
        if is_blank_page(img):
            blank_pages.append(i)
            hashes.append(None)
            if verbose:
                print(f"  Page {page_num}: BLANK")
        else:
            hashes.append(compute_image_hash(img))
    
    # Find boundaries based on blank pages and hash differences
    for i in range(1, n_pages):
        is_boundary = False
        reason = ""
        
        # Method 1: Previous page was blank (separator)
        if i - 1 in blank_pages and i not in blank_pages:
            is_boundary = True
            reason = "after blank separator"
        
        # Method 2: Large visual difference from previous non-blank page
        elif hashes[i] is not None:
            # Find previous non-blank page
            prev_idx = i - 1
            while prev_idx >= 0 and hashes[prev_idx] is None:
                prev_idx -= 1
            
            if prev_idx >= 0 and hashes[prev_idx] is not None:
                diff = hashes[i] - hashes[prev_idx]
                if diff > hash_threshold:
                    is_boundary = True
                    reason = f"visual change (diff={diff})"
        
        if is_boundary:
            boundaries.append(i)
            if verbose:
                print(f"  Page {i + 1}: NEW DOCUMENT ({reason})")
    
    # Convert boundaries to (start, end) ranges
    segments = []
    for i, start in enumerate(boundaries):
        if i + 1 < len(boundaries):
            end = boundaries[i + 1] - 1
        else:
            end = n_pages - 1
        
        # Skip if this segment is just blank pages
        segment_pages = range(start, end + 1)
        non_blank_count = sum(1 for p in segment_pages if p not in blank_pages)
        
        if non_blank_count > 0:
            segments.append((start + 1, end + 1))  # Convert to 1-indexed
    
    if verbose:
        print(f"\n✓ Found {len(segments)} document segments")
        for i, (start, end) in enumerate(segments):
            print(f"  Document {i + 1}: Pages {start}-{end} ({end - start + 1} pages)")
    
    return segments, blank_pages


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


def batch_classify_documents(
    client,
    compartment_id: str,
    segments: List[DocumentSegment],
    categories: List[str],
    verbose: bool = False
) -> List[DocumentSegment]:
    """
    Classify multiple document segments in a single LLM call.
    
    Args:
        client: OCI Generative AI client
        compartment_id: OCI compartment ID
        segments: List of DocumentSegment objects with first_page_text populated
        categories: List of allowed category names
        verbose: Print progress
    
    Returns:
        Updated segments with classification results
    """
    if verbose:
        print("\n🤖 Classifying documents with Llama 3.3...")
    
    # Build categories list
    categories_list = "\n".join([f"- {cat}" for cat in categories])
    
    # Build documents list for prompt
    docs_text = ""
    for i, seg in enumerate(segments):
        text_preview = seg.first_page_text[:500] if seg.first_page_text else "No text extracted"
        docs_text += f"""
--- DOCUMENT {i + 1} (Pages {seg.start_page}-{seg.end_page}) ---
{text_preview}
"""
    
    prompt = f"""
You are a document classification expert. Analyze the following document excerpts and classify each one.

ALLOWED_CATEGORIES (choose exactly one per document):
{categories_list}

DOCUMENTS TO CLASSIFY:
{docs_text}

For each document, provide:
1. The category (must be from the allowed list, or "INVALID_CATEGORY" if none fit)
2. Confidence level: high, medium, or low
3. Confidence score: 0.0 to 1.0
4. Brief reasoning (one sentence)

OUTPUT FORMAT (JSON array):
[
  {{
    "document": 1,
    "category": "Category Name",
    "confidence": "high",
    "confidence_score": 0.95,
    "reasoning": "Contains employment contract terms and signatures"
  }},
  ...
]

Return ONLY the JSON array, no other text.
"""
    
    # Create and send chat request
    chat_request = create_chat_request(prompt=prompt, max_tokens=4000, temperature=0.0)
    chat_detail = create_chat_details(
        chat_request,
        model_id=DEFAULT_MODEL_ID,
        compartment_id=compartment_id
    )
    
    try:
        response = client.chat(chat_detail)
        response_text = (
            response.data.chat_response.choices[0]
            .message.content[0]
            .text.strip()
        )
        
        # Clean markdown if present
        if response_text.startswith("```"):
            response_text = response_text.strip("`").strip()
            if response_text.lower().startswith("json"):
                response_text = response_text[4:].strip()
        
        # Extract JSON array
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group()
        
        # Fix invalid escape sequences
        response_text = fix_invalid_json_escapes(response_text)
        
        classifications = json.loads(response_text)
        
        # Apply classifications to segments
        for cls in classifications:
            doc_idx = cls.get("document", 0) - 1
            if 0 <= doc_idx < len(segments):
                segments[doc_idx].category = cls.get("category", "Unknown")
                segments[doc_idx].confidence = cls.get("confidence", "unknown")
                segments[doc_idx].confidence_score = cls.get("confidence_score", 0.0)
                segments[doc_idx].reasoning = cls.get("reasoning", "")
                
                # Flag sensitive documents
                if segments[doc_idx].category in SENSITIVE_CATEGORIES:
                    segments[doc_idx].is_sensitive = True
        
        return segments
    
    except Exception as e:
        print(f"  ❌ Classification error: {e}")
        # Return segments with "Unknown" classification
        for seg in segments:
            seg.category = "Unknown"
            seg.confidence = "low"
        return segments
