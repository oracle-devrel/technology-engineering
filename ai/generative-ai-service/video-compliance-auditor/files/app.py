"""
Compliance Audit Intelligence
Powered by NVIDIA Nemotron 3 Nano Omni 30B (Reasoning) on OCI Generative AI (DAC).

Audits video recordings against documented SOPs using a single multimodal model —
video frames, embedded audio, and policy text reasoned over jointly.

Author: Ali Ottoman
"""
import html
import os
import streamlit as st
from oci_openai import OciOpenAI, OciUserPrincipalAuth
from pydantic import ValidationError

import config
import prompts
from schemas import AuditReport, Finding
from utils import (
    detect_video_mime,
    encode_video_inline,
    extract_pdf_text,
    parse_json_response,
)
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Compliance Audit Intelligence",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Styling
def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,400;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,400;1,9..144,500;1,9..144,600&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
          --bg: #FAF9F5;
          --bg-alt: #F4F2EA;
          --bg-card: #FFFFFF;
          --border: #E8E6DD;
          --border-strong: #D6D2C4;
          --text: #1A1A1A;
          --text-muted: #6B6B6B;
          --text-faint: #9B9690;
          --accent: #C74634;
          --accent-hover: #A53A2A;
          --accent-soft: #FCEBE7;
          --accent-deep: #7A2A1F;
          --success: #16A34A;
          --success-soft: #DCFCE7;
          --warn: #D97706;
          --warn-soft: #FEF3C7;
          --minor: #A16207;
          --minor-soft: #FEF9C3;
          --info: #6B7280;
          --info-soft: #E5E7EB;
        }

        html, body, .stApp {
          background: var(--bg) !important;
          font-family: 'Inter', sans-serif;
          color: var(--text);
        }
        .block-container { padding-top: 1.2rem; max-width: 1180px; }

        h1, h2, h3, h4 {
          font-family: 'Fraunces', serif;
          color: var(--text);
          letter-spacing: -0.015em;
        }

        /* ───────── Hero ───────── */
        .hero {
          padding: 2.2rem 0 0 0;
          border-bottom: 1px solid var(--border);
          margin-bottom: 2.5rem;
          position: relative;
        }
        .eyebrow {
          display: inline-flex;
          align-items: center;
          gap: 0.55rem;
          padding: 0.32rem 0.8rem;
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 999px;
          font-size: 0.7rem;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          font-weight: 600;
          color: var(--text-muted);
          margin-bottom: 1.4rem;
        }
        .eyebrow-dot {
          width: 6px; height: 6px; border-radius: 50%;
          background: var(--accent);
          box-shadow: 0 0 0 3px var(--accent-soft);
        }
        .hero-title {
          font-family: 'Fraunces', serif;
          font-size: 4.2rem;
          font-weight: 400;
          line-height: 1;
          letter-spacing: -0.025em;
          margin: 0 0 0.4rem 0;
        }
        .hero-title em {
          font-style: italic;
          color: var(--accent);
          font-weight: 500;
        }
        .hero-lede {
          font-family: 'Fraunces', serif;
          font-size: 1.25rem;
          font-weight: 300;
          line-height: 1.45;
          color: var(--text);
          max-width: 720px;
          margin: 0.9rem 0 1.6rem 0;
          letter-spacing: -0.005em;
        }
        .hero-lede em { font-style: italic; color: var(--accent-deep); }

        .spec-row { display: flex; flex-wrap: wrap; gap: 0.45rem; }
        .spec {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.74rem;
          font-weight: 500;
          padding: 0.32rem 0.7rem;
          background: var(--bg-card);
          border: 1px solid var(--border);
          color: var(--text);
          border-radius: 4px;
          letter-spacing: 0.02em;
        }
        .spec-accent {
          background: var(--accent-soft);
          border-color: #F4D5CE;
          color: var(--accent-deep);
        }

        /* ───────── Capability strip ───────── */
        .cap-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 0.75rem;
          margin: 0 0 2.2rem 0;
        }
        .cap-card {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 1.1rem 1.15rem;
          position: relative;
          overflow: hidden;
        }
        .cap-card::before {
          content: '';
          position: absolute;
          left: 0; top: 0; bottom: 0;
          width: 2px;
          background: var(--accent);
          opacity: 0.85;
        }
        .cap-icon {
          width: 28px; height: 28px;
          color: var(--accent);
          margin-bottom: 0.7rem;
        }
        .cap-title {
          font-family: 'Fraunces', serif;
          font-size: 1.05rem;
          font-weight: 500;
          color: var(--text);
          margin-bottom: 0.2rem;
        }
        .cap-desc {
          font-family: 'Inter', sans-serif;
          font-size: 0.8rem;
          color: var(--text-muted);
          line-height: 1.45;
        }

        /* ───────── Numbered steps ───────── */
        .step-row {
          display: flex; align-items: baseline;
          gap: 0.85rem;
          margin: 0.2rem 0 0.85rem 0;
        }
        .step-num {
          font-family: 'Fraunces', serif;
          font-size: 1.3rem;
          font-weight: 500;
          color: var(--accent);
          min-width: 1.5rem;
        }
        .step-label {
          font-family: 'Inter', sans-serif;
          font-size: 0.74rem;
          letter-spacing: 0.16em;
          text-transform: uppercase;
          color: var(--text-muted);
          font-weight: 600;
        }
        .step-divider {
          flex: 1;
          height: 1px;
          background: var(--border);
          margin-left: 0.4rem;
        }

        /* ───────── Verdict ───────── */
        .verdict {
          padding: 1.8rem 2rem;
          border-radius: 10px;
          border: 1px solid var(--border);
          background: var(--bg-card);
          margin-bottom: 1.2rem;
          position: relative;
          overflow: hidden;
        }
        .verdict::before {
          content: '';
          position: absolute;
          left: 0; top: 0; bottom: 0;
          width: 4px;
        }
        .verdict-pass::before { background: var(--success); }
        .verdict-fail::before { background: var(--accent); }
        .verdict-conditional::before { background: var(--warn); }

        .verdict-label {
          font-size: 0.7rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--text-muted);
          font-weight: 600;
        }
        .verdict-status {
          font-family: 'Fraunces', serif;
          font-size: 2.4rem;
          font-weight: 500;
          margin: 0.4rem 0 0.7rem 0;
          line-height: 1.05;
          letter-spacing: -0.02em;
        }
        .v-pass { color: var(--success); }
        .v-fail { color: var(--accent); }
        .v-conditional { color: var(--warn); }
        .verdict-summary {
          color: var(--text);
          font-size: 1.02rem;
          line-height: 1.6;
          font-family: 'Fraunces', serif;
          font-weight: 300;
          max-width: 780px;
        }

        /* ───────── KPI tiles ───────── */
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 0.6rem;
          margin: 1.4rem 0 2rem 0;
        }
        .kpi {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 0.95rem 1rem;
        }
        .kpi-value {
          font-family: 'Fraunces', serif;
          font-size: 2.2rem;
          font-weight: 500;
          line-height: 1;
          color: var(--text);
          letter-spacing: -0.02em;
        }
        .kpi-label {
          font-size: 0.68rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--text-muted);
          font-weight: 600;
          margin-top: 0.4rem;
        }
        .kpi-critical .kpi-value { color: var(--accent); }
        .kpi-major .kpi-value { color: var(--warn); }
        .kpi-minor .kpi-value { color: var(--minor); }
        .kpi-compliant .kpi-value { color: var(--success); }

        /* ───────── Findings (timeline) ───────── */
        .findings-wrap {
          position: relative;
          padding-left: 1rem;
        }
        .findings-wrap::before {
          content: '';
          position: absolute;
          left: 0; top: 0.6rem; bottom: 0.6rem;
          width: 1px;
          background: var(--border);
        }
        .finding {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-left: 3px solid var(--info);
          border-radius: 6px;
          padding: 1.05rem 1.2rem;
          margin-bottom: 0.85rem;
          position: relative;
        }
        .finding::before {
          content: '';
          position: absolute;
          left: -1.05rem;
          top: 1.4rem;
          width: 9px; height: 9px;
          background: var(--bg);
          border: 2px solid var(--accent);
          border-radius: 50%;
        }
        .finding-critical { border-left-color: var(--accent); }
        .finding-major    { border-left-color: var(--warn); }
        .finding-minor    { border-left-color: var(--minor); }
        .finding-compliant{ border-left-color: var(--success); }
        .finding-compliant::before { border-color: var(--success); }
        .finding-major::before { border-color: var(--warn); }
        .finding-minor::before { border-color: var(--minor); }

        .finding-header {
          display: flex; align-items: center; gap: 0.6rem;
          margin-bottom: 0.55rem;
        }
        .timestamp {
          font-family: 'JetBrains Mono', monospace;
          font-size: 0.83rem;
          font-weight: 500;
          color: var(--text);
          background: var(--bg);
          border: 1px solid var(--border);
          padding: 0.18rem 0.55rem;
          border-radius: 4px;
        }
        .badge {
          font-size: 0.65rem;
          letter-spacing: 0.13em;
          text-transform: uppercase;
          font-weight: 700;
          padding: 0.22rem 0.6rem;
          border-radius: 4px;
        }
        .badge-critical  { background: var(--accent-soft);  color: var(--accent); }
        .badge-major     { background: var(--warn-soft);    color: var(--warn); }
        .badge-minor     { background: var(--minor-soft);   color: var(--minor); }
        .badge-compliant { background: var(--success-soft); color: var(--success); }
        .badge-partial   { background: var(--info-soft);    color: var(--info); }

        .finding-clause {
          font-family: 'Fraunces', serif;
          font-size: 1.1rem;
          font-weight: 500;
          color: var(--text);
          margin-bottom: 0.5rem;
          line-height: 1.3;
        }
        .finding-text {
          color: var(--text);
          font-size: 0.93rem;
          line-height: 1.55;
          margin-bottom: 0.45rem;
        }
        .finding-evidence {
          color: var(--text-muted);
          font-size: 0.85rem;
          line-height: 1.5;
          padding-left: 0.7rem;
          border-left: 2px solid var(--border);
          font-family: 'Fraunces', serif;
          font-style: italic;
        }

        /* ───────── Recommendations ───────── */
        .recommendations {
          background: var(--bg-card);
          border: 1px solid var(--border);
          border-radius: 8px;
          padding: 1.4rem 1.6rem;
        }
        .rec-item {
          display: flex; gap: 0.95rem;
          padding: 0.75rem 0;
          border-bottom: 1px solid var(--border);
        }
        .rec-item:last-child { border-bottom: none; }
        .rec-num {
          font-family: 'Fraunces', serif;
          font-style: italic;
          font-size: 1.1rem;
          font-weight: 500;
          color: var(--accent);
          min-width: 1.6rem;
        }
        .rec-text {
          color: var(--text);
          font-size: 0.95rem;
          line-height: 1.55;
          flex: 1;
        }

        /* ───────── Footer ───────── */
        .footer {
          margin-top: 4rem;
          padding: 1.5rem 0 1rem 0;
          border-top: 1px solid var(--border);
          display: flex;
          justify-content: space-between;
          align-items: center;
          font-size: 0.78rem;
          color: var(--text-faint);
        }
        .footer-mark {
          font-family: 'Fraunces', serif;
          font-style: italic;
          color: var(--text-muted);
        }

        /* ───────── Streamlit overrides ───────── */
        .stButton > button {
          background: var(--accent);
          color: white !important;
          border: none;
          border-radius: 6px;
          padding: 0.78rem 1.9rem;
          font-family: 'Inter', sans-serif;
          font-weight: 600;
          font-size: 0.95rem;
          letter-spacing: 0.02em;
          transition: all 0.15s ease;
          box-shadow: 0 1px 2px rgba(199, 70, 52, 0.15);
        }
        .stButton > button:hover:not(:disabled) {
          background: var(--accent-hover);
          color: white !important;
          transform: translateY(-1px);
          box-shadow: 0 4px 10px rgba(199, 70, 52, 0.22);
        }
        .stButton > button:disabled {
          background: #D1CFC4;
          color: var(--text-faint) !important;
          box-shadow: none;
        }
        .stButton > button[kind="secondary"] {
          background: var(--bg-card);
          color: var(--text) !important;
          border: 1px solid var(--border);
          font-weight: 500;
          font-size: 0.86rem;
          padding: 0.5rem 1rem;
          box-shadow: none;
        }
        .stButton > button[kind="secondary"]:hover {
          border-color: var(--accent);
          color: var(--accent) !important;
          background: var(--bg-card);
          transform: none;
          box-shadow: none;
        }

        .stTabs [data-baseweb="tab-list"] {
          gap: 0.4rem;
          border-bottom: 1px solid var(--border);
        }
        .stTabs [data-baseweb="tab"] {
          font-family: 'Inter', sans-serif;
          font-size: 0.9rem;
          color: var(--text-muted);
          font-weight: 500;
        }
        .stTabs [aria-selected="true"] { color: var(--accent) !important; }
        .stTabs [data-baseweb="tab-highlight"] { background: var(--accent) !important; }

        .stTextArea textarea, .stFileUploader { background: var(--bg-card) !important; border-radius: 6px !important; }
        .stTextArea textarea {
          border: 1px solid var(--border) !important;
          font-family: 'Inter', sans-serif !important;
          font-size: 0.9rem !important;
        }
        section[data-testid="stFileUploaderDropzone"] {
          background: var(--bg-card);
          border: 1.5px dashed var(--border-strong);
          padding: 1.5rem 1rem;
        }

        footer, header { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_styles()


# Hero
st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">
        <span class="eyebrow-dot"></span>
        Oracle &times; NVIDIA Nemotron &middot; demo 
      </div>
      <div class="hero-title">Compliance Audit <em>Intelligence</em></div>
      <div class="hero-lede">
        A single multimodal model audits video recordings against documented
        Standard Operating Procedures. Now replacing your fragmented
        <em>Whisper&nbsp;+&nbsp;VLM&nbsp;+&nbsp;LLM</em> pipelines with one
        loop that maintains shared context across video frames, embedded audio, and policy text.
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Capability strip
st.markdown(
    """
    <div class="cap-grid">
      <div class="cap-card">
        <svg class="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="6" width="14" height="12" rx="2"></rect>
          <path d="m22 8-6 4 6 4V8z"></path>
        </svg>
        <div class="cap-title">Video frames</div>
        <div class="cap-desc">Spatiotemporal reasoning over what was physically performed</div>
      </div>
      <div class="cap-card">
        <svg class="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 12h2l3-9 4 18 3-12 2 6h4"></path>
        </svg>
        <div class="cap-title">Audio track</div>
        <div class="cap-desc">Speech, narration, and ambient signals captured natively</div>
      </div>
      <div class="cap-card">
        <svg class="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
          <path d="M14 2v6h6"></path><path d="M9 13h6"></path><path d="M9 17h6"></path>
        </svg>
        <div class="cap-title">Policy text</div>
        <div class="cap-desc">SOP grounding with clause-level reference and citation</div>
      </div>
      <div class="cap-card">
        <svg class="cap-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="3"></circle>
          <path d="M12 2v3M12 19v3M22 12h-3M5 12H2M19.07 4.93l-2.12 2.12M7.05 16.95l-2.12 2.12M19.07 19.07l-2.12-2.12M7.05 7.05 4.93 4.93"></path>
        </svg>
        <div class="cap-title">Reasoning</div>
        <div class="cap-desc">Timestamped findings, severity, and audit-grade evidence</div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# Sample SOP scenarios
SAMPLE_SCENARIOS: dict[str, str] = {
    "🧪 Lab safety": """SOP-LAB-001: Chemical Handling Procedure
1. Personal protective equipment (gloves, goggles, lab coat) must be worn at all times when handling reagents.
2. Fume hood sash must be lowered to 18 inches or below when working with volatile chemicals.
3. Reagents must be returned to their designated storage location immediately after use.
4. Spills must be reported and contained within 60 seconds of occurrence.
5. The eye-wash station must be visibly accessible and unobstructed.""",
    "📞 Customer service call": """SOP-CS-014: Inbound Call Handling
1. Greeting must include agent name, company name, and offer of assistance within 10 seconds.
2. Customer identity must be verified using two factors before discussing account details.
3. Agent must summarize the issue back to the customer before proposing a resolution.
4. Hold time must not exceed 90 seconds without a check-back.
5. Call must close with a clear next step, expected timeline, and reference number.""",
    "🏭 Manufacturing line": """SOP-MFG-203: Pre-Shift Equipment Inspection
1. Operator must complete the visual inspection checklist before starting the line.
2. Emergency stop functionality must be tested and confirmed operational.
3. Lockout-tagout (LOTO) tags must be removed only by the originating technician.
4. PPE compliance (hi-vis vest, hard hat, safety boots) must be verified.
5. Inspection findings must be logged in the shift handover system before line start.""",
}

# Session state
if "sop_text" not in st.session_state:
    st.session_state.sop_text = ""
if "audit_result" not in st.session_state:
    st.session_state.audit_result = None
if "audit_raw" not in st.session_state:
    st.session_state.audit_raw = None


def step_header(num: str, label: str) -> None:
    st.markdown(
        f"""
        <div class="step-row">
          <div class="step-num">{num}</div>
          <div class="step-label">{label}</div>
          <div class="step-divider"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


step_header("01", "Choose a scenario")
chip_cols = st.columns(len(SAMPLE_SCENARIOS) + 1)
for i, (label, sop) in enumerate(SAMPLE_SCENARIOS.items()):
    if chip_cols[i].button(label, key=f"chip_{i}", use_container_width=True):
        st.session_state.sop_text = sop
        st.session_state.audit_result = None
        st.session_state.audit_raw = None

st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

# Two-column input layout: video on the left, SOP on the right
left, right = st.columns(2, gap="large")

with left:
    step_header("02", "Upload recording")
    video_file = st.file_uploader(
        "Upload a video recording",
        type=config.SUPPORTED_VIDEO_TYPES,
        label_visibility="collapsed",
    )
    if video_file is not None:
        size_mb = len(video_file.getvalue()) / (1024 * 1024)
        if size_mb > config.MAX_VIDEO_SIZE_MB:
            st.error(
                f"Video is {size_mb:.1f} MB — exceeds the {config.MAX_VIDEO_SIZE_MB} MB inline limit. "
                "Switch to the Object Storage PAR fallback (see README)."
            )
            video_file = None
        else:
            st.video(video_file)
            st.caption(f"{video_file.name} · {size_mb:.1f} MB")

with right:
    step_header("03", "Provide SOP")
    pdf_tab, text_tab = st.tabs(["PDF upload", "Paste text"])

    with pdf_tab:
        sop_pdf = st.file_uploader(
            "Upload SOP as PDF",
            type=["pdf"],
            label_visibility="collapsed",
            key="sop_pdf",
        )
        if sop_pdf is not None:
            try:
                extracted = extract_pdf_text(sop_pdf.getvalue())
                if extracted:
                    st.session_state.sop_text = extracted
                    st.success(f"Extracted {len(extracted):,} characters from {sop_pdf.name}")
                else:
                    st.warning("No text extracted — the PDF may be scanned (image-only).")
            except Exception as e:
                st.error(f"PDF extraction failed: {e}")

    with text_tab:
        st.session_state.sop_text = st.text_area(
            "Paste SOP text",
            value=st.session_state.sop_text,
            height=240,
            label_visibility="collapsed",
            placeholder="Paste the procedure text here, or use a sample chip above…",
        )

st.markdown("<div style='height:1.4rem'></div>", unsafe_allow_html=True)

step_header("04", "Run audit")
ready = video_file is not None and bool(st.session_state.sop_text.strip())
run = st.button("Run compliance audit", disabled=not ready)


# OCI OpenAI-compatible client
def build_client() -> OciOpenAI:
    return OciOpenAI(
        auth=OciUserPrincipalAuth(profile_name="DEFAULT"),
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        region="uk-london-1",
        base_url=config.OCI_OPENAI_BASE_URL,
    )


# Single audit invocation: builds the multimodal message and returns raw text
def run_audit(video_bytes: bytes, mime_type: str, sop_text: str) -> str:
    video_block = encode_video_inline(video_bytes, mime_type)
    user_prompt = prompts.AUDIT_PROMPT_TEMPLATE.format(sop_text=sop_text.strip())

    messages = [
        {"role": "system", "content": prompts.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                video_block,
            ],
        },
    ]

    client = build_client()
    response = client.chat.completions.create(
        model=config.NEMOTRON_OMNI_OCID,
        messages=messages,
        temperature=config.TEMPERATURE,
        max_tokens=config.MAX_TOKENS,
    )
    return response.choices[0].message.content or ""


if run:
    with st.spinner("Auditing video against SOP - this may take a minute or two…"):
        try:
            mime_type = detect_video_mime(video_file.name)
            raw = run_audit(video_file.getvalue(), mime_type, st.session_state.sop_text)
            st.session_state.audit_raw = raw

            parsed = parse_json_response(raw)
            if parsed is None:
                st.session_state.audit_result = None
                st.error("Could not parse model output as JSON. See raw response below.")
            else:
                try:
                    st.session_state.audit_result = AuditReport.model_validate(parsed)
                except ValidationError as ve:
                    st.session_state.audit_result = None
                    st.error("Schema validation failed.")
                    st.exception(ve)
        except Exception as e:
            st.session_state.audit_result = None
            st.error(f"Audit failed: {e}")
            st.exception(e)


def finding_classes(f: Finding) -> tuple[str, str, str]:
    if f.status == "compliant":
        return "finding-compliant", "badge-compliant", "COMPLIANT"
    if f.status == "partial":
        return "finding-minor", "badge-partial", "PARTIAL"
    severity = f.severity or "major"
    return f"finding-{severity}", f"badge-{severity}", severity.upper()


# Tally findings into KPI counts
def tally(findings: list[Finding]) -> dict:
    counts = {"total": len(findings), "critical": 0, "major": 0, "minor": 0, "compliant": 0}
    for f in findings:
        if f.status == "compliant":
            counts["compliant"] += 1
        elif f.status == "violation":
            sev = f.severity or "major"
            if sev in counts:
                counts[sev] += 1
    return counts


# Results
report: AuditReport | None = st.session_state.audit_result
if report is not None:
    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

    step_header("05", "Audit verdict")

    verdict_class = {
        "pass": "verdict-pass",
        "fail": "verdict-fail",
        "conditional": "verdict-conditional",
    }[report.overall_compliance]
    verdict_text_class = {
        "pass": "v-pass", "fail": "v-fail", "conditional": "v-conditional",
    }[report.overall_compliance]
    verdict_label = {
        "pass": "Compliant",
        "fail": "Non-compliant",
        "conditional": "Conditionally compliant",
    }[report.overall_compliance]

    st.markdown(
        f"""
        <div class="verdict {verdict_class}">
          <div class="verdict-label">Overall</div>
          <div class="verdict-status {verdict_text_class}">{verdict_label}</div>
          <div class="verdict-summary">{html.escape(report.summary)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    counts = tally(report.findings)
    st.markdown(
        f"""
        <div class="kpi-grid">
          <div class="kpi"><div class="kpi-value">{counts['total']}</div><div class="kpi-label">Findings</div></div>
          <div class="kpi kpi-critical"><div class="kpi-value">{counts['critical']}</div><div class="kpi-label">Critical</div></div>
          <div class="kpi kpi-major"><div class="kpi-value">{counts['major']}</div><div class="kpi-label">Major</div></div>
          <div class="kpi kpi-minor"><div class="kpi-value">{counts['minor']}</div><div class="kpi-label">Minor</div></div>
          <div class="kpi kpi-compliant"><div class="kpi-value">{counts['compliant']}</div><div class="kpi-label">Compliant</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if report.findings:
        step_header("06", "Findings timeline")
        # Sort by timestamp string — works for zero-padded MM:SS or HH:MM:SS
        sorted_findings = sorted(report.findings, key=lambda f: f.timestamp)
        # Build each card as a single-line string — Streamlit's markdown dedent
        # falls back to 0 when other parts of the joined string have no leading
        # whitespace, so any indentation here would render as a code block.
        cards_html = ['<div class="findings-wrap">']
        for f in sorted_findings:
            border_cls, badge_cls, badge_text = finding_classes(f)
            cards_html.append(
                f'<div class="finding {border_cls}">'
                f'<div class="finding-header">'
                f'<span class="timestamp">{html.escape(f.timestamp)}</span>'
                f'<span class="badge {badge_cls}">{badge_text}</span>'
                f'</div>'
                f'<div class="finding-clause">{html.escape(f.sop_clause)}</div>'
                f'<div class="finding-text">{html.escape(f.description)}</div>'
                f'<div class="finding-evidence">{html.escape(f.evidence)}</div>'
                f'</div>'
            )
        cards_html.append('</div>')
        st.markdown("".join(cards_html), unsafe_allow_html=True)

    if report.recommendations:
        step_header("07", "Recommendations")
        items = "".join(
            f'<div class="rec-item"><div class="rec-num">{i+1:02d}</div><div class="rec-text">{html.escape(r)}</div></div>'
            for i, r in enumerate(report.recommendations)
        )
        st.markdown(f'<div class="recommendations">{items}</div>', unsafe_allow_html=True)

    with st.expander("Raw structured output"):
        st.json(report.model_dump())

elif st.session_state.audit_raw and report is None:
    with st.expander("Raw model output (unparsed)"):
        st.code(st.session_state.audit_raw)


# Footer
st.markdown(
    """
    <div class="footer">
      <div class="footer-mark">Ali Ottoman &middot; Generative AI Specialist</div>
    </div>
    """,
    unsafe_allow_html=True,
)