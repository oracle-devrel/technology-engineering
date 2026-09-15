"""
Legal Due Diligence Agent — Streamlit App
==========================================
Oracle Redwood themed Streamlit app showcasing multi-step agentic contract analysis
using OCI Generative AI Responses API.

Setup:
    pip install streamlit openai pymupdf python-dotenv

Run:
    streamlit run app.py

Notes:
    - Requires .env with OPENAI_API_KEY_CHICAGO and CHICAGO_PROJECT_OCID
    - Place contract PDFs in ./contracts/ directory
"""

import streamlit as st
import os
import json
import time
import fitz  # PyMuPDF
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="OCI Enterprise AI · Legal Due Diligence",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# Theme Dark CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --oracle-red:     #C74634;
        --brand-yellow:   #F1B13F;

        --neutral-30:     #F1EFED;
        --slate-150:      #3C4545;
        --slate-100:      #697778;
        --slate-50:       #C2D4D4;

        --pine-170:       #1E3224;
        --pine-140:       #33553C;
        --pine-100:       #4C825C;

        --teal-170:       #1E3133;
        --teal-140:       #315357;
        --teal-100:       #4F7D7B;

        --bg-base:        #F7F6F3;
        --bg-card:        #FFFFFF;
        --bg-card-2:      #FFFFFF;
        --sidebar-bg:     #F1EFED;
        --border:         #D7D3CC;
        --border-strong:  #BEB8AF;

        --text-pri:       #2F2F2F;
        --text-sec:       #5F6768;
        --text-dim:       #7C8384;

        --input-bg:       #FFFFFF;
        --input-text:     #2F2F2F;
        --input-border:   #C9C4BB;

        --red-glow:       rgba(199, 70, 52, 0.18);
    }

    .stApp,
    .stApp > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"] {
        background-color: var(--bg-base) !important;
        color: var(--text-pri) !important;
    }

    [data-testid="stSidebar"] {
        background: var(--sidebar-bg) !important;
        border-right: 1px solid var(--slate-50) !important;
    }
    [data-testid="stSidebar"] * {
        color: var(--slate-150) !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: var(--slate-50) !important;
    }

    .oracle-header {
        background: linear-gradient(135deg, #FFFFFF 0%, #F3F0EA 100%);
        border-bottom: 2px solid var(--oracle-red);
        padding: 1.2rem 2rem;
        margin: -1rem -1rem 2rem -1rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .oracle-header h1 {
        color: var(--text-pri) !important;
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        margin: 0 !important;
        letter-spacing: -0.3px;
    }
    .oracle-header .badge {
        background: var(--oracle-red);
        color: white;
        font-size: 0.68rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .card-title {
        font-size: 1.1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        color: var(--oracle-red);
    }

    .file-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        display: flex;
        align-items: center;
        gap: 1rem;
        height: 100%;
    }
    .file-icon {
        font-size: 1.8rem;
        width: 44px;
        height: 44px;
        background: rgba(199, 70, 52, 0.10);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }
    .file-name { color: var(--text-pri); font-weight: 600; font-size: 0.88rem; line-height: 1.3; }
    .file-meta { color: var(--text-dim); font-size: 0.72rem; margin-top: 2px; }

    .step-item {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.4rem;
        display: flex;
        align-items: center;
        gap: 0.7rem;
        font-size: 0.82rem;
        transition: all 0.3s ease;
    }
    .step-item.active {
        border-color: var(--oracle-red);
        background: rgba(199, 70, 52, 0.08);
    }
    .step-item.done {
        border-color: var(--pine-100);
        background: rgba(76, 130, 92, 0.08);
    }
    .step-icon {
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.68rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step-icon.pending { background: #E7E3DD; color: var(--text-dim); }
    .step-icon.active { background: var(--oracle-red); color: white; }
    .step-icon.done { background: var(--pine-100); color: white; }
    .step-label { color: var(--text-sec); }
    .step-item.active .step-label { color: var(--text-pri); font-weight: 600; }
    .step-item.done .step-label { color: var(--pine-100); }

    .risk-badge {
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    .risk-critical { background: rgba(255, 59, 48, 0.15); color: #FF3B30; }
    .risk-high     { background: rgba(255, 159, 10, 0.15); color: #FF9F0A; }
    .risk-medium   { background: rgba(90, 200, 250, 0.15); color: #5AC8FA; }
    .risk-low      { background: rgba(76, 130, 92, 0.15);  color: #4C825C; }

    .info-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(199, 70, 52, 0.12);
        border: 1px solid rgba(199, 70, 52, 0.3);
        border-radius: 20px;
        padding: 4px 14px;
        font-size: 0.78rem;
        color: #B94A3D;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .infra-strip {
        background: #FFFFFF;
        border: 1px solid var(--slate-50);
        border-radius: 10px;
        padding: 0.8rem 1rem;
        margin-top: 0.5rem;
    }
    .infra-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.3rem 0;
    }
    .infra-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-dim);
    }
    .infra-value {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-sec);
    }

    .risk-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 0.5rem;
    }
    .risk-table th {
        background: #F3F1ED;
        color: var(--slate-150);
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
        padding: 0.7rem 0.8rem;
        text-align: left;
        border-bottom: 1px solid var(--border);
    }
    .risk-table td {
        padding: 0.8rem;
        font-size: 0.82rem;
        color: var(--text-pri);
        border-bottom: 1px solid var(--border);
        vertical-align: top;
    }
    .risk-table tr:last-child td { border-bottom: none; }
    .risk-table tr:hover td { background: rgba(199, 70, 52, 0.04); }

    .stat-box {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.2rem 1rem;
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.3rem;
    }
    .stat-label {
        font-size: 0.68rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: var(--text-dim);
    }

    .stButton > button {
        background: var(--oracle-red) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.7rem 2.5rem !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        letter-spacing: 0.3px;
    }
    .stButton > button:hover {
        background: #A33828 !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 18px var(--red-glow) !important;
    }
    .stButton > button:active { transform: translateY(0) !important; }

    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div {
        background: var(--input-bg) !important;
        color: var(--input-text) !important;
        border-radius: 8px !important;
        border: 1px solid var(--input-border) !important;
        font-size: 0.92rem !important;
    }

    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: var(--text-dim) !important;
        opacity: 1 !important;
    }

    .stTextInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--oracle-red) !important;
        box-shadow: 0 0 0 2px var(--red-glow) !important;
    }

    .stSelectbox [data-baseweb="select"] svg { fill: var(--text-sec) !important; }

    .stCheckbox label span { color: var(--text-sec) !important; font-size: 0.88rem; }
    .stCheckbox [data-testid="stCheckbox"] > div:first-child {
        border-color: var(--border) !important;
    }

    [data-testid="stFileUploader"] {
        background: var(--bg-card) !important;
        border: 1px dashed var(--border) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }

    .streamlit-expanderHeader {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        color: var(--text-pri) !important;
        font-size: 0.88rem !important;
    }

    hr { border-color: var(--border) !important; }
    .stCaption, small { color: var(--text-dim) !important; }
    .stSpinner > div { border-top-color: var(--oracle-red) !important; }

    .footer-strip {
        background: var(--bg-card);
        border-top: 1px solid var(--border);
        margin: 2rem -1rem -1rem -1rem;
        padding: 0.8rem 2rem;
        display: flex;
        justify-content: center;
        gap: 2.5rem;
    }
    .footer-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .footer-label {
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        color: var(--text-dim);
    }
    .footer-value {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--text-sec);
    }

    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)
