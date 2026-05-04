"""
OCI Architecture Diagram Generator
==================================

A Streamlit application for generating Oracle Cloud Infrastructure (OCI)
reference architecture diagrams from natural-language descriptions.

Supports multiple text-to-image backends:
    - Qwen DAC (Dedicated AI Cluster on OCI Generative AI)
    - Grok (xAI image generation)

Author: Ali Ottoman
"""
import os
from datetime import datetime
from io import BytesIO

import streamlit as st
from dotenv import load_dotenv

from clients import generate_qwen, generate_grok
from prompts import OCI_STYLE_GUIDE

load_dotenv()

st.set_page_config(
    page_title="Architect — OCI Reference Diagram Generator",
    page_icon="◐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Editorial CSS — serif headline, warm palette, generous spacing, subtle copper accents
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"], .stApp {
    background-color: #FAF9F5 !important;
    font-family: 'Inter', -apple-system, sans-serif;
}

section[data-testid="stSidebar"] {
    background-color: #F4F1EA !important;
    border-right: 1px solid #E8E2D5;
}

h1, h2, h3 {
    font-family: 'Fraunces', Georgia, serif !important;
    font-weight: 500 !important;
    letter-spacing: -0.015em;
    color: #1F1E1B !important;
}

.hero-eyebrow {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #C74634;
    margin-bottom: 18px;
}
.hero-headline {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 64px;
    line-height: 1.02;
    font-weight: 500;
    letter-spacing: -0.025em;
    color: #1F1E1B;
    margin: 0 0 22px 0;
}
.hero-headline em {
    font-style: italic;
    color: #C74634;
    font-weight: 400;
}
.hero-tagline em{
    font-family: 'Inter', sans-serif;
    font-size: 17px;
    line-height: 1.55;
    color: #5C5953;
    max-width: 620px;
    margin: 0 auto 36px auto;
    font-weight: 400;
}
.hero-divider {
    width: 40px;
    height: 1px;
    background: #C74634;
    margin: 0 auto 36px auto;
    opacity: 0.7;
}

.chip-label {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #8B8780;
    text-align: center;
    margin-bottom: 14px;
}

div.stButton > button[kind="secondary"] {
    background: #FFFFFF;
    border: 1px solid #E8E2D5;
    color: #1F1E1B;
    font-family: 'Inter', sans-serif;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 18px;
    border-radius: 999px;
    transition: all 0.15s ease;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #C74634;
    color: #C74634;
    background: #FFFFFF;
}

div.stButton > button[kind="primary"] {
    background: #1F1E1B;
    border: 1px solid #1F1E1B;
    color: #FAF9F5;
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    font-weight: 500;
    padding: 12px 28px;
    border-radius: 6px;
    letter-spacing: 0.01em;
}
div.stButton > button[kind="primary"]:hover {
    background: #C74634;
    border-color: #C74634;
}

div.stTextArea textarea {
    background: #FFFFFF !important;
    border: 1px solid #E8E2D5 !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    color: #1F1E1B !important;
    padding: 14px 16px !important;
}
div.stTextArea textarea:focus {
    border-color: #C74634 !important;
    box-shadow: 0 0 0 3px rgba(199, 70, 52, 0.1) !important;
}

div[data-testid="stSelectbox"] > div > div {
    background: #FFFFFF !important;
    border-color: #E8E2D5 !important;
    border-radius: 6px !important;
}

label {
    font-family: 'Inter', sans-serif !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    color: #5C5953 !important;
    text-transform: uppercase !important;
}

.iteration-meta {
    font-family: 'Inter', sans-serif;
    font-size: 12px;
    color: #8B8780;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.iteration-title {
    font-family: 'Fraunces', Georgia, serif;
    font-size: 28px;
    font-weight: 500;
    color: #1F1E1B;
    letter-spacing: -0.015em;
    margin: 0 0 24px 0;
}
.iteration-title em {
    font-style: italic;
    color: #C74634;
    font-weight: 400;
}

[data-testid="stImage"] img {
    border-radius: 8px;
    border: 1px solid #E8E2D5;
}

hr {
    border: none !important;
    border-top: 1px solid #E8E2D5 !important;
    margin: 32px 0 !important;
}

.stCaption, [data-testid="stCaptionContainer"] {
    color: #8B8780 !important;
    font-size: 12px !important;
}

