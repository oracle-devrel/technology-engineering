"""
Author: Ali Ottoman
"""

import os
import json
import re
import base64
from datetime import datetime
from typing import List, Dict, Any

import streamlit as st
from reportlab.pdfbase import pdfmetrics
import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.pdfbase.ttfonts import TTFont

from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import COMPARTMENT_ID, MODEL_ID



# For the font
ARABIC_FONT_PATH = "fonts/NotoNaskhArabic-Regular.ttf" 
# Register a font name for Arabic text
pdfmetrics.registerFont(TTFont("ArabicMain", ARABIC_FONT_PATH))
# -----------------------------
# Helpers
# -----------------------------
def normalize_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def ar(text):
    """Shape + bidi Arabic text for correct RTL display in ReportLab."""
    if not text:
        return ""
    # Ensure we work with str
    text = str(text)
    reshaped = arabic_reshaper.reshape(text)
    # Bidi to get correct visual ordering
    return get_display(reshaped)

def inject_arabic_css():
    with open(ARABIC_FONT_PATH, "rb") as f:
        font_data = f.read()
    encoded = base64.b64encode(font_data).decode("utf-8")

    st.markdown(
        f"""
        <style>
        @font-face {{
            font-family: 'ArabicMainWeb';
            src: url(data:font/ttf;base64,{encoded}) format('truetype');
            font-weight: 400;
            font-style: normal;
        }}

        /* Force Arabic font on most Streamlit text */
        html, body, [class*="stApp"] {{
            font-family: 'ArabicMainWeb', 'Noto Naskh Arabic', 'Amiri', sans-serif !important;
        }}

        /* Markdown + normal text */
        .stMarkdown, .stMarkdown * ,
        .stText, .stText * ,
        .stCaption, .stCaption * ,
        .stTitle, .stTitle * ,
        .stHeader, .stHeader * ,
        .stSubheader, .stSubheader * {{
            font-family: 'ArabicMainWeb', 'Noto Naskh Arabic', 'Amiri', sans-serif !important;
        }}

        /* Inputs (text_area/text_input) */
        textarea, input {{
            font-family: 'ArabicMainWeb', 'Noto Naskh Arabic', 'Amiri', sans-serif !important;
            direction: rtl;
            text-align: right;
        }}

        /* Code blocks (JSON tab) */
        pre, code {{
            font-family: 'ArabicMainWeb', 'Noto Naskh Arabic', 'Amiri', monospace !important;
            direction: rtl;
            text-align: right;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def read_uploaded_txt_files(files) -> List[str]:
    texts = []
    for f in files:
        # Streamlit UploadedFile -> bytes
        b = f.read()
        try:
            txt = b.decode("utf-8")
        except UnicodeDecodeError:
            txt = b.decode("utf-8", errors="replace")
        txt = txt.strip()
        if txt:
            texts.append(txt)
    return texts

def safe_filename(name: str) -> str:
    name = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    name = re.sub(r"\s+", "_", name).strip("_")
    return name[:80] if name else "article"

def build_llm(
    auth_profile: str = "DEFAULT",
):
    """
    ChatOCIGenAI uses OCI config file authentication by default when auth_type="API_KEY".
    Ensure you have ~/.oci/config and API key configured.
    """
    return ChatOCIGenAI(
        model_id= MODEL_ID,
        compartment_id= COMPARTMENT_ID,
        auth_type="API_KEY",
        auth_profile=auth_profile,
        model_kwargs={
            "temperature": 0.6,
            "max_tokens": 2200,
        },
    )

def extract_style_guide(llm, sample_articles: List[str], language: str) -> str:
    """
    Turn many samples into a compact style guide (tone, pacing, structures, phrasing habits).
    Keeps the second generation step cheaper + more consistent.
    """
    samples_joined = "\n\n---\n\n".join(sample_articles[:8])  # keep bounded
    sys = SystemMessage(content=f"""
        You are a senior editor. Your task: infer the author's writing style from sample news articles.

        Return ONLY a compact "style guide" in {language} that includes:
        - Tone (e.g., formal, conversational, assertive, neutral)
        - Sentence length / rhythm
        - Common phrases / transitions the author uses
        - Typical structure (lede, context, quotes, numbers, wrap-up)
        - Preferred level of detail
        - Arabic-specific guidance if Arabic (MSA vs dialect, punctuation norms, diacritics usage)
        - Do's and Don'ts

        Keep it concise but specific: 12-18 bullet points maximum.
        No explanations, no preamble.
    """)

    human = HumanMessage(content=f"""
        SAMPLE ARTICLES (for style imitation). Treat as reference only:

        {samples_joined}
    """)

    resp = llm.invoke([sys, human])
    return resp.content.strip()

def generate_article(llm, *, headline: str, key_facts: str, style_guide: str, language: str) -> Dict[str, Any]:
    """
    Ask for strict JSON so we can reliably write txt/md/json files.
    """
    schema = {
        "language": "Arabic or English",
        "title": "string",
        "subtitle": "string (optional)",
        "lede": "string (1-3 sentences)",
        "body_markdown": "string (markdown, includes headings if needed)",
        "body_text": "string (plain text version)",
        "key_points": ["string", "string"],
        "suggested_tags": ["string", "string"],
        "disclaimer": "string (optional, e.g., 'facts provided by user')"
    }

    sys = SystemMessage(content=f"""
        You are an experienced news writer.

        You MUST write in {language}.
        You MUST follow this style guide closely (tone, pacing, phrasing):

        {style_guide}

        CRITICAL OUTPUT RULES:
        - Output MUST be valid JSON ONLY (no backticks, no commentary).
        - JSON MUST match this schema exactly (keys + types):
        {json.dumps(schema, ensure_ascii=False)}

        CONTENT RULES:
        - Use ONLY the facts provided by the user. Do NOT invent names, dates, quotes, statistics, or locations.
        - If a detail is missing, omit it or use a cautious generic phrasing (without fabricating).
        - Keep it newsroom-quality: clear, structured, and readable.
    """)

    human = HumanMessage(content=f"""
        HEADLINE:
        {headline}

        KEY FACTS (bullet style, may be Arabic/English mixed):
        {key_facts}

        Write the full article.
    """)

    resp = llm.invoke([sys, human])
    raw = resp.content.strip()

    # Minimal cleanup if model adds stray text (still keep strict)
    # If parsing fails, we surface the raw to the user.
    data = json.loads(raw)
    return data

def article_to_markdown(data: Dict[str, Any]) -> str:
    title = data.get("title", "").strip()
    subtitle = (data.get("subtitle") or "").strip()
    lede = data.get("lede", "").strip()
    body_md = data.get("body_markdown", "").strip()
    key_points = data.get("key_points") or []
    tags = data.get("suggested_tags") or []
    disclaimer = (data.get("disclaimer") or "").strip()

    md = []
    if title:
        md.append(f"# {title}")
    if subtitle:
        md.append(f"**{subtitle}**")
    if lede:
        md.append(f"\n{lede}\n")
    if body_md:
        md.append(body_md)

    if key_points:
        md.append("\n## Key points\n")
        for kp in key_points:
            md.append(f"- {kp}")

    if tags:
        md.append("\n## Tags\n")
        md.append(", ".join(tags))

    if disclaimer:
        md.append("\n---\n")
        md.append(disclaimer)

    return "\n".join(md).strip()

def article_to_text(data: Dict[str, Any]) -> str:
    # Prefer model-provided plain text; fallback to stripped markdown
    txt = (data.get("body_text") or "").strip()
    if txt:
        return txt
    # fallback:
    md = article_to_markdown(data)
    md = re.sub(r"^#{1,6}\s*", "", md, flags=re.MULTILINE)
    md = re.sub(r"\*\*(.*?)\*\*", r"\1", md)
    md = re.sub(r"`(.*?)`", r"\1", md)
    return md.strip()


# -----------------------------
# Streamlit UI
# -----------------------------
def admn():
    st.set_page_config(page_title="OCI News Writer", layout="wide")
    inject_arabic_css()
    st.title("📰 OCI GenAI News Writer (Style Mimic)")

    with st.sidebar:
        st.header("OCI / Model Settings")

        language = st.selectbox("Output language", ["Arabic", "English"], index=0)
        st.caption("Tip: For Arabic, keep facts in Arabic for best consistency.")

    col1, col2 = st.columns([1, 1])

    with col1:
        headline = st.text_area("Headline", height=80, placeholder="اكتب العنوان هنا...")
        key_facts = st.text_area(
            "Key facts (bullet points)",
            height=220,
            placeholder="- من؟\n- ماذا حدث؟\n- أين؟\n- متى؟\n- لماذا/كيف؟\n- أرقام/بيانات مؤكدة فقط\n- اقتباسات (إن وجدت) نصاً كما هي",
        )

    with col2:
        st.subheader("Style samples (TXT uploads)")
        samples_files = st.file_uploader(
            "Upload 1+ .txt files (your past articles)",
            type=["txt"],
            accept_multiple_files=True,
        )
        st.caption("These are used ONLY to imitate tone/structure — not copied verbatim.")

    generate_btn = st.button("Generate article", type="primary", use_container_width=True)

    if generate_btn:

        if not headline.strip() or not key_facts.strip():
            st.error("Please provide both a headline and key facts.")
            st.stop()

        sample_texts = read_uploaded_txt_files(samples_files) if samples_files else []
        if len(sample_texts) == 0:
            st.warning("No sample articles uploaded — I’ll generate in a neutral newsroom style (still in your chosen language).")
            # fallback style guide
            style_guide = "اكتب بأسلوب خبري مهني واضح، جمل متوسطة، هيكل: مقدمة ثم تفاصيل ثم خلفية ثم خاتمة." if language == "Arabic" \
                else "Write in a clear professional newsroom style: medium sentences; lede -> details -> context -> wrap-up."
        else:
            with st.status("Extracting style guide from samples...", expanded=False):
                llm = build_llm(auth_profile="DEFAULT")
                style_guide = extract_style_guide(llm, sample_texts, language)

        with st.status("Generating article...", expanded=False):
            llm = build_llm(auth_profile="DEFAULT")
            try:
                data = generate_article(
                    llm,
                    headline=headline.strip(),
                    key_facts=key_facts.strip(),
                    style_guide=style_guide,
                    language=language,
                )
            except Exception as e:
                st.error(f"Generation failed (likely non-JSON output). Error: {e}")
                st.stop()

        md = article_to_markdown(data)
        txt = article_to_text(data)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)

        st.success("Done!")

        tab1, tab2, tab3 = st.tabs(["Markdown", "Text", "JSON"])
        with tab1:
            st.markdown(md)
        with tab2:
            st.text_area("Plain text", value=txt, height=320)
        with tab3:
            st.code(json_str, language="json")

        # Download outputs
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = safe_filename(headline)

        st.download_button(
            "⬇️ Download .md",
            data=md.encode("utf-8"),
            file_name=f"{base}_{ts}.md",
            mime="text/markdown; charset=utf-8",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Download .txt",
            data=txt.encode("utf-8"),
            file_name=f"{base}_{ts}.txt",
            mime="text/plain; charset=utf-8",
            use_container_width=True,
        )
        st.download_button(
            "⬇️ Download .json",
            data=json_str.encode("utf-8"),
            file_name=f"{base}_{ts}.json",
            mime="application/json; charset=utf-8",
            use_container_width=True,
        )

if __name__ == "__main__":
    admn()