# ─────────────────────────────────────────────
# OCI Client
# ─────────────────────────────────────────────
@st.cache_resource
def get_client():
    return OpenAI(
        base_url="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/v1",
        api_key=os.getenv("OPENAI_API_KEY_CHICAGO"),
        project=os.getenv("CHICAGO_PROJECT_OCID"),
    )

MODEL = "xai.grok-4.20-reasoning"

# ─────────────────────────────────────────────
# LLM Helper
# ─────────────────────────────────────────────
def llm_call(system_prompt: str, user_prompt: str) -> str:
    client = get_client()
    response = client.responses.create(
        model=MODEL,
        instructions=system_prompt,
        input=user_prompt,
    )
    return response.output_text


def clean_json_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    return json.loads(cleaned)

# ─────────────────────────────────────────────
# Tool Implementations
# ─────────────────────────────────────────────
def tool_parse_contract(file_path: str) -> dict:
    try:
        doc = fitz.open(file_path)
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
        doc.close()
    except Exception as e:
        return {"error": f"Failed to read PDF: {str(e)}"}

    if not raw_text.strip():
        return {"error": "PDF appears empty or image-based"}

    metadata_str = llm_call(
        system_prompt="""You are a legal document analyst. Extract structured metadata from the contract.
        Return ONLY valid JSON, no markdown, no backticks:
        {
            "contract_type": "type of agreement",
            "parties": [{"name": "...", "role": "...", "jurisdiction": "..."}],
            "effective_date": "date",
            "term_length": "duration",
            "governing_law": "jurisdiction",
            "total_value": "monetary value if stated"
        }""",
        user_prompt=f"Extract metadata from this contract:\n\n{raw_text[:6000]}",
    )

    try:
        metadata = clean_json_response(metadata_str)
    except json.JSONDecodeError:
        metadata = {"raw_response": metadata_str}

    return {
        "contract_id": Path(file_path).stem,
        "file_path": file_path,
        "metadata": metadata,
        "text_length": len(raw_text),
        "full_text": raw_text[:8000],
    }


