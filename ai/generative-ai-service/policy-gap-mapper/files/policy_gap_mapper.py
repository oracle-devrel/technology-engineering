"""
Document Understanding with LLMs - Policy Gap Mapper

1) Input regulation PDFs/images/docs and internal policy PDFs/images/docs
2) Use DU to extract text
3) Use LLM to:
   - Extract atomic obligations from regulation
   - Extract control statements from internal policies
   - Map obligations to controls and score coverage
4) Output a gap report in the UI (and optionally as CSV)

To run this code:
1) pip install -r requirements.txt
2) streamlit run doc_llm.py

Author: Ali Ottoman
"""

import io
import json
import os
import base64
import re
from typing import List, Dict, Any

import pandas as pd
from PIL import Image
import streamlit as st

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage

import oci
from oci.ai_document.models import (
    AnalyzeDocumentDetails,
    InlineDocumentDetails,
    DocumentTextExtractionFeature
)
from oci.ai_document import AIServiceDocumentClient
from pdf2image import convert_from_bytes
from config import COMPARTMENT_ID, MODEL_ID

# -----------------------------
# OCI / DU Setup
# -----------------------------

config = oci.config.from_file(profile_name="DEFAULT")
document_client = AIServiceDocumentClient(config)

# -----------------------------
# Helper functions
# -----------------------------

def save_images(images: List[Image.Image], output_format: str = "JPEG") -> List[io.BytesIO]:
    """
    Convert PIL Image objects to in-memory byte streams for downstream processing.
    """
    image_list = []
    for image in images:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)
        image_list.append(img_byte_arr)
    return image_list


def encode_image(image_path: str) -> str:
    """
    Read an image file from disk and return its Base64-encoded string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def save_to_csv(data: List[Dict[str, Any]], file_name: str = "gap_report.csv"):
    """
    Persist a list of dicts to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)
    st.success(f"Data saved to {file_name}")


def extract_text_from_du_response(response_dict: Dict[str, Any]) -> str:
    """
    Extract plain text from the DU analyze_document response.
    Tries multiple patterns to be robust against response structure.
    """
    # Newer DU responses often have `text` at root
    if "text" in response_dict and isinstance(response_dict["text"], str):
        return response_dict["text"]

    pages = response_dict.get("pages", [])
    texts = []

    for page in pages:
        # If full page text exists
        if "text" in page:
            texts.append(page["text"])
            continue

        # Otherwise, build from lines
        lines = page.get("lines", [])
        page_text_lines = []
        for line in lines:
            if "text" in line:
                page_text_lines.append(line["text"])
        if page_text_lines:
            texts.append("\n".join(page_text_lines))

    return "\n\n".join(texts)


def du_extractor(file_obj) -> str:
    """
    Uses Document Understanding to extract plain text from a PDF/image.
    """
    with st.spinner("Extracting text with Document Understanding..."):
        file_bytes = file_obj.read()
        encoded_frame = base64.b64encode(file_bytes).decode("utf-8")

        inline_doc = InlineDocumentDetails(
            data=encoded_frame,
            source="INLINE"
        )

        analyze_details = AnalyzeDocumentDetails(
            compartment_id=COMPARTMENT_ID,
            features=[DocumentTextExtractionFeature()],
            document=inline_doc,
            language="en"
        )

        doc_response = document_client.analyze_document(analyze_details)
        response_dict = oci.util.to_dict(doc_response.data)

    text = extract_text_from_du_response(response_dict)
    return text


def chunk_text(text: str, max_chars: int = 6000) -> List[str]:
    """
    Simple text chunker by character length.
    """
    chunks = []
    text = text.strip()
    while text:
        chunk = text[:max_chars]
        chunks.append(chunk)
        text = text[max_chars:]
    return chunks


