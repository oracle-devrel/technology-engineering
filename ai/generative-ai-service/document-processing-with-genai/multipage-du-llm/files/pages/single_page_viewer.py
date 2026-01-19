# pages/run_document_classifier.py
"""
Copyright (c) 2025 Oracle and/or its affiliates.

MIT License — see LICENSE for details.Streamlit Document Classifier Application
Uses OCI Document Understanding for OCR and OCI Generative AI (Llama 3.3) for classification.
"""

import io
import json
import os
import sys

from PIL import Image
import streamlit as st
from pdf2image import convert_from_bytes
import base64
import oci
from typing import Dict, Tuple

# Add parent directory to path for imports
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Import from centralized modules
from config import (
    COMPARTMENT_ID,
    OCI_LLAMA_3_3_MODEL_ID,
    OUTPUT_DIR,
)
from oci_utils import (
    init_document_client,
    load_categories,
    get_langchain_llm,
)

from oci.ai_document.models import (
    AnalyzeDocumentDetails,
    InlineDocumentDetails,
    DocumentTextExtractionFeature,
)

try:
    from langchain_core.messages import SystemMessage, HumanMessage
except ImportError:
    from langchain.schema import SystemMessage, HumanMessage

st.set_page_config(page_title="Document Classifier", layout="wide")
st.title("Document Classifier")

st.caption(
    "Upload any document (PDF/image) and the AI will classify it into one of the HR/Finance categories using Llama 3.3."
)

# Load categories using shared utility with caching
@st.cache_data
def get_categories():
    """Load document categories from JSON file"""
    try:
        return load_categories()
    except Exception as e:
        st.error(f"Error loading categories: {e}")
        return []

DOCUMENT_CATEGORIES = get_categories()


def extract_text_from_ocr(du_dict, max_chars: int = 3000) -> str:
    """
    Extract plain text from OCR result (no coordinates/layout data).
    Much more efficient for LLM classification - ~80% smaller payload.
    
    Args:
        du_dict: OCR response dictionary from Document Understanding
        max_chars: Maximum characters to extract (to limit LLM tokens)
    
    Returns:
        Plain text string extracted from the document
    """
    text_parts = []
    total_chars = 0
    
    for page in du_dict.get("pages", []):
        for line in page.get("lines", []):
            line_text = line.get("text", "").strip()
            if line_text:
                text_parts.append(line_text)
                total_chars += len(line_text) + 1  # +1 for newline
                
                if total_chars >= max_chars:
                    break
        
        if total_chars >= max_chars:
            break
    
    return "\n".join(text_parts)