def tool_extract_clauses(contract_id: str, contract_text: str) -> dict:
    clauses_str = llm_call(
        system_prompt="""You are a senior legal analyst. Extract ALL relevant clauses in these categories.
        For each clause: include the section number, quoted text, and plain-English summary.
        Return ONLY valid JSON, no markdown, no backticks:
        {
            "termination": [{"section": "...", "text": "...", "summary": "..."}],
            "change_of_control": [...],
            "assignment_restrictions": [...],
            "liability_caps": [...],
            "penalty_clauses": [...],
            "exclusivity": [...],
            "non_compete": [...],
            "confidentiality": [...],
            "data_protection": [...],
            "financial_terms": [...],
            "ip_ownership": [...]
        }
        Empty array for categories with no relevant clauses.""",
        user_prompt=f"Extract all key clauses:\n\n{contract_text}",
    )

    try:
        clauses = clean_json_response(clauses_str)
    except json.JSONDecodeError:
        clauses = {"raw_response": clauses_str}

    return {"contract_id": contract_id, "clauses": clauses}


def tool_compare_to_market(contract_id: str, contract_type: str, clauses_json: str) -> dict:
    market_baselines = {
        "SaaS Agreement": {
            "termination_notice": "60-90 days standard",
            "liability_cap": "12 months fees standard",
            "fee_escalation": "3-5% annual standard; >5% aggressive",
            "exclusivity": "Uncommon in SaaS",
            "data_return": "30 days post-termination standard",
            "change_of_control_notice": "90 days standard; <60 aggressive",
        },
        "Employment Agreement": {
            "non_compete_duration": "6-12 months standard; 24 months aggressive",
            "non_compete_geography": "Same country standard; entire GCC very broad",
            "severance": "3-6 months standard; 12 months generous",
            "termination_notice": "30-90 days standard",
            "confidentiality_duration": "2-5 years standard; unlimited aggressive",
        },
        "Commercial Lease": {
            "rent_escalation": "3-5% standard; >5% aggressive",
            "early_termination_penalty": "3-6 months rent standard",
            "security_deposit": "2-3 months standard",
            "renewal_notice": "6-12 months standard",
        },
    }

    baselines = market_baselines.get(contract_type, {})

    comparison_str = llm_call(
        system_prompt=f"""You are a senior M&A lawyer. Compare clauses against market standards.
        BASELINES for {contract_type}: {json.dumps(baselines, indent=2)}
        Rate each: STANDARD, AGGRESSIVE, FAVORABLE, MISSING, or UNUSUAL.
        Return ONLY valid JSON, no markdown:
        {{
            "deviations": [
                {{
                    "clause_category": "...",
                    "finding": "AGGRESSIVE|FAVORABLE|MISSING|UNUSUAL",
                    "detail": "explanation",
                    "risk_level": "HIGH|MEDIUM|LOW",
                    "recommendation": "action item"
                }}
            ],
            "overall_risk": "HIGH|MEDIUM|LOW",
            "summary": "2-3 sentence assessment"
        }}""",
        user_prompt=f"Compare these clauses against market standards:\n\n{clauses_json}",
    )

    try:
        comparison = clean_json_response(comparison_str)
    except json.JSONDecodeError:
        comparison = {"raw_response": comparison_str}

    return {"contract_id": contract_id, "contract_type": contract_type, "comparison": comparison}