#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 3rem !important; padding-bottom: 4rem !important; max-width: 1200px;}
</style>
""", unsafe_allow_html=True)


# Session state
if "iterations" not in st.session_state:
    st.session_state.iterations = []
if "qwen_reference" not in st.session_state:
    st.session_state.qwen_reference = None
if "description" not in st.session_state:
    st.session_state.description = ""


QWEN_STYLE_TRANSFER_PREAMBLE = (
    "The attached image is a REFERENCE showing the exact visual style, icon set, "
    "color palette, swim-lane layout, arrow conventions, and typography to use. "
    "Do NOT edit or modify the reference image. Generate a completely NEW Oracle "
    "Cloud Infrastructure architecture diagram that matches that reference's visual "
    "language while rendering the system described below.\n\n"
)

# Sample architectures
SAMPLES = {
    "RAG Chatbot": (
        "A logical reference architecture for a financial-services chatbot with three vertical swim-lane "
        "panels: Channels, AI Services, Data. Channels contains Users and a Web Chat icon. AI Services "
        "contains Oracle Digital Assistant, Cohere Command A LLM, and AI Vector Search 23ai. Data contains "
        "OCI Object Storage for policy docs and Oracle Autonomous Database for conversation history. "
        "Flow: (1) user message into Digital Assistant, (2) embedding lookup against Vector Search, "
        "(3) RAG context plus query to Cohere Command A, (4) response back to user, (5) audit log "
        "to Autonomous Database. Use OCI flat vector aesthetic with monochrome dark-navy icons, "
        "burnt-orange dashed boundaries, charcoal numbered circles."
    ),
    "Document Pipeline": (
        "A logical reference architecture for an enterprise document-intelligence pipeline with four "
        "vertical swim-lanes: Input, Integration, Business Logic, Backend. Input contains Remote Data "
        "Storage, an Input UI, and a Chatbot. Integration contains Oracle Integration and OCI Object "
        "Storage. Business Logic contains a Multi-modal LLM, a Textual LLM, and OCI Document "
        "Understanding. Backend contains Embedding and Data Loading Logic and a Vector Store. "
        "Flow: (1) source data lands in Integration, (2) routed to Object Storage, (3) parallel calls "
        "to multi-modal LLM and OCR which feeds Textual LLM, (4) embeddings written to Vector Store. "
        "Use OCI flat vector aesthetic with monochrome dark-navy icons."
    ),
    "Multi-Region HA": (
        "A physical reference architecture for a high-availability multi-region web application. Render "
        "two OCI Region panels side by side titled OCI Region Frankfurt and OCI Region Amsterdam. Each "
        "region contains an Availability Domain with three Fault Domains and a single LZ Compartment "
        "spanning across them. Inside each LZ Compartment, one VCN with a public Subnet containing a "
        "Load Balancer and a private Subnet containing two Compute instances and an Autonomous Database. "
        "Between the two regions, Oracle Data Guard replication. Above both regions, a global Traffic "
        "Manager DNS icon distributing traffic. Numbered flow shows users hitting Traffic Manager, "
        "routing to the nearest region, requests reaching the Load Balancer, then the Compute layer, "
        "then the database. Use OCI flat vector aesthetic with burnt-orange dashed network boundaries."
    ),
}


# Sidebar — model and config
with st.sidebar:
    st.markdown("<div style='font-family: Fraunces, serif; font-size: 22px; font-weight: 500; "
                "color: #1F1E1B; margin-bottom: 4px;'>Configuration</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 12px; color: #8B8780; margin-bottom: 28px;'>"
                "Choose model and output dimensions.</div>", unsafe_allow_html=True)

    model_choice = st.selectbox(
        "Model",
        ["Image Generation Model", "Qwen (DAC)", "Grok Imagine"],
    )
    size = st.selectbox(
        "Aspect",
        ["1536x1024 — landscape", "1024x1024 — square", "1024x1536 — portrait"],
    )
    size_value = size.split(" ")[0]

    if model_choice == "Qwen (DAC)":
        st.markdown("<hr>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 11px; font-weight: 600; letter-spacing: 0.14em; "
                    "text-transform: uppercase; color: #5C5953; margin-bottom: 4px;'>"
                    "Reference architecture</div>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 12px; color: #8B8780; margin-bottom: 12px;'>"
                    "Required — Qwen runs in image-edit mode.</div>", unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload PNG or JPEG",
            type=["png", "jpg", "jpeg"],
            label_visibility="collapsed",
        )
        if uploaded is not None:
            st.session_state.qwen_reference = {
                "bytes": uploaded.getvalue(),
                "name": uploaded.name,
            }
        if st.session_state.qwen_reference:
            st.image(
                st.session_state.qwen_reference["bytes"],
                caption=st.session_state.qwen_reference["name"],
                use_container_width=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.iterations:
        st.markdown("<hr>", unsafe_allow_html=True)
        if st.button("Reset session", use_container_width=True):
            st.session_state.iterations = []
            st.session_state.description = ""
            st.session_state.qwen_reference = None
            st.rerun()


# Hero — only on first load
if not st.session_state.iterations:
    st.markdown("""
    <div style='text-align: center; padding: 32px 0 12px 0;'>
        <div class='hero-eyebrow'>Reference Architecture · OCI Generative AI</div>
        <h1 class='hero-headline'>Describe the system.<br>Generate the <em>diagram.</em></h1>
        <div class='hero-divider'></div>
        <p class='hero-tagline'>
            Turn a natural-language description of any Oracle Cloud workload into a 
            production-quality reference architecture diagram. Compare three image models 
            side by side. Refine until the picture matches the pitch.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='chip-label'>Start from an example</div>", unsafe_allow_html=True)
    cols = st.columns([1, 1, 1, 1, 1])
    sample_keys = list(SAMPLES.keys())
    for i, key in enumerate(sample_keys):
        with cols[i + 1] if len(sample_keys) <= 3 else cols[i]:
            if st.button(key, key=f"sample_{i}", use_container_width=True):
                st.session_state.description = SAMPLES[key]
                st.rerun()
    st.markdown("<div style='margin-bottom: 40px;'></div>", unsafe_allow_html=True)