def classify_document(
    image_bytes: bytes,
    language: str,
    compartment_id: str,
    show_ocr_output: bool = False
) -> Tuple[Dict, Dict]:
    """
    Classify document using OCR and Llama 3.3 LLM
    """
    # Step 1: Run OCR using shared client
    client = init_document_client()
    encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    inline_doc = InlineDocumentDetails(data=encoded_image, source="INLINE")
    
    analyze_details = AnalyzeDocumentDetails(
        compartment_id=compartment_id,
        features=[DocumentTextExtractionFeature()],
        document=inline_doc,
        language=language,
    )
    
    try:
        du_resp = client.analyze_document(analyze_details)
        du_dict = oci.util.to_dict(du_resp.data)
    except Exception as e:
        if "not currently supported" in str(e):
            st.warning(f"Language '{language}' not officially supported. Retrying with multilingual mode...")
            analyze_details = AnalyzeDocumentDetails(
                compartment_id=compartment_id,
                features=[DocumentTextExtractionFeature()],
                document=inline_doc,
                language="en",
            )
            du_resp = client.analyze_document(analyze_details)
            du_dict = oci.util.to_dict(du_resp.data)
            st.info("OCR completed using multilingual fallback mode")
        else:
            raise e
    
    # Show OCR output if requested
    if show_ocr_output:
        with st.expander("Raw OCR Output from Document Understanding"):
            ocr_display = json.dumps(du_dict, indent=2, ensure_ascii=False)
            st.code(ocr_display, language="json")
    
    # Extract plain text from OCR (much more efficient than JSON with coordinates)
    document_text = extract_text_from_ocr(du_dict, max_chars=3000)

    # Log token reduction
    original_size = len(json.dumps(du_dict, ensure_ascii=False))
    text_size = len(document_text)
    reduction_pct = ((original_size - text_size) / original_size * 100) if original_size > 0 else 0
    
    if show_ocr_output:
        st.info(f"OCR data optimized: {original_size:,} → {text_size:,} characters ({reduction_pct:.1f}% reduction)")
        with st.expander("Extracted Text (sent to LLM)"):
            st.text(document_text)

    # Step 2: Use Llama 3.3 to classify the document
    llm = get_langchain_llm(
        model_id=OCI_LLAMA_3_3_MODEL_ID,
        compartment_id=compartment_id,
    )

    # Create categories list as a formatted string
    categories_list = "\n".join([f"- {cat}" for cat in DOCUMENT_CATEGORIES])

    # Classification prompt
    system_msg = SystemMessage(content="""
You are an expert document classifier for HR and Finance documents.

Your task is to:
1. Analyze the document text provided
2. Classify it into ONE primary category from the provided list
3. Provide a confidence score (high/medium/low)
4. Identify the top 3-4 most likely alternative categories if there's any ambiguity

RULES:
- Return ONLY valid JSON matching the schema below
- Base your classification on document content, structure, and keywords
- High confidence: Clear, unambiguous document type
- Medium confidence: Document matches but has some ambiguous elements
- Low confidence: Document is unclear or could fit multiple categories
- Look for key indicators like:
  * Document titles and headers
  * Form numbers or reference codes
  * Specific terminology (e.g., "visa", "pension", "leave", "payroll")
  * Document structure and layout
  * Mentioned institutions or authorities

OUTPUT SCHEMA:
{
  "primary_category": "The single most likely category",
  "confidence": "high|medium|low",
  "confidence_score": 0.0-1.0,
  "reasoning": "Brief explanation of why this category was chosen",
  "alternative_categories": [
    {
      "category": "Alternative category name",
      "probability": 0.0-1.0,
      "reasoning": "Why this could also match"
    }
  ]
}

Return ONLY the JSON object, no other text.
""")
    
    human_prompt = f"""
Classify the following document into one of these categories:

{categories_list}

=== DOCUMENT TEXT (from OCR) ===
{document_text}

Return ONLY the JSON classification result.
"""

    human_msg = HumanMessage(content=human_prompt)

    # Get LLM response
    raw_text = ""
    try:
        raw_text = llm.invoke([system_msg, human_msg]).content
        
        # Clean up markdown code fences if present
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`").strip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].strip()
        
        # Parse JSON
        result = json.loads(cleaned)
        result["_raw_llm_response"] = raw_text
        
        return result, du_dict
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse LLM response as JSON: {e}")
        return {
            "error": "Failed to parse classification result",
            "_raw_llm_response": raw_text
        }, du_dict
    except Exception as e:
        st.error(f"Classification error: {e}")
        return {"error": str(e), "_raw_llm_response": raw_text}, du_dict


def _first_page_to_jpeg_bytes(file) -> bytes:
    """Convert first page of document to JPEG bytes"""
    Image.MAX_IMAGE_PIXELS = None

    def _to_rgb_jpeg_bytes(img: Image.Image) -> bytes:
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode not in ("RGB",):
            img = img.convert("RGB")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90, optimize=True, progressive=True)
        return buf.getvalue()

    try:
        file.seek(0)
        
        if file.type == "application/pdf":
            pdf_bytes = file.read()
            file.seek(0)
            pages = convert_from_bytes(pdf_bytes, dpi=300)
            if not pages:
                raise ValueError("No pages found in PDF.")
            return _to_rgb_jpeg_bytes(pages[0])
        else:
            img = Image.open(file)
            file.seek(0)
            return _to_rgb_jpeg_bytes(img)
    except Exception as e:
        raise RuntimeError(f"Failed to render first page to JPEG: {e}") from e


def _persist_json(data, path):
    """Save JSON to file"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---- Sidebar Configuration ----
with st.sidebar:
    st.header("Configuration")
    
    language = st.selectbox(
        "OCR Language", 
        options=[
            ("Auto-detect / Multilingual", "en"),
            ("Arabic", "ar"),
            ("English (explicit)", "en"),
            ("Japanese", "ja"),
            ("Chinese Simplified", "zh"),
            ("German", "de"),
            ("French", "fr"),
            ("Spanish", "es"),
            ("Italian", "it"),
            ("Portuguese", "pt"),
            ("Dutch", "nl"),
            ("Russian", "ru")
        ],
        format_func=lambda x: x[0],
        index=0
    )
    
    st.info(f"OCR Language: **{language[0]}** (`{language[1]}`)")
    st.success("**LLM Model:** Meta Llama 3.3 70B Instruct")
    
    show_ocr = st.checkbox("Show raw OCR output", value=False)
    show_llm_response = st.checkbox("Show raw LLM response (debug)", value=False)
    save_outputs = st.checkbox("Save results to disk", value=True)
    
    out_dir = st.text_input("Output folder", value=OUTPUT_DIR) if save_outputs else OUTPUT_DIR
    
    # Show loaded categories
    with st.expander(f"Loaded Categories ({len(DOCUMENT_CATEGORIES)})"):
        st.write(DOCUMENT_CATEGORIES)

# ---- Main Interface ----
uploaded = st.file_uploader(
    "Upload a document (PDF/JPG/PNG):", 
    type=["pdf", "jpg", "jpeg", "png"]
)

if uploaded:
    # Convert to JPEG once and reuse
    try:
        img_bytes = _first_page_to_jpeg_bytes(uploaded)
    except Exception as e:
        st.error(f"Error processing document: {e}")
        st.stop()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Document Preview")
        try:
            st.image(img_bytes, use_container_width=True)
            if uploaded.type == "application/pdf":
                st.info("PDF uploaded - showing first page")
        except Exception as e:
            st.error(f"Could not display preview: {e}")
    
    with col2:
        with st.spinner("Analyzing and classifying document with Llama 3.3..."):
            try:
                result, ocr_data = classify_document(
                    image_bytes=img_bytes,
                    language=language[1],
                    compartment_id=COMPARTMENT_ID,
                    show_ocr_output=show_ocr
                )
                
                # Show raw LLM response if debug is enabled
                if show_llm_response and "_raw_llm_response" in result:
                    with st.expander("Raw LLM Response (Debug)"):
                        st.code(result["_raw_llm_response"])
                
                if "error" not in result:
                    # Display classification results
                    st.markdown("### Classification Result • Llama 3.3")
                    
                    # Primary classification
                    primary_cat = result.get("primary_category", "Unknown")
                    confidence = result.get("confidence", "unknown")
                    confidence_score = result.get("confidence_score", 0.0)
                    reasoning = result.get("reasoning", "No reasoning provided")
                    
                    # Confidence color coding
                    conf_color_map = {
                        "high": "🟢",
                        "medium": "🟡",
                        "low": "🔴"
                    }
                    conf_emoji = conf_color_map.get(confidence.lower(), "⚪")
                    
                    # Display primary result
                    st.success(f"**Primary Category:** {primary_cat}")
                    st.info(f"{conf_emoji} **Confidence:** {confidence.upper()} ({confidence_score:.2%})")
                    st.write(f"**Reasoning:** {reasoning}")
                    
                    # Display alternative categories
                    alternatives = result.get("alternative_categories", [])
                    if alternatives:
                        st.markdown("#### Alternative Classifications")
                        for i, alt in enumerate(alternatives[:3], 1):
                            alt_cat = alt.get("category", "Unknown")
                            alt_prob = alt.get("probability", 0.0)
                            alt_reason = alt.get("reasoning", "")
                            
                            with st.expander(f"{i}. {alt_cat} ({alt_prob:.1%})"):
                                st.write(alt_reason)
                    
                    # Summary metrics
                    st.markdown("---")
                    cols = st.columns(4)
                    with cols[0]:
                        st.metric("Primary", primary_cat)
                    with cols[1]:
                        st.metric("Confidence", f"{confidence_score:.0%}")
                    with cols[2]:
                        st.metric("Alternatives", len(alternatives))
                    with cols[3]:
                        st.metric("Model", "Llama 3.3")
                    
                    # Show raw data in expander
                    with st.expander("View Raw Classification Data"):
                        display_result = {k: v for k, v in result.items() if not k.startswith("_")}
                        st.json(display_result)
                    
                    # Save results
                    if save_outputs:
                        base = os.path.splitext(uploaded.name)[0]
                        json_path = os.path.join(out_dir, f"{base}.classification.json")
                        
                        full_output = {
                            "filename": uploaded.name,
                            "classification_result": {k: v for k, v in result.items() if not k.startswith("_")},
                            "model_used": "Meta Llama 3.3 70B Instruct",
                            "ocr_language": language[0]
                        }
                        
                        _persist_json(full_output, json_path)
                        st.success(f"✅ Saved results to: `{json_path}`")
                
                else:
                    st.error("Failed to classify document")
                    if "_raw_llm_response" in result:
                        with st.expander("Raw response"):
                            st.code(result["_raw_llm_response"])
                    
            except Exception as e:
                st.error(f"Processing error: {e}")
                import traceback
                with st.expander("Error details"):
                    st.code(traceback.format_exc())
else:
    # Instructions when no file is uploaded
    st.info("📄 Upload a document to begin automatic classification")
    
    with st.expander("ℹ️ How it works"):
        st.markdown("""
        This tool uses a two-step process:
        
        1. **OCR (Optical Character Recognition)**: OCI Document Understanding extracts text from your document
        2. **AI Classification**: Meta Llama 3.3 70B analyzes the content and classifies it into one of the predefined categories
        
        **Features:**
        - Classifies into 90+ HR and Finance document categories
        - Provides confidence scoring (high/medium/low)
        - Shows alternative classifications if there's ambiguity
        - Explains the reasoning behind the classification
        - Supports multiple languages
        """)
    
    st.markdown("---")
    st.markdown(f"**Loaded {len(DOCUMENT_CATEGORIES)} document categories**")