def tool_cross_reference_conflicts(all_clauses_json: str) -> dict:
    conflicts_str = llm_call(
        system_prompt="""You are a senior M&A due diligence lawyer reviewing MULTIPLE contracts for the same target.
        Find CONFLICTS, CONTRADICTIONS, and OVERLAPPING OBLIGATIONS.
        Return ONLY valid JSON, no markdown:
        {
            "conflicts": [
                {
                    "contracts_involved": ["id_1", "id_2"],
                    "conflict_type": "CONTRADICTION|OVERLAP|RISK_STACKING|BLOCKING",
                    "detail": "explanation",
                    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
                    "acquisition_impact": "how it affects the deal"
                }
            ],
            "summary": "2-3 sentence assessment"
        }""",
        user_prompt=f"Find conflicts across these contracts:\n\n{all_clauses_json}",
    )

    try:
        conflicts = clean_json_response(conflicts_str)
    except json.JSONDecodeError:
        conflicts = {"raw_response": conflicts_str}

    return {"conflicts": conflicts}


def tool_generate_risk_register(market_json: str, conflicts_json: str, metadata_json: str) -> dict:
    register_str = llm_call(
        system_prompt="""You are a senior M&A partner producing the final risk register.
        Return ONLY valid JSON, no markdown:
        {
            "deal_summary": "overview",
            "critical_risks": [
                {
                    "risk_id": "R-001",
                    "title": "short title",
                    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
                    "source_contracts": ["..."],
                    "description": "what the risk is",
                    "financial_exposure": "estimated impact",
                    "recommendation": "action item",
                    "negotiation_priority": "MUST_FIX|SHOULD_FIX|NICE_TO_HAVE|ACCEPT"
                }
            ],
            "total_identified_risks": 0,
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
            "executive_summary": "3-5 sentence summary",
            "recommended_next_steps": ["step 1", "step 2"]
        }""",
        user_prompt=f"Generate the final risk register:\n\nMETADATA:\n{metadata_json}\n\nDEVIATIONS:\n{market_json}\n\nCONFLICTS:\n{conflicts_json}",
    )

    try:
        register = clean_json_response(register_str)
    except json.JSONDecodeError:
        register = {"raw_response": register_str}

    return {"risk_register": register}


# ─────────────────────────────────────────────
# Tool Router
# ─────────────────────────────────────────────
def execute_tool(name: str, arguments: dict) -> dict:
    if name == "parse_contract":
        return tool_parse_contract(arguments["file_path"])
    elif name == "extract_clauses":
        return tool_extract_clauses(arguments["contract_id"], arguments["contract_text"])
    elif name == "compare_to_market":
        return tool_compare_to_market(arguments["contract_id"], arguments["contract_type"], arguments["clauses_json"])
    elif name == "cross_reference_conflicts":
        return tool_cross_reference_conflicts(arguments["all_clauses_json"])
    elif name == "generate_risk_register":
        return tool_generate_risk_register(arguments["market_deviations_json"], arguments["conflicts_json"], arguments["contracts_metadata_json"])
    return {"error": f"Unknown tool: {name}"}


