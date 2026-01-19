"""
Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Single Document Classifier (Command Line)
==========================================
Classifies a single document using OCI Document Understanding + Llama 3.3.
Command-line equivalent of the Streamlit app.

Usage:
    python classify_single_document.py document.pdf
    python classify_single_document.py document.jpg -o results/
"""

import os
import sys
import json
import base64
import argparse
from datetime import datetime
from io import BytesIO
from typing import Dict, Tuple

from PIL import Image
from pdf2image import convert_from_path
import oci

# Import from centralized modules
from config import (
    COMPARTMENT_ID,
    DEFAULT_MODEL_ID,
    OUTPUT_DIR,
)
from oci_utils import (
    init_generative_ai_client,
    init_document_client,
    load_categories,
    create_chat_request,
    create_chat_details,
)


def image_to_jpeg_bytes(image: Image.Image, quality: int = 90) -> bytes:
    """Convert PIL Image to JPEG bytes"""
    if image.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", image.size, (255, 255, 255))
        bg.paste(image, mask=image.split()[-1])
        image = bg
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    buf = BytesIO()
    image.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def load_document_as_image(file_path: str) -> Image.Image:
    """
    Load a document (PDF or image) and return the first page as PIL Image.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        print("📄 Converting PDF first page to image...")
        pages = convert_from_path(file_path, dpi=200, first_page=1, last_page=1)
        if not pages:
            raise ValueError("No pages found in PDF")
        return pages[0]
    else:
        print("🖼️ Loading image...")
        return Image.open(file_path)


def extract_text_from_ocr(du_dict: dict, max_chars: int = 3000) -> str:
    """
    Extract plain text from OCR result.
    """
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


def run_ocr(doc_client, image: Image.Image) -> Tuple[dict, str]:
    """
    Run OCR on the image using OCI Document Understanding.
    Returns (raw_ocr_dict, extracted_text).
    """
    from oci.ai_document.models import (
        AnalyzeDocumentDetails,
        InlineDocumentDetails,
        DocumentTextExtractionFeature,
    )
    
    print("🔤 Running OCR...")
    img_bytes = image_to_jpeg_bytes(image)
    encoded_image = base64.b64encode(img_bytes).decode("utf-8")
    
    inline_doc = InlineDocumentDetails(data=encoded_image, source="INLINE")
    analyze_details = AnalyzeDocumentDetails(
        compartment_id=COMPARTMENT_ID,
        features=[DocumentTextExtractionFeature()],
        document=inline_doc,
        language="en",
    )
    
    response = doc_client.analyze_document(analyze_details)
    du_dict = oci.util.to_dict(response.data)
    
    text = extract_text_from_ocr(du_dict, max_chars=3000)
    print(f"✓ Extracted {len(text)} characters of text")
    
    return du_dict, text


def classify_document(gen_client, compartment_id: str, document_text: str, categories: list) -> dict:
    """
    Classify document using Llama 3.3.
    """
    print("🤖 Classifying with Llama 3.3...")
    
    categories_list = "\n".join([f"- {cat}" for cat in categories])
    
    prompt = f"""You are an expert document classifier for HR and Finance documents.

Classify this document into ONE category from the list below.

ALLOWED CATEGORIES:
{categories_list}

DOCUMENT TEXT:
{document_text}

Return ONLY a JSON object with this structure:
{{
  "primary_category": "Category Name",
  "confidence": "high|medium|low",
  "confidence_score": 0.0-1.0,
  "reasoning": "Brief explanation",
  "alternative_categories": [
    {{"category": "Alt Category", "probability": 0.0-1.0, "reasoning": "Why"}}
  ]
}}
"""
    
    chat_request = create_chat_request(prompt=prompt, max_tokens=2000, temperature=0.0)
    chat_detail = create_chat_details(chat_request, model_id=DEFAULT_MODEL_ID, compartment_id=compartment_id)
    
    response = gen_client.chat(chat_detail)
    response_text = (
        response.data.chat_response.choices[0]
        .message.content[0]
        .text.strip()
    )
    
    # Clean markdown fences
    if response_text.startswith("```"):
        response_text = response_text.strip("`").strip()
        if response_text.lower().startswith("json"):
            response_text = response_text[4:].strip()
    
    # Parse JSON
    import re
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        response_text = json_match.group()
    
    return json.loads(response_text)


def classify_single_document(file_path: str, output_dir: str = OUTPUT_DIR) -> dict:
    """
    Main function to classify a single document.
    """
    start_time = datetime.now()
    filename = os.path.basename(file_path)
    
    print("=" * 60)
    print("Single Document Classifier")
    print(f"File: {filename}")
    print("=" * 60)
    
    # Load document
    image = load_document_as_image(file_path)
    
    # Initialize clients
    doc_client = init_document_client()
    gen_client, compartment_id = init_generative_ai_client()
    
    # Run OCR
    ocr_dict, document_text = run_ocr(doc_client, image)
    
    # Classify
    categories = load_categories()
    result = classify_document(gen_client, compartment_id, document_text, categories)
    
    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Print results
    print("\n" + "=" * 60)
    print("CLASSIFICATION RESULT")
    print("=" * 60)
    print(f"Category: {result.get('primary_category', 'Unknown')}")
    print(f"Confidence: {result.get('confidence', 'unknown')} ({result.get('confidence_score', 0):.0%})")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    
    alternatives = result.get("alternative_categories", [])
    if alternatives:
        print("\nAlternatives:")
        for alt in alternatives[:3]:
            print(f"  - {alt.get('category')}: {alt.get('probability', 0):.0%}")
    
    print(f"\nProcessing time: {processing_time:.1f} seconds")
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{os.path.splitext(filename)[0]}_classification.json"
    output_path = os.path.join(output_dir, output_filename)
    
    full_result = {
        "filename": filename,
        "classification": result,
        "processing_time_seconds": round(processing_time, 2),
        "model_used": "Meta Llama 3.3 70B Instruct",
        "text_extracted_chars": len(document_text)
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(full_result, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    print("=" * 60)
    
    return full_result


def main():
    parser = argparse.ArgumentParser(
        description="Classify a single document using OCR + Llama 3.3"
    )
    parser.add_argument(
        "file_path",
        help="Path to the document (PDF, JPG, PNG)"
    )
    parser.add_argument(
        "-o", "--output",
        default=OUTPUT_DIR,
        help=f"Output directory for results (default: {OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"❌ Error: File not found: {args.file_path}")
        sys.exit(1)
    
    classify_single_document(args.file_path, args.output)


if __name__ == "__main__":
    main()
