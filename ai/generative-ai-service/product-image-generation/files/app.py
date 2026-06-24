"""
SKU Imagery Generator — Proof of Concept
Generates lifestyle and product imagery for retail/e-commerce SKUs
using OCI GenAI image generation.

Author: Ali Ottoman
"""

import base64
import io
import streamlit as st
from PIL import Image
from prompt_builder import build_prompt
from oci_client import generate_image

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SKU Image Studio",
    page_icon="⬜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500&display=swap');

/* Reset & base */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    font-weight: 500;
}

.stApp {
    background-color: #F8F7F4;
    color: #1a1a1a;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 3rem 4rem 4rem 4rem; max-width: 1200px; }

/* Header */
.app-header {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.3rem;
    margin-bottom: 0.25rem;
}
.app-title {
    font-family: 'DM Serif Display', serif !important;
    font-size: 2.7rem !important;
    color: #33553C !important;
    letter-spacing: -0.02em !important;
    margin: 0 !important;
    line-height: 1 !important;
}
.app-subtitle {
    font-size: 1.25rem;
    color: #888;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 400;
}
.divider {
    height: 1px;
    background: linear-gradient(to right, #1a1a1a, transparent);
    margin: 1.5rem 0 2.5rem 0;
    opacity: 0.12;
}

/* Section labels */
.section-label {
    font-size: 1.125rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4C825C;
    margin-bottom: 0.5rem;
}

/* Inputs */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-baseweb="select"] {
    background: #ffffff !important;
    border: 1px solid #E8E5E0 !important;
    border-radius: 6px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.92rem !important;
    color: #1a1a1a !important;
    font-weight: 300 !important;
}
div[data-baseweb="input"] input:focus,
div[data-baseweb="textarea"] textarea:focus {
    border-color: #1a1a1a !important;
    box-shadow: none !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label {
    font-size: 0.7rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #999 !important;
}

/* Generate button */
.stButton > button {
    background: #F0CC72 !important;
    color: #1a1a1a !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.7rem 2rem !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    transition: opacity 0.2s ease !important;
    width: 100% !important;
}
.stButton > button:hover {
    opacity: 0.75 !important;
}

/* Output card */
.output-card {
    background: #ffffff;
    border: 1px solid #E8E5E0;
    border-radius: 10px;
    padding: 1.5rem;
    height: 100%;
}
.output-label {
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #bbb;
    margin-bottom: 1rem;
}
.prompt-display {
    background: #F8F7F4;
    border-radius: 6px;
    padding: 1rem;
    font-size: 0.82rem;
    color: #666;
    line-height: 1.6;
    font-style: italic;
}
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 420px;
    color: #ccc;
    gap: 0.75rem;
}
.empty-icon {
    font-size: 2.5rem;
    opacity: 0.3;
}
.empty-text {
    font-size: 0.82rem;
    letter-spacing: 0.06em;
}

/* Metadata row */
.meta-row {
    display: flex;
    gap: 1.5rem;
    margin-top: 1rem;
}
.meta-chip {
    font-size: 0.72rem;
    color: #999;
    background: #F8F7F4;
    border-radius: 4px;
    padding: 0.25rem 0.6rem;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <p class="app-title">SKU Image Studio</p>
    <span class="app-subtitle">Retail Imagery · OCI GenAI</span>
</div>
<div class="divider"></div>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.4], gap="large")

with left_col:
    st.markdown('<div class="section-label">Product Details</div>', unsafe_allow_html=True)

    product_name = st.text_input(
        "Product Name",
        placeholder="e.g. Merino Wool Crewneck Sweater",
    )
    product_description = st.text_area(
        "Description",
        placeholder="e.g. Lightweight, fine-knit, available in earth tones. Positioned as everyday luxury.",
        height=100,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        market = st.selectbox(
            "Target Market",
            ["Global / Neutral", "Middle East", "Western Europe", "North America", "South & Southeast Asia"],
        )
    with col_b:
        shot_type = st.selectbox(
            "Shot Type",
            ["Lifestyle — Editorial", "Lifestyle — Candid", "Flat Lay", "On-Model", "Product Only"],
        )

    setting = st.selectbox(
        "Setting / Context",
        ["Minimal Studio", "Home / Interior", "Outdoor / Urban", "Café / Workspace", "Nature / Travel"],
    )

    st.markdown("<br>", unsafe_allow_html=True)
    generate = st.button("Generate Image")

# ── Generation logic ──────────────────────────────────────────────────────────
if "result" not in st.session_state:
    st.session_state.result = None
if "last_prompt" not in st.session_state:
    st.session_state.last_prompt = None
if "last_meta" not in st.session_state:
    st.session_state.last_meta = {}

if generate:
    if not product_name.strip():
        st.warning("Add a product name to continue.")
    else:
        prompt = build_prompt(product_name, product_description, market, shot_type, setting)
        with right_col:
            with st.spinner("Generating..."):
                img_bytes, error = generate_image(prompt)

        if error:
            st.error(f"Generation failed: {error}")
        else:
            st.session_state.result = img_bytes
            st.session_state.last_prompt = prompt
            st.session_state.last_meta = {
                "market": market,
                "shot": shot_type,
                "setting": setting,
                "size": "1024 × 1024",
                "model": "Add your model name here",
            }

# ── Output panel ──────────────────────────────────────────────────────────────
with right_col:
    st.markdown('<div class="section-label">Output</div>', unsafe_allow_html=True)

    if st.session_state.result:
        img = Image.open(io.BytesIO(st.session_state.result))
        st.image(img, use_container_width=True)

        meta = st.session_state.last_meta
        chips = " ".join([
            f'<span class="meta-chip">{meta["market"]}</span>',
            f'<span class="meta-chip">{meta["shot"]}</span>',
            f'<span class="meta-chip">{meta["setting"]}</span>',
            f'<span class="meta-chip">{meta["size"]}</span>',
            f'<span class="meta-chip">{meta["model"]}</span>',
        ])
        st.markdown(f'<div class="meta-row">{chips}</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="output-label">Prompt sent to model</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="prompt-display">{st.session_state.last_prompt}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.download_button(
            label="Download Image",
            data=st.session_state.result,
            file_name=f"{product_name.lower().replace(' ', '_')}.png",
            mime="image/png",
        )
    else:
        st.markdown("""
        <div class="output-card">
            <div class="empty-state">
                <div class="empty-icon">⬜</div>
                <div class="empty-text">Your generated image will appear here</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