# ─────────────────────────────────────────────
# Agent Tool Definitions
# ─────────────────────────────────────────────
AGENT_TOOLS = [
    {
        "type": "function",
        "name": "parse_contract",
        "description": "Extracts text from a contract PDF and returns structured metadata. Call this first for each contract.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Path to the contract PDF"}
            },
            "required": ["file_path"],
        },
    },
    {
        "type": "function",
        "name": "extract_clauses",
        "description": "Analyzes contract text and extracts key clauses by category.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract identifier"},
                "contract_text": {"type": "string", "description": "Full text of the contract"},
            },
            "required": ["contract_id", "contract_text"],
        },
    },
    {
        "type": "function",
        "name": "compare_to_market",
        "description": "Compares extracted clauses against market standard terms. Flags deviations.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {"type": "string", "description": "Contract identifier"},
                "contract_type": {"type": "string", "description": "Type of contract"},
                "clauses_json": {"type": "string", "description": "JSON of extracted clauses"},
            },
            "required": ["contract_id", "contract_type", "clauses_json"],
        },
    },
    {
        "type": "function",
        "name": "cross_reference_conflicts",
        "description": "Finds contradictions across ALL contracts. Call after all individual analyses.",
        "parameters": {
            "type": "object",
            "properties": {
                "all_clauses_json": {"type": "string", "description": "JSON of all clauses from all contracts"},
            },
            "required": ["all_clauses_json"],
        },
    },
    {
        "type": "function",
        "name": "generate_risk_register",
        "description": "Produces the final risk register. Call last after all analysis is complete.",
        "parameters": {
            "type": "object",
            "properties": {
                "market_deviations_json": {"type": "string", "description": "All market comparison results"},
                "conflicts_json": {"type": "string", "description": "Cross-reference conflict results"},
                "contracts_metadata_json": {"type": "string", "description": "All contract metadata"},
            },
            "required": ["market_deviations_json", "conflicts_json", "contracts_metadata_json"],
        },
    },
]

AGENT_INSTRUCTIONS = """You are a senior M&A due diligence AI assistant.

Workflow:
1. Call parse_contract for EACH contract PDF to extract text and metadata
2. Call extract_clauses for each parsed contract
3. Call compare_to_market for each contract's clauses
4. After all individual analyses, call cross_reference_conflicts with ALL clauses combined
5. Finally, call generate_risk_register with all findings

Be systematic. Process all contracts before cross-referencing.
Pass JSON data between tools from previous results."""


