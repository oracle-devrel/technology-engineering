"""
Copyright (c) 2026 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Multi-Document Bundle Classifier
================================
Processes large PDF files (e.g., 70 pages) containing multiple scanned documents.
OCR runs per page; a single LLM call then groups pages into documents and classifies them.

Strategy:
1. Convert PDF to images
2. OCR every non-blank page with Document Understanding
3. One LLM call groups consecutive pages into documents and classifies each
4. Generate report with page ranges and categories
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List
from dataclasses import dataclass

from PIL import Image
from pdf2image import convert_from_path

# Import from centralized modules
from config import (
    COMPARTMENT_ID,
    OUTPUT_DIR,
)
from oci_utils import (
    init_generative_ai_client,
    init_document_client,
    load_categories,
)
from document_utils import (
    DocumentSegment,
    SENSITIVE_CATEGORIES,
    is_blank_page,
    ocr_page,
    segment_and_classify_pages,
)


@dataclass
class BundleAnalysis:
    """Complete analysis of a document bundle"""
    filename: str
    total_pages: int
    documents_found: int
    segments: List[DocumentSegment]
    processing_time_seconds: float
    pages_ocrd: int
    model_used: str


def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[Image.Image]:
    """Convert PDF to images at the given DPI (200 is plenty for OCR)."""
    print(f"📄 Converting PDF to images (DPI={dpi})...")
    images = convert_from_path(pdf_path, dpi=dpi)
    print(f"✓ Converted {len(images)} pages")
    return images


def analyze_document_bundle(pdf_path: str, output_dir: str = OUTPUT_DIR) -> BundleAnalysis:
    """
    Main function to analyze a multi-document PDF bundle.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save results
    
    Returns:
        BundleAnalysis object with complete results
    """
    start_time = datetime.now()
    filename = os.path.basename(pdf_path)
    
    print("=" * 70)
    print(f"Multi-Document Bundle Classifier")
    print(f"File: {filename}")
    print("=" * 70)
    
    # Step 1: Convert PDF to images
    images = pdf_to_images(pdf_path)
    total_pages = len(images)

    # Step 2: OCR every non-blank page
    print("\n🔤 Running OCR on each page...")
    doc_client = init_document_client()
    page_texts: List[str] = []
    for i, img in enumerate(images, start=1):
        if is_blank_page(img):
            print(f"  Page {i}: blank, skipped")
            page_texts.append("")
            continue
        print(f"  OCR page {i}...", end=" ")
        text = ocr_page(doc_client, img, i)
        page_texts.append(text)
        preview = text[:50].replace("\n", " ")
        print(f"✓ ({len(text)} chars) \"{preview}...\"" if text else "✓ (no text)")
    pages_ocrd = sum(1 for t in page_texts if t)

    # Step 3: One LLM call groups pages into documents and classifies them
    categories = load_categories()
    gen_client, compartment_id = init_generative_ai_client()
    segments = segment_and_classify_pages(gen_client, compartment_id, page_texts, categories, verbose=True)

    # Calculate processing time
    processing_time = (datetime.now() - start_time).total_seconds()
    
    # Create analysis result
    analysis = BundleAnalysis(
        filename=filename,
        total_pages=total_pages,
        documents_found=len(segments),
        segments=segments,
        processing_time_seconds=processing_time,
        pages_ocrd=pages_ocrd,
        model_used="Meta Llama 3.3 70B Instruct"
    )
    
    # Print results
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    print(f"Total pages: {total_pages}")
    print(f"Documents found: {len(segments)}")
    print(f"Pages OCR'd: {pages_ocrd} ({total_pages - pages_ocrd} blank pages skipped)")
    print(f"Processing time: {processing_time:.1f} seconds")
    
    print("\n📋 Documents in bundle:")
    sensitive_count = 0
    for i, seg in enumerate(segments):
        sensitive_flag = "🔴 SENSITIVE" if seg.is_sensitive else ""
        print(f"\n  {i + 1}. Pages {seg.start_page}-{seg.end_page}: {seg.category}")
        print(f"     Confidence: {seg.confidence} ({seg.confidence_score:.0%})")
        if seg.reasoning:
            print(f"     Reason: {seg.reasoning}")
        if seg.is_sensitive:
            print(f"     {sensitive_flag}")
            sensitive_count += 1
    
    if sensitive_count > 0:
        print(f"\n⚠️  Found {sensitive_count} potentially sensitive document(s)")
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"{os.path.splitext(filename)[0]}_analysis.json"
    output_path = os.path.join(output_dir, output_filename)
    
    # Convert to JSON-serializable format
    result_dict = {
        "filename": analysis.filename,
        "total_pages": analysis.total_pages,
        "documents_found": analysis.documents_found,
        "pages_ocrd": analysis.pages_ocrd,
        "processing_time_seconds": round(analysis.processing_time_seconds, 2),
        "model_used": analysis.model_used,
        "sensitive_documents_found": sensitive_count,
        "documents": [
            {
                "pages": f"{seg.start_page}-{seg.end_page}",
                "page_count": seg.end_page - seg.start_page + 1,
                "category": seg.category,
                "confidence": seg.confidence,
                "confidence_score": seg.confidence_score,
                "reasoning": seg.reasoning,
                "is_sensitive": seg.is_sensitive
            }
            for seg in analysis.segments
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result_dict, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_path}")
    print("=" * 70)
    
    return analysis


def main():
    parser = argparse.ArgumentParser(
        description="Classify multiple documents within a single PDF bundle"
    )
    parser.add_argument(
        "pdf_path",
        help="Path to the PDF file containing multiple documents"
    )
    parser.add_argument(
        "-o", "--output",
        default=OUTPUT_DIR,
        help=f"Output directory for results (default: {OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: File not found: {args.pdf_path}")
        sys.exit(1)
    
    analyze_document_bundle(args.pdf_path, args.output)


if __name__ == "__main__":
    main()
