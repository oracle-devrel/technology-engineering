# pages/multi_document_viewer.py
"""
Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.

Multi-Document Bundle Viewer & Classifier
=========================================
Streamlit app for visually browsing multi-page PDF bundles and classifying 
the documents within them.

Features:
- Visual page-by-page navigation
- Automatic document boundary detection
- Classification of each detected document
- Export results to JSON
"""

import io
import json
import os
import sys
from typing import List, Optional
from dataclasses import dataclass

from PIL import Image
import streamlit as st
from pdf2image import convert_from_bytes

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from config import COMPARTMENT_ID
from oci_utils import (
    init_generative_ai_client,
    init_document_client,
    load_categories,
)
# Import shared utilities - single source of truth
from document_utils import (
    DocumentSegment,
    SENSITIVE_CATEGORIES,
    image_to_jpeg_bytes,
    is_blank_page,
    compute_image_hash,
    detect_document_boundaries,
    ocr_page,
    batch_classify_documents,
)

st.set_page_config(page_title="Multi-Document Viewer", layout="wide")
st.title("📚 Multi-Document Bundle Viewer")
st.caption("Upload a multi-page PDF to detect and classify documents within it")


# ============================================================================
# Data Classes (local to Streamlit app for UI state)
# ============================================================================

@dataclass
class PageInfo:
    """Information about a single page"""
    page_num: int
    image: Image.Image
    is_blank: bool
    is_boundary: bool
    document_idx: Optional[int] = None
    category: Optional[str] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None


@dataclass
class UIDocumentSegment:
    """A detected document within the bundle (for UI)"""
    doc_idx: int
    start_page: int
    end_page: int
    category: Optional[str] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    reasoning: Optional[str] = None
    ocr_text: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

@st.cache_data
def convert_pdf_to_images(pdf_bytes: bytes, dpi: int = 100) -> List[bytes]:
    """Convert PDF to list of JPEG bytes (cached)"""
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    return [image_to_jpeg_bytes(img) for img in images]


def detect_boundaries_for_ui(images: List[Image.Image]) -> List[PageInfo]:
    """
    Detect document boundaries and return page info for UI.
    Uses the shared detect_document_boundaries function.
    """
    # Use shared boundary detection - returns (segments, blank_pages)
    segments, blank_indices = detect_document_boundaries(images, verbose=False)
    blank_set = set(blank_indices)
    
    # Build boundary set from segments
    boundaries = set()
    for start, end in segments:
        boundaries.add(start - 1)  # Convert back to 0-indexed
    
    # Map pages to document indices
    page_to_doc = {}
    for doc_idx, (start, end) in enumerate(segments):
        for page_num in range(start, end + 1):
            page_to_doc[page_num - 1] = doc_idx  # 0-indexed
    
    # Create PageInfo objects
    pages = []
    for i, img in enumerate(images):
        pages.append(PageInfo(
            page_num=i + 1,
            image=img,
            is_blank=i in blank_set,
            is_boundary=i in boundaries,
            document_idx=page_to_doc.get(i) if i not in blank_set else None, 
        ))
    
    return pages


def create_ui_document_segments(pages: List[PageInfo]) -> List[UIDocumentSegment]:
    """Create document segments from page info"""
    segments = {}
    
    for page in pages:
        if page.document_idx is not None:
            if page.document_idx not in segments:
                segments[page.document_idx] = UIDocumentSegment(
                    doc_idx=page.document_idx,
                    start_page=page.page_num,
                    end_page=page.page_num
                )
            else:
                segments[page.document_idx].end_page = page.page_num
    
    return list(segments.values())