# ─────────────────────────────────────────────
# Agent Loop (ZDR-compatible)
# ─────────────────────────────────────────────
def run_agent(user_input: str, step_placeholder, log_placeholder):
    client = get_client()
    steps = []
    step_count = 0

    def update_steps(tool_name, status, detail=""):
        nonlocal step_count
        step_count += 1
        steps.append({"step": step_count, "tool": tool_name, "status": status, "detail": detail})
        render_steps(steps, step_placeholder)

    def render_steps(steps_list, placeholder):
        html = ""
        for s in steps_list:
            if s["status"] == "running":
                cls = "active"
                icon_cls = "active"
                icon = "⟳"
            elif s["status"] == "done":
                cls = "done"
                icon_cls = "done"
                icon = "✓"
            else:
                cls = ""
                icon_cls = "pending"
                icon = str(s["step"])

            tool_display = s["tool"].replace("_", " ").title()
            html += f'''<div class="step-item {cls}">
                <div class="step-icon {icon_cls}">{icon}</div>
                <span class="step-label">{tool_display}</span>
            </div>'''
        placeholder.markdown(html, unsafe_allow_html=True)

    # First call
    response = client.responses.create(
        model=MODEL,
        instructions=AGENT_INSTRUCTIONS,
        input=user_input,
        tools=AGENT_TOOLS,
    )

    all_logs = []
    risk_register_data = None
    conversation_history = [{"role": "user", "content": user_input}]

    while True:
        function_calls = [item for item in response.output if item.type == "function_call"]

        if not function_calls:
            return response.output_text, steps, all_logs, risk_register_data

        tool_results = []
        call_items = []
        for call in function_calls:
            args = json.loads(call.arguments)
            update_steps(call.name, "running")

            result = execute_tool(call.name, args)
            if call.name == "generate_risk_register":
                risk_register_data = result
            result_str = json.dumps(result)

            all_logs.append({
                "tool": call.name,
                "args_preview": {k: (v[:60] + "..." if isinstance(v, str) and len(v) > 60 else v) for k, v in args.items()},
                "result_size": len(result_str),
            })

            # Mark done
            steps[-1]["status"] = "done"
            steps[-1]["detail"] = f"{len(result_str):,} chars"
            render_steps(steps, step_placeholder)

            call_items.append({
                "type": "function_call",
                "name": call.name,
                "arguments": call.arguments,
                "call_id": call.call_id,
            })

            tool_results.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": result_str,
            })

        # Append this round's calls + results to the accumulated history
        conversation_history.extend(call_items)
        conversation_history.extend(tool_results)

        # Follow-up with FULL accumulated context
        response = client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            input=conversation_history,
            tools=AGENT_TOOLS,
        )