def safe_json_loads(raw: str):
    """
    Try to robustly load JSON from an LLM response.
    """
    raw = raw.strip()
    # Try direct load
    try:
        return json.loads(raw)
    except Exception:
        pass

    # Try to extract the first {...} or [...] block
    match = re.search(r'(\{.*\}|\[.*\])', raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    # Last resort: return empty
    return []


# -----------------------------
# LLM Setup
# -----------------------------

llm = ChatOCIGenAI(
    model_id=MODEL_ID,
    compartment_id=COMPARTMENT_ID,
    model_kwargs={"max_tokens": 2000, "temperature": 0}
)


def llm_call(messages: List[Any]) -> str:
    """
    Thin wrapper around ChatOCIGenAI to return the content string.
    """
    response = llm.invoke(messages)
    return response.content if hasattr(response, "content") else str(response)


# LLM Logic: Obligations & Controls

def extract_obligations_llm(text_chunk: str, regulation_name: str = "Regulation") -> List[Dict[str, Any]]:
    """
    Call LLM to extract atomic obligations from a regulation chunk.
    """
    system_prompt = """You are a regulatory analysis assistant for a bank’s compliance team.
                    Input is one section or article from a regulation.
                    Your task is to extract atomic obligations – each is a single, testable requirement.
                    For each obligation, return:
                    "obligation_text"
                    "article_reference": if present in the text, otherwise null
                    "category": short category (e.g., "Data Protection", "Reporting", "Governance")
                    "criticality": "High" | "Medium" | "Low"
                    "keywords": 3–10 key terms

                    Respond ONLY as a JSON array of objects. No extra text.
    """

    user_prompt = f"Regulation name: {regulation_name}\n\nText:\n\"\"\"\n{text_chunk}\n\"\"\""

    raw = llm_call([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    obligations = safe_json_loads(raw)
    if not isinstance(obligations, list):
        obligations = []
    # Add basic IDs if missing
    final_obls = []
    for idx, obl in enumerate(obligations):
        if not isinstance(obl, dict):
            continue
        obl.setdefault("obligation_id", f"{regulation_name}-OBL-{idx+1}")
        obl.setdefault("regulation_name", regulation_name)
        final_obls.append(obl)
    return final_obls


def extract_controls_llm(text_chunk: str, document_name: str) -> List[Dict[str, Any]]:
    """
    Call LLM to extract control statements from an internal policy chunk.
    """
    system_prompt = """You are helping a compliance officer catalogue internal controls.
                    Input is a small section from an internal policy or procedure.
                    Extract 0–5 control statements (if any exist).
                    A control is a specific rule, process, or requirement.

                    For each control, return:
                    - "control_text"
                    - "control_type": one of ["Policy", "Procedure", "Standard", "Guideline"]
                    - "owner_department": guess (e.g., "IT", "Security", "Compliance", "HR")
                    - "keywords": 3–10 key terms

                    Respond ONLY as a JSON array of objects. No extra text.
    """

    user_prompt = f"Document name: {document_name}\n\nText:\n\"\"\"\n{text_chunk}\n\"\"\""

    raw = llm_call([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    controls = safe_json_loads(raw)
    if not isinstance(controls, list):
        controls = []

    final_controls = []
    for idx, ctrl in enumerate(controls):
        if not isinstance(ctrl, dict):
            continue
        ctrl.setdefault("control_id", f"{document_name}-CTRL-{idx+1}")
        ctrl.setdefault("document_name", document_name)
        final_controls.append(ctrl)
    return final_controls


def compute_keyword_overlap_score(obl_keywords: List[str], ctrl_keywords: List[str]) -> int:
    """
    Simple overlap score based on keyword intersection size.
    """
    obl_set = set([k.lower() for k in obl_keywords or []])
    ctrl_set = set([k.lower() for k in ctrl_keywords or []])
    return len(obl_set.intersection(ctrl_set))


def map_obligation_to_controls_llm(obligation: Dict[str, Any],
                                   candidate_controls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Use LLM to map one obligation to candidate controls and score coverage.
    """
    system_prompt = (
        """You are a senior compliance officer. You are given:
            1) One regulatory obligation. 
            2) A list of candidate internal controls.  
            For each control, decide if it: 
            - fully covers the obligation 
            - partially covers the obligation 
            - does not cover the obligation  
            Then: 
            - Assign a coverage_score from 0 to 100 
            - Set coverage_level: \"Full\" | \"Partial\" | \"None\" 
            - Provide a short explanation 
            - If coverage_score < 80, propose improved control wording  
            Finally, decide an overall_status for the obligation: 
            \"Covered\" | \"Partial\" | \"Gap\".  
            Respond EXACTLY in this JSON format: 
        { 
          \"obligation_id\": \"<id>\", 
          \"overall_status\": \"Covered|Partial|Gap\", 
          \"mappings\": [ 
            { 
              \"control_id\": \"<id>\", 
              \"coverage_score\": <0-100>, 
              \"coverage_level\": \"Full|Partial|None\", 
              \"explanation\": \"<text>\", 
              \"suggested_control_text\": \"<text or null>\", 
              \"risks\": [\"<risk1>\", \"<risk2>\"] 
            } 
          ] 
        }"""
    )

    user_payload = {
        "obligation": obligation,
        "candidate_controls": candidate_controls,
    }
    user_prompt = json.dumps(user_payload, ensure_ascii=False)

    raw = llm_call([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    mapping = safe_json_loads(raw)
    if not isinstance(mapping, dict):
        mapping = {
            "obligation_id": obligation.get("obligation_id"),
            "overall_status": "Gap",
            "mappings": []
        }
    return mapping


# -----------------------------
# Streamlit UI
# -----------------------------

def main():
    st.set_page_config(layout="wide")
    st.title("☞ Policy Gap Mapper")

    st.markdown(
        "Upload a **regulation** and your **internal policies**. "
        "The app will extract obligations, map them to your policies, "
        "and show coverage & gaps."
    )

    with st.sidebar:
        st.header("Upload documents")

        regulations_uploaded_files = st.file_uploader(
            "Upload the regulation documents here:",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        internal_policies_uploaded_files = st.file_uploader(
            "Upload your internal policies here:",
            type=["pdf", "jpg", "jpeg", "png"],
            accept_multiple_files=True
        )

        analyze_button = st.button("Analyze", type="primary")

    if analyze_button:
        if not regulations_uploaded_files or not internal_policies_uploaded_files:
            st.error("Please upload at least one regulation document and one internal policy document.")
            return

        # DU extraction
        st.subheader("Step 1: Extracting text from documents")
        reg_texts = []
        for f in regulations_uploaded_files:
            st.write(f"Regulation file: {f.name}")
            reg_texts.append((f.name, du_extractor(f)))

        pol_texts = []
        for f in internal_policies_uploaded_files:
            st.write(f"Policy file: {f.name}")
            pol_texts.append((f.name, du_extractor(f)))

        st.success("Text extraction complete.")

        # Extract obligations
        st.subheader("Step 2: Extracting obligations from regulation")
        all_obligations = []

        for reg_name, reg_text in reg_texts:
            chunks = chunk_text(reg_text, max_chars=6000)
            with st.spinner("Extraction in progress..."):
                for chunk in chunks:
                    obligations = extract_obligations_llm(chunk, regulation_name=reg_name)
                    all_obligations.extend(obligations)

        if not all_obligations:
            st.warning("No obligations could be extracted from the regulation.")
            return

        st.write(f"Extracted **{len(all_obligations)}** obligations from regulation documents.")

        # Extract controls
        st.subheader("Step 3: Extracting controls from internal policies")
        all_controls = []

        for pol_name, pol_text in pol_texts:
            chunks = chunk_text(pol_text, max_chars=6000)
            with st.spinner("Extraction in progress..."):
                for chunk in chunks:
                    controls = extract_controls_llm(chunk, document_name=pol_name)
                    all_controls.extend(controls)

        if not all_controls:
            st.warning("No controls could be extracted from the internal policies.")
            return

        st.write(f"Extracted **{len(all_controls)}** control statements from internal policies.")

        # Retrieve candidate controls per obligation (simple keyword overlap)
        st.subheader("Step 4: Mapping obligations to controls")
        gap_results = []
        progress = st.progress(0)
        total_obls = len(all_obligations)

        for idx, obl in enumerate(all_obligations, start=1):
            obl_keywords = obl.get("keywords") or []

            # Score controls by keyword overlap
            scored_controls = []
            for ctrl in all_controls:
                score = compute_keyword_overlap_score(obl_keywords, ctrl.get("keywords") or [])
                scored_controls.append((score, ctrl))

            # Take top N candidate controls
            scored_controls.sort(key=lambda x: x[0], reverse=True)
            top_n = 5
            candidate_controls = [c for s, c in scored_controls[:top_n] if s > 0]

            # If no keyword overlap at all, still pass a small generic list
            if not candidate_controls:
                candidate_controls = [c for _, c in scored_controls[:3]]

            mapping = map_obligation_to_controls_llm(obl, candidate_controls)
            gap_results.append({
                "obligation": obl,
                "mapping": mapping
            })

            progress.progress(idx / total_obls)

        st.success("Mapping complete.")

        # Build a flat table for display
        st.subheader("Step 5: Gap report")

        table_rows = []
        for item in gap_results:
            obl = item["obligation"]
            mapping = item["mapping"]

            obligation_id = obl.get("obligation_id")
            reg_name = obl.get("regulation_name")
            article_ref = obl.get("article_reference")
            category = obl.get("category")
            criticality = obl.get("criticality")
            overall_status = mapping.get("overall_status", "Unknown")

            table_rows.append({
                "Obligation ID": obligation_id,
                "Regulation": reg_name,
                "Article": article_ref,
                "Category": category,
                "Criticality": criticality,
                "Status": overall_status,
                "Obligation Text": obl.get("obligation_text", "")[:200] + "..."
            })

        df = pd.DataFrame(table_rows)
        st.dataframe(df, use_container_width=True)

        # Download CSV of the flat table
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download gap report as CSV",
            data=csv_data,
            file_name="policy_gap_report.csv",
            mime="text/csv",
        )

        # Drill-down section
        st.subheader("Obligation drill-down")

        selected_obl_id = st.selectbox(
            "Select an obligation to inspect in detail:",
            options=[row["Obligation ID"] for row in table_rows]
        )

        if selected_obl_id:
            item = next(x for x in gap_results if x["obligation"]["obligation_id"] == selected_obl_id)
            obl = item["obligation"]
            mapping = item["mapping"]

            st.markdown(f"### Obligation: `{obl.get('obligation_id')}`")
            st.markdown(f"**Regulation:** {obl.get('regulation_name')}")
            st.markdown(f"**Article:** {obl.get('article_reference')}")
            st.markdown(f"**Category:** {obl.get('category')}  |  **Criticality:** {obl.get('criticality')}")
            st.markdown("**Obligation text:**")
            st.code(obl.get("obligation_text", ""), language="markdown")

            st.markdown(f"**Overall status:** `{mapping.get('overall_status', 'Unknown')}`")
            st.markdown("**Control mappings:**")

            for m in mapping.get("mappings", []):
                ctrl_id = m.get("control_id")
                ctrl = next((c for c in all_controls if c["control_id"] == ctrl_id), None)

                with st.expander(f"Control {ctrl_id} - Coverage {m.get('coverage_score', 0)} ({m.get('coverage_level')})"):
                    if ctrl:
                        st.markdown(f"**Document:** {ctrl.get('document_name')}")
                        st.markdown(f"**Owner dept:** {ctrl.get('owner_department')}")
                        st.markdown("**Control text:**")
                        st.code(ctrl.get("control_text", ""), language="markdown")
                    st.markdown("**Explanation:**")
                    st.write(m.get("explanation", ""))
                    if m.get("risks"):
                        st.markdown("**Risks:**")
                        for r in m["risks"]:
                            st.write(f"- {r}")
                    if m.get("suggested_control_text"):
                        st.markdown("**Suggested improved control wording:**")
                        st.code(m["suggested_control_text"], language="markdown")


if __name__ == "__main__":
    main()