# Description input
description = st.text_area(
    "Architecture description",
    value=st.session_state.description,
    height=240,
    placeholder=(
        "Describe the architecture and its data flow. Name every component, the zones they sit in, "
        "and number each step of the flow. The more specific, the better the diagram."
    ),
    label_visibility="visible",
)

refinement = ""
if st.session_state.iterations:
    refinement = st.text_area(
        "Refinement",
        height=120,
        placeholder=(
            "What to change in the next iteration. Example: 'Move the vector store to the Backend "
            "lane, add a step 5 where the Digital Assistant queries it, and thicken the arrows.'"
        ),
    )


# Generate
btn_col1, btn_col2 = st.columns([1, 5])
with btn_col1:
    button_label = "Regenerate" if st.session_state.iterations else "Generate"
    generate_clicked = st.button(button_label, type="primary", use_container_width=True)

if generate_clicked:
    if not description.strip():
        st.warning("Add a description first.")
        st.stop()

    prompt_parts = [OCI_STYLE_GUIDE, description.strip()]
    if refinement.strip():
        prompt_parts.append("\nREFINEMENTS TO APPLY:\n" + refinement.strip())
    prompt = "\n\n".join(prompt_parts)

    host = os.getenv("OCI_GENAI_BASE")
    api_key = os.getenv("OPENAI_API_KEY_CHICAGO")
    project = os.getenv("CHICAGO_PROJECT_OCID")

    if model_choice == "Qwen (DAC)" and not st.session_state.qwen_reference:
        st.warning("Upload a reference architecture in the sidebar — Qwen runs in image-edit mode.")
        st.stop()

    with st.spinner(f"Generating with {model_choice}…"):
        try:
            if model_choice == "Qwen (DAC)":
                ref = st.session_state.qwen_reference
                qwen_prompt = QWEN_STYLE_TRANSFER_PREAMBLE + prompt
                image = generate_qwen(
                    prompt=qwen_prompt,
                    reference_image_bytes=ref["bytes"],
                    reference_image_name=ref["name"],
                    host=host,
                    api_key=api_key,
                    project=project,
                    dac_endpoint_ocid=os.getenv("OCI_QWEN_DAC_ENDPOINT_OCID"),
                )
            else:
                image = generate_grok(
                    prompt=prompt, host=host, api_key=api_key, project=project,
                )
        except Exception as e:
            st.error(f"Generation failed: {e}")
            st.stop()

    st.session_state.iterations.append({
        "timestamp": datetime.now(),
        "model": model_choice,
        "size": size_value,
        "description": description,
        "refinement": refinement,
        "image": image,
    })
    st.session_state.description = description
    st.rerun()


# Latest iteration
if st.session_state.iterations:
    latest = st.session_state.iterations[-1]
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='iteration-meta'>Iteration {len(st.session_state.iterations)} · "
        f"{latest['model']} · {latest['timestamp'].strftime('%H:%M:%S')}</div>"
        f"<div class='iteration-title'>The <em>generated</em> diagram</div>",
        unsafe_allow_html=True,
    )

    st.image(latest["image"], use_container_width=True)

    buf = BytesIO()
    latest["image"].save(buf, format="PNG")
    dl_col1, dl_col2 = st.columns([1, 5])
    with dl_col1:
        st.download_button(
            "Download PNG",
            data=buf.getvalue(),
            file_name=f"oci_architecture_{latest['timestamp'].strftime('%Y%m%d_%H%M%S')}.png",
            mime="image/png",
            use_container_width=True,
        )

    if len(st.session_state.iterations) > 1:
        with st.expander(f"Earlier iterations · {len(st.session_state.iterations) - 1}"):
            for i in range(len(st.session_state.iterations) - 2, -1, -1):
                it = st.session_state.iterations[i]
                cols = st.columns([1, 3])
                cols[0].image(it["image"], width=220)
                cols[1].markdown(
                    f"<div style='font-family: Fraunces, serif; font-size: 18px; "
                    f"font-weight: 500; color: #1F1E1B; margin-bottom: 4px;'>"
                    f"Iteration {i + 1}</div>"
                    f"<div style='font-size: 12px; color: #8B8780; "
                    f"letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 12px;'>"
                    f"{it['model']} · {it['timestamp'].strftime('%H:%M:%S')}</div>",
                    unsafe_allow_html=True,
                )
                if it["refinement"]:
                    cols[1].markdown(
                        f"<div style='font-size: 13px; color: #5C5953; line-height: 1.5; "
                        f"font-style: italic;'>“{it['refinement']}”</div>",
                        unsafe_allow_html=True,
                    )