def classify_documents_for_ui(
    gen_client, 
    compartment_id: str, 
    segments: List[UIDocumentSegment],
    categories: List[str]
) -> List[UIDocumentSegment]:
    """Classify documents using the shared batch_classify_documents function"""
    
    # Convert UI segments to DocumentSegment for shared function
    shared_segments = [
        DocumentSegment(
            start_page=seg.start_page,
            end_page=seg.end_page,
            first_page_text=seg.ocr_text
        )
        for seg in segments
    ]
    
    # Use shared classification function
    classified_segments = batch_classify_documents(
        gen_client, compartment_id, shared_segments, categories, verbose=False
    )
    
    # Apply results back to UI segments
    for ui_seg, classified in zip(segments, classified_segments):
        ui_seg.category = classified.category
        ui_seg.confidence = classified.confidence
        ui_seg.confidence_score = classified.confidence_score
        ui_seg.reasoning = classified.reasoning
    
    return segments


# ============================================================================
# Main App
# ============================================================================

# Initialize session state
if "pages" not in st.session_state:
    st.session_state.pages = []
if "segments" not in st.session_state:
    st.session_state.segments = []
if "current_page" not in st.session_state:
    st.session_state.current_page = 0
if "classified" not in st.session_state:
    st.session_state.classified = False


# Sidebar
with st.sidebar:
    st.header("📁 Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file:
        if st.button("🔍 Analyze Document", type="primary"):
            with st.spinner("Converting PDF to images..."):
                pdf_bytes = uploaded_file.read()
                images = convert_from_bytes(pdf_bytes, dpi=100)
                
            with st.spinner("Detecting document boundaries..."):
                st.session_state.pages = detect_boundaries_for_ui(images)
                st.session_state.segments = create_ui_document_segments(st.session_state.pages)
                st.session_state.current_page = 0
                st.session_state.classified = False
            
            st.success(f"Found {len(st.session_state.segments)} documents in {len(images)} pages")
        
        if st.session_state.pages and not st.session_state.classified:
            if st.button("🤖 Classify All Documents"):
                with st.spinner("Running OCR on first pages..."):
                    doc_client = init_document_client()
                    for seg in st.session_state.segments:
                        first_page_idx = seg.start_page - 1
                        if first_page_idx < len(st.session_state.pages):
                            img = st.session_state.pages[first_page_idx].image
                            # Use shared OCR function
                            seg.ocr_text = ocr_page(doc_client, img, seg.start_page)
                
                with st.spinner("Classifying with Llama 3.3..."):
                    gen_client, compartment_id = init_generative_ai_client()
                    categories = load_categories()
                    st.session_state.segments = classify_documents_for_ui(
                        gen_client, compartment_id, 
                        st.session_state.segments, categories
                    )
                    
                    # Apply classifications to pages
                    for seg in st.session_state.segments:
                        for page in st.session_state.pages:
                            if page.document_idx == seg.doc_idx:
                                page.category = seg.category
                                page.confidence = seg.confidence
                                page.confidence_score = seg.confidence_score
                    
                    st.session_state.classified = True
                
                st.success("Classification complete!")
                st.rerun()
    
    # Document summary
    if st.session_state.segments:
        st.markdown("---")
        st.subheader("📋 Documents Found")
        for seg in st.session_state.segments:
            is_sensitive = seg.category in SENSITIVE_CATEGORIES
            icon = "🔴" if is_sensitive else "📄"
            category = seg.category or "Not classified"
            confidence = f"{seg.confidence_score:.0%}" if seg.confidence_score else ""
            
            with st.expander(f"{icon} Doc {seg.doc_idx + 1}: Pages {seg.start_page}-{seg.end_page}"):
                st.write(f"**Category:** {category}")
                if seg.confidence:
                    st.write(f"**Confidence:** {seg.confidence} {confidence}")
                if seg.reasoning:
                    st.write(f"**Reasoning:** {seg.reasoning}")
                if is_sensitive:
                    st.warning("⚠️ Potentially sensitive document")


# Main content area
if st.session_state.pages:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Page navigation
        n_pages = len(st.session_state.pages)
        
        nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
        with nav_col1:
            if st.button("⬅️ Previous", disabled=st.session_state.current_page == 0):
                st.session_state.current_page -= 1
                st.rerun()
        
        with nav_col2:
            new_page = st.slider(
                "Page", 1, n_pages, 
                st.session_state.current_page + 1,
                label_visibility="collapsed"
            )
            if new_page - 1 != st.session_state.current_page:
                st.session_state.current_page = new_page - 1
                st.rerun()
        
        with nav_col3:
            if st.button("Next ➡️", disabled=st.session_state.current_page >= n_pages - 1):
                st.session_state.current_page += 1
                st.rerun()
        
        # Display current page
        page_info = st.session_state.pages[st.session_state.current_page]
        
        # Page status badges
        badges = []
        if page_info.is_boundary:
            badges.append("🆕 Document Start")
        if page_info.is_blank:
            badges.append("⬜ Blank Page")
        if page_info.category:
            badges.append(f"📁 {page_info.category}")
        
        st.markdown(f"### Page {page_info.page_num} of {n_pages}")
        if badges:
            st.markdown(" • ".join(badges))
        
        # Display image
        img_bytes = image_to_jpeg_bytes(page_info.image)
        st.image(img_bytes, use_container_width=True)
    
    with col2:
        st.subheader("Page Details")
        
        page_info = st.session_state.pages[st.session_state.current_page]
        
        # Page info
        st.metric("Page Number", f"{page_info.page_num} / {n_pages}")
        
        if page_info.is_blank:
            st.info("⬜ This is a blank/separator page")
        
        if page_info.is_boundary:
            st.success("🆕 New document starts here")
        
        # Document info
        if page_info.document_idx is not None:
            seg = st.session_state.segments[page_info.document_idx]
            
            st.markdown("---")
            st.subheader(f"Document {seg.doc_idx + 1}")
            st.write(f"**Pages:** {seg.start_page} - {seg.end_page}")
            
            if seg.category:
                is_sensitive = seg.category in SENSITIVE_CATEGORIES
                
                if is_sensitive:
                    st.error(f"🔴 **{seg.category}**")
                    st.warning("⚠️ Potentially sensitive document")
                else:
                    st.success(f"📁 **{seg.category}**")
                
                conf_emoji = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(seg.confidence, "⚪")
                st.write(f"**Confidence:** {conf_emoji} {seg.confidence} ({seg.confidence_score:.0%})")
                
                if seg.reasoning:
                    st.write(f"**Reasoning:** {seg.reasoning}")
            else:
                st.info("Not classified yet")
        
        # Export button
        if st.session_state.classified:
            st.markdown("---")
            if st.button("💾 Export Results"):
                result = {
                    "total_pages": len(st.session_state.pages),
                    "documents_found": len(st.session_state.segments),
                    "documents": [
                        {
                            "pages": f"{seg.start_page}-{seg.end_page}",
                            "category": seg.category,
                            "confidence": seg.confidence,
                            "confidence_score": seg.confidence_score,
                            "reasoning": seg.reasoning,
                            "is_sensitive": seg.category in SENSITIVE_CATEGORIES
                        }
                        for seg in st.session_state.segments
                    ]
                }
                
                st.download_button(
                    "📥 Download JSON",
                    json.dumps(result, indent=2),
                    file_name="bundle_analysis.json",
                    mime="application/json"
                )

else:
    # No file uploaded - show instructions
    st.info("👈 Upload a PDF file in the sidebar to begin")
    
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        This tool analyzes multi-page PDF bundles containing multiple scanned documents:
        
        1. **Upload** a PDF containing multiple documents (e.g., employee files)
        2. **Analyze** to detect document boundaries (blank pages, layout changes)
        3. **Classify** each detected document using AI
        4. **Browse** through pages visually with classification info
        5. **Export** results to JSON
        
        **Smart Detection:**
        - Detects blank separator pages
        - Uses visual similarity to find document boundaries
        - Only OCRs the first page of each document (cost efficient)
        
        **Sensitive Document Flagging:**
        - Automatically flags potentially sensitive documents
        - Passports, Bank Details, ID documents, Health records, etc.
        """)
