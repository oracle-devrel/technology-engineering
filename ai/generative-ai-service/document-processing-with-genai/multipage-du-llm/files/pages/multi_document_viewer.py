# pages/multi_document_viewer.py
"""
Copyright (c) 2026 Oracle and/or its affiliates.

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
from typing import List, Optional, Tuple
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
    ocr_page,
    segment_and_classify_pages,
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


def analyze_bundle(images: List[Image.Image]) -> Tuple[List[PageInfo], List[UIDocumentSegment]]:
    """OCR every non-blank page, then let the LLM group pages into documents and classify them."""
    doc_client = init_document_client()
    page_texts = ["" if is_blank_page(img) else ocr_page(doc_client, img, i) for i, img in enumerate(images, 1)]

    gen_client, compartment_id = init_generative_ai_client()
    found = segment_and_classify_pages(gen_client, compartment_id, page_texts, load_categories())

    segments = [
        UIDocumentSegment(doc_idx=i, start_page=s.start_page, end_page=s.end_page, category=s.category,
                          confidence=s.confidence, confidence_score=s.confidence_score,
                          reasoning=s.reasoning, ocr_text=s.first_page_text)
        for i, s in enumerate(found)
    ]
    page_to_seg = {p: seg for seg in segments for p in range(seg.start_page, seg.end_page + 1)}

    pages = []
    for i, img in enumerate(images, 1):
        seg = page_to_seg.get(i)
        pages.append(PageInfo(
            page_num=i, image=img, is_blank=not page_texts[i - 1],
            is_boundary=seg is not None and seg.start_page == i,
            document_idx=seg.doc_idx if seg else None,
            category=seg.category if seg else None,
            confidence=seg.confidence if seg else None,
            confidence_score=seg.confidence_score if seg else None,
        ))
    return pages, segments


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


# Sidebar
with st.sidebar:
    st.header("📁 Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file:
        if st.button("🔍 Analyze & Classify", type="primary"):
            with st.spinner("Converting PDF to images..."):
                images = convert_from_bytes(uploaded_file.read(), dpi=200)
            with st.spinner(f"OCR on {len(images)} pages, then grouping and classifying with Llama 3.3..."):
                st.session_state.pages, st.session_state.segments = analyze_bundle(images)
                st.session_state.current_page = 0
            st.success(f"Found {len(st.session_state.segments)} documents in {len(images)} pages")
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
        if st.session_state.segments:
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
        2. **Analyze & Classify**: every non-blank page is OCR'd, then one LLM call
           groups consecutive pages into documents and classifies each one
        3. **Browse** through pages visually with classification info
        4. **Export** results to JSON
        
        **Why the LLM does the grouping:**
        - Page 2 of a letter looks nothing like page 1, so visual similarity cannot merge them
        - Reading the text, the model sees a continued paragraph or closing signature
        - Blank pages are skipped and never sent to OCR
        
        **Sensitive Document Flagging:**
        - Automatically flags potentially sensitive documents
        - Passports, Bank Details, ID documents, Health records, etc.
        """)
