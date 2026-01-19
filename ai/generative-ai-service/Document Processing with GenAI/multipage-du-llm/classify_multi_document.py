"""
Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Multi-Document Bundle Classifier
================================
Processes large PDF files (e.g., 70 pages) containing multiple scanned documents.
Uses smart boundary detection to minimize OCR/LLM costs.

Strategy:
1. Convert PDF to low-res images for boundary detection
2. Detect document boundaries (blank pages, visual breaks)
3. OCR only first page of each detected sub-document
4. Batch classify all documents with LLM
5. Generate report with page ranges and categories
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
    detect_document_boundaries,
    ocr_page,
    batch_classify_documents,
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


def pdf_to_images(pdf_path: str, dpi: int = 72) -> List[Image.Image]:
    """
    Convert PDF to images at specified DPI.
    Lower DPI (72) for boundary detection, higher (200) for OCR.
    """
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
    
    # Step 1: Convert PDF to low-res images for boundary detection
    low_res_images = pdf_to_images(pdf_path, dpi=72)
    total_pages = len(low_res_images)
    
    # Step 2: Detect document boundaries (using shared function)
    boundaries, blank_pages = detect_document_boundaries(low_res_images, verbose=True)
    
    # Create DocumentSegment objects
    segments = [DocumentSegment(start_page=s, end_page=e) for s, e in boundaries]
    
    # Step 3: Convert to high-res for OCR (only first page of each segment)
    print("\n📷 Converting key pages to high-res for OCR...")
    high_res_images = pdf_to_images(pdf_path, dpi=200)
    
    # Step 4: OCR first page of each segment (using shared function)
    print("\n🔤 Running OCR on first page of each document...")
    doc_client = init_document_client()
    pages_ocrd = 0
    
    for seg in segments:
        page_idx = seg.start_page - 1  # Convert to 0-indexed
        print(f"  OCR page {seg.start_page}...", end=" ")
        seg.first_page_text = ocr_page(doc_client, high_res_images[page_idx], seg.start_page)
        pages_ocrd += 1
        
        if seg.first_page_text:
            preview = seg.first_page_text[:50].replace('\n', ' ')
            print(f"✓ ({len(seg.first_page_text)} chars) \"{preview}...\"")
        else:
            print("✓ (no text)")
    
    # Step 5: Batch classify all documents (using shared function)
    categories = load_categories()
    gen_client, compartment_id = init_generative_ai_client()
    segments = batch_classify_documents(gen_client, compartment_id, segments, categories, verbose=True)
    
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
    print(f"Pages OCR'd: {pages_ocrd} (saved {total_pages - pages_ocrd} OCR calls)")
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