# ─────────────────────────────────────────────
# Render Risk Register
# ─────────────────────────────────────────────
def render_risk_register(result_text: str):
    """Attempt to parse the agent's final output and render a rich risk register."""
    # Try to extract JSON from the output
    register = None

    # The agent might return the register as JSON or as prose
    # Try to find JSON in the output
    try:
        register = json.loads(result_text)
    except json.JSONDecodeError:
        # Try to find JSON block in text
        if "{" in result_text and "}" in result_text:
            start = result_text.index("{")
            end = result_text.rindex("}") + 1
            try:
                register = json.loads(result_text[start:end])
            except json.JSONDecodeError:
                pass

    if register and "risk_register" in register:
        register = register["risk_register"]

    if register and isinstance(register, dict) and "critical_risks" in register:
        # Stat boxes
        cols = st.columns(5)
        stats = [
            (str(register.get("total_identified_risks", "—")), "Total Risks", "var(--text-pri)"),
            (str(register.get("critical_count", "—")), "Critical", "#FF3B30"),
            (str(register.get("high_count", "—")), "High", "#FF9F0A"),
            (str(register.get("medium_count", "—")), "Medium", "#5AC8FA"),
            (str(register.get("low_count", "—")), "Low", "#34C759"),
        ]
        for col, (num, label, color) in zip(cols, stats):
            col.markdown(f'''
            <div class="stat-box">
                <div class="stat-number" style="color: {color};">{num}</div>
                <div class="stat-label">{label}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

        # Executive summary
        if register.get("executive_summary"):
            st.markdown(f'''
            <div class="card">
                <div class="card-title">Executive Summary</div>
                <div style="color: var(--text-sec); font-size: 0.9rem; line-height: 1.7;">
                    {register["executive_summary"]}
                </div>
            </div>
            ''', unsafe_allow_html=True)

        # Risk table
        risks = register.get("critical_risks", [])
        if risks:
            severity_class = {"CRITICAL": "risk-critical", "HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}
            priority_labels = {"MUST_FIX": "🔴 Must Fix", "SHOULD_FIX": "🟠 Should Fix", "NICE_TO_HAVE": "🔵 Nice to Have", "ACCEPT": "🟢 Accept"}

            rows_html = ""
            for risk in risks:
                sev = risk.get("severity", "MEDIUM")
                sev_cls = severity_class.get(sev, "risk-medium")
                priority = priority_labels.get(risk.get("negotiation_priority", ""), risk.get("negotiation_priority", "—"))
                contracts = ", ".join(risk.get("source_contracts", [])) if risk.get("source_contracts") else "—"

                rows_html += f'''<tr>
                    <td style="font-weight:700; color: var(--red-600); white-space:nowrap;">{risk.get("risk_id", "—")}</td>
                    <td><strong>{risk.get("title", "—")}</strong><br/><span style="color: var(--text-dim); font-size:0.78rem;">{contracts}</span></td>
                    <td><span class="risk-badge {sev_cls}">{sev}</span></td>
                    <td style="color: var(--text-sec); font-size:0.82rem;">{risk.get("description", "—")}</td>
                    <td style="color: var(--amber); font-weight:600; font-size:0.82rem;">{risk.get("financial_exposure", "—")}</td>
                    <td style="font-size:0.82rem;">{priority}</td>
                    <td style="color: var(--text-sec); font-size:0.82rem;">{risk.get("recommendation", "—")}</td>
                </tr>'''

            st.markdown(f'''
            <div class="card" style="overflow-x: auto;">
                <div class="card-title">Risk Register</div>
                <table class="risk-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Risk</th>
                            <th>Severity</th>
                            <th>Description</th>
                            <th>Exposure</th>
                            <th>Priority</th>
                            <th>Recommendation</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            ''', unsafe_allow_html=True)

        # Next steps
        next_steps = register.get("recommended_next_steps", [])
        if next_steps:
            steps_html = "".join(
                f'<div style="display:flex; align-items:flex-start; gap:0.6rem; margin-bottom:0.5rem;">'
                f'<span style="color:var(--red-600); font-weight:700; flex-shrink:0;">{i+1}.</span>'
                f'<span style="color:var(--text-sec); font-size:0.88rem;">{step}</span></div>'
                for i, step in enumerate(next_steps)
            )
            st.markdown(f'''
            <div class="card">
                <div class="card-title">Recommended Next Steps</div>
                {steps_html}
            </div>
            ''', unsafe_allow_html=True)
    else:
        # Fallback: render raw text
        st.markdown("""
        <div class="card">
            <div class="card-title">Analysis Results</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(result_text.strip())

# ─────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────

def app():
    # Header
    st.markdown("""
    <div class="oracle-header">
        <div>
            <h1>⚖️ OCI Enterprise AI · Legal Due Diligence</h1>
        </div>
        <span class="badge">Responses API · Multi-Step Agent</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.markdown("### 📋 Workflow")
        st.markdown("""
        <div style="color: var(--text-dim); font-size: 0.78rem; line-height: 1.7;">
        <strong style="color: var(--text-sec);">1.</strong> Parse each contract PDF<br/>
        <strong style="color: var(--text-sec);">2.</strong> Extract key clauses by category<br/>
        <strong style="color: var(--text-sec);">3.</strong> Compare against market standards<br/>
        <strong style="color: var(--text-sec);">4.</strong> Cross-reference for conflicts<br/>
        <strong style="color: var(--text-sec);">5.</strong> Generate risk register
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.markdown("### 📄 Contract Sources")
        st.markdown("<div style='color: var(--text-dim); font-size: 0.82rem; margin-bottom: 0.8rem;'>Upload PDFs or use the included samples</div>", unsafe_allow_html=True)

        use_samples = st.checkbox("Use sample contracts", value=True)

        if not use_samples:
            uploaded_files = st.file_uploader(
                "Upload contract PDFs",
                type=["pdf"],
                accept_multiple_files=True,
            )
        else:
            uploaded_files = None

        st.markdown("---")
        st.markdown("### 🏗️ Infrastructure")

        st.markdown(f"""
        <div class="infra-strip">
            <div class="infra-row">
                <span class="infra-label">Model</span>
                <span class="infra-value">{MODEL}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


    # Main content
    contract_dir = Path("./contracts")

    if use_samples:
        contract_files = sorted(contract_dir.glob("*.pdf")) if contract_dir.exists() else []
    else:
        contract_files = []
        if uploaded_files:
            upload_dir = Path("/tmp/uploaded_contracts")
            upload_dir.mkdir(exist_ok=True)
            for uf in uploaded_files:
                path = upload_dir / uf.name
                path.write_bytes(uf.getvalue())
                contract_files.append(path)

    # Show loaded contracts
    if contract_files:
        st.markdown("""
        <div class="card">
            <div class="card-title">Contracts</div>
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(len(contract_files))
        for col, f in zip(cols, contract_files):
            size_kb = f.stat().st_size / 1024
            name = f.stem.replace("_", " ").title()
            col.markdown(f'''
            <div class="file-card">
                <div class="file-icon">📑</div>
                <div>
                    <div class="file-name">{name}</div>
                    <div class="file-meta">{size_kb:.0f} KB · PDF</div>
                </div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

        # Deal name in a card
        deal_name = st.text_input(
            "Deal Name",
            value="",
            help="Name of the M&A transaction for the report header",
            label_visibility="collapsed",
            placeholder="Enter deal name, e.g. Acquisition of Acme Holdings Ltd",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)

        # Run button
        if st.button("🔍  Run Due Diligence Analysis", use_container_width=True):
            contracts_list = "\n".join(f"- {f}" for f in contract_files)
            user_input = f"""Perform a full due diligence review of the following contracts for the {deal_name}:
                            {contracts_list}
                            For each contract:
                            1. Parse and extract metadata
                            2. Extract all key clauses
                            3. Compare clauses against market standards
                            Then cross-reference all contracts for conflicts, and produce a comprehensive risk register."""
            col_steps, col_results = st.columns([1, 2.5])

            with col_steps:
                st.markdown("""
                <div class="card">
                    <div class="card-title">Agent Progress</div>
                </div>
                """, unsafe_allow_html=True)
                step_placeholder = st.empty()

            with col_results:
                result_placeholder = st.empty()
                with result_placeholder.container():
                    st.markdown('''
                    <div class="card" style="text-align:center; padding: 4rem 2rem;">
                        <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">⏳</div>
                        <div style="color: var(--text-pri); font-size: 1rem; font-weight: 600; margin-bottom: 0.3rem;">Analyzing contracts...</div>
                        <div style="color: var(--text-dim); font-size: 0.82rem;">The agent is processing each contract through 5 analysis stages.</div>
                    </div>
                    ''', unsafe_allow_html=True)

            log_placeholder = st.empty()

            try:
                start_time = time.time()
                result_text, steps, logs, risk_register_data = run_agent(user_input, step_placeholder, log_placeholder)
                elapsed = time.time() - start_time

                with col_results:
                    result_placeholder.empty()
                    render_risk_register(json.dumps(risk_register_data) if risk_register_data else result_text)

                # Metadata footer
                st.markdown(f"""
                <div class="footer-strip">
                    <div class="footer-item">
                        <span class="footer-label">Model</span>
                        <span class="footer-value">{MODEL}</span>
                    </div>
                    <div class="footer-item">
                        <span class="footer-label">Duration</span>
                        <span class="footer-value">{elapsed:.0f}s</span>
                    </div>
                    <div class="footer-item">
                        <span class="footer-label">Tool Calls</span>
                        <span class="footer-value">{len(steps)}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)


            except Exception as e:
                st.error(f"Agent error: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

    else:
        st.markdown('''
        <div class="card" style="text-align:center; padding: 4rem 2rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.8rem;">📄</div>
            <div style="color: var(--text-pri); font-size: 1.1rem; font-weight: 600; margin-bottom: 0.5rem;">No Contracts Loaded</div>
            <div style="color: var(--text-dim); font-size: 0.88rem;">
                Enable "Use sample contracts" in the sidebar or upload your own PDFs to begin analysis.
            </div>
        </div>
        ''', unsafe_allow_html=True)


if __name__ == "__main__":
    app()