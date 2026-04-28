# ⚖️ OCI Enterprise AI — Legal Due Diligence Agent

A multi-step agentic application that performs M&A contract due diligence using **OCI Generative AI Responses API**. The agent autonomously parses contracts, extracts key clauses, compares them against market standards, identifies cross-contract conflicts, and produces a structured risk register, all orchestrated through a single API call with client-side tool execution.

---

## When to Use This Asset

### The Challenge

M&A due diligence is one of the most time-intensive and costly stages of any transaction. Associates and junior lawyers spend days, sometimes weeks, manually reviewing hundreds of contracts to surface risks, flag non-standard terms, and identify conflicts across agreements. The work is repetitive, error-prone under time pressure, and directly impacts deal timelines and advisory fees.

Similar challenges exist across any industry where large volumes of contracts or regulatory documents need systematic review: commercial real estate transactions, insurance policy audits, procurement compliance, government tender evaluations, and regulatory filings.

### Who Is This For?

- **Law firms and legal departments** looking to accelerate due diligence cycles, reduce associate hours on document review, and deliver more consistent risk assessments across deals.
- **Financial services and investment firms** performing portfolio-level contract analysis for acquisitions, fund restructurings, or regulatory compliance reviews.
- **Real estate companies** reviewing lease portfolios, tenant agreements, and property management contracts at scale during acquisitions or portfolio rebalancing.
- **Government and public sector organizations** auditing vendor contracts, procurement agreements, and compliance documentation across departments.
- **Insurance companies** analyzing policy documents, underwriting agreements, and reinsurance treaties for risk exposure and coverage gaps.
- **System integrators and legal tech companies** building document intelligence platforms for their clients on OCI infrastructure.

### When to Use It

- When you need to review **multiple contracts simultaneously** and identify risks both within individual agreements and across the full contract set.
- When the document volume or deal timeline makes **manual review impractical** and you need to surface the most critical risks first.
- When **data sovereignty matters**, the entire pipeline runs on OCI with no data leaving your tenancy, making it suitable for government, financial, and healthcare use cases where documents cannot be sent to third-party APIs.
- When you need a **repeatable, auditable process**, every tool call, input, and output is logged, providing a clear trail of how each risk was identified.

### Key Capabilities

- **Automated contract parsing** — extracts text and structured metadata (parties, dates, governing law, financial terms) from PDF contracts
- **Clause extraction by category** — identifies and categorizes termination, change of control, assignment, liability, penalty, exclusivity, non-compete, confidentiality, data protection, financial, and IP clauses
- **Market standard benchmarking** — compares extracted terms against configurable industry baselines and flags deviations as aggressive, favorable, missing, or unusual
- **Cross-contract conflict detection** — analyzes clauses across all contracts together to find contradictions, overlapping obligations, and terms that could block a transaction
- **Structured risk register** — produces a prioritized risk matrix with severity ratings, financial exposure estimates, and actionable recommendations

---

## How to Use This Asset

### For a Quick Demo

1. Clone the repo and install dependencies
2. Set up your OCI Generative AI project and API key (see [Setup](#setup))
3. Run `streamlit run app.py`
4. Click "Run Due Diligence Analysis" with the included sample contracts
5. Watch the agent autonomously chain through 5 analysis stages and produce a risk register

### For a PoC

The agent is designed to be modular. Each tool is an independent function that you can replace with real integrations:

- **`tool_parse_contract`** — currently uses PyMuPDF for PDF text extraction. For production, you can swap this with **OCI Document Understanding** for structured extraction, or use a **multimodal model** such as **Cohere Command A Vision** (`cohere.command-a-03-2025`) to handle scanned PDFs, handwritten documents, faxed contracts, and image-based files that standard text extraction cannot process. The multimodal approach sends the document page as an image input to the model, which can read and structure content regardless of whether it was digitally created or physically scanned.
- **`tool_extract_clauses`** — uses an LLM call with a detailed extraction prompt. For scanned or handwritten documents, the same multimodal vision approach applies here: pass document page images directly to a vision-capable model to extract clauses that OCR-based pipelines would miss or misread.
- **`tool_compare_to_market`** — currently uses hardcoded market baselines combined with LLM judgment. For production, replace the hardcoded baselines with a **web search tool** (the Responses API supports `web_search_preview` as a built-in tool) to fetch current market data, or implement a **RAG pipeline** over a corpus of template contracts and legal benchmarking databases. This makes the comparison dynamic and always up to date rather than static.
- **`tool_cross_reference_conflicts`** — sends all clause data to the model for conflict detection. For larger document sets, consider chunking and parallel processing.
- **`tool_generate_risk_register`** — synthesizes all findings into the final output. Customize the risk categories, severity thresholds, and output format to match your customer's internal risk framework.

### Customizing the Agent Behavior

The agent's decision-making is controlled by two things:

1. **`AGENT_INSTRUCTIONS`** (in `app.py`) — the system prompt that tells the model what workflow to follow and in what order to call tools.
2. **Individual tool `system_prompt` strings** inside each `tool_*` function — these control what each tool extracts, how it analyzes, and what format it returns.

Modify these prompts to adapt the agent to different industries or use cases without changing any code logic.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Streamlit UI                      │
│         Oracle Redwood Dark Theme                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│   ┌─────────────────────────────────────────────┐   │
│   │         OCI Responses API (Outer Agent)     │   │
│   │         Model: xai.grok-4.20-reasoning      │   │
│   │                                             |   │
│   └──────────────┬──────────────────────────────┘   │
│                  │                                  │
│     ┌────────────┼────────────┐                     │
│     ▼            ▼            ▼                     │
│  ┌──────┐  ┌──────────┐  ┌──────────┐               │
│  │Parse │  │ Extract  │  │ Compare  │               │
│  │Contract││ Clauses  │  │to Market │               │
│  │      │  │          │  │          │               │
│  │PyMuPDF│ │Inner LLM │  │Baselines │               │
│  │+ LLM │  │  Call    │  │+ LLM     │               │
│  └──────┘  └──────────┘  └──────────┘               │
│     │            │            │                     │
│     ▼            ▼            ▼                     │
│  ┌──────────────────────────────────┐               │
│  │     Cross-Reference Conflicts    │               │
│  │         (Inner LLM Call)         │               │
│  └──────────────┬───────────────────┘               │
│                 ▼                                   │
│  ┌──────────────────────────────────┐               │
│  │     Generate Risk Register       │               │
│  │         (Inner LLM Call)         │               │
│  └──────────────────────────────────┘               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## File Structure

```
legal-due-diligence-agent/
│
├── app.py                      # Main Streamlit application
│
├── requirements.txt             # Python dependencies
│
├── .env.example                 # Environment variable template
│
├── LICENSE                      
│
└── README.md                    # This file
```

---

## Setup

### Prerequisites

- Python 3.10 or higher
- An OCI tenancy with access to OCI Generative AI
- An OCI Generative AI **Project** (required for the Responses API)
- An OCI Generative AI **API Key** (generates a Bearer token for OpenAI SDK compatibility)

### Step 1: Create an OCI Generative AI Project

1. Log in to the [OCI Console](https://cloud.oracle.com)
2. Navigate to **Analytics & AI → Generative AI**
3. Click **Projects** in the left sidebar
4. Click **Create Project**
5. Give it a name (e.g., "Legal Due Diligence Agent") and select your compartment
6. Note the **Project OCID** — you will need this for `CHICAGO_PROJECT_OCID`

### Step 2: Create an OCI Generative AI API Key

1. In the Generative AI console, navigate to **API Keys**
2. Click **Create API Key**
3. Name your key and set an expiration
4. Copy the generated key value — this is your `OPENAI_API_KEY_CHICAGO`

### Step 3: Install and Run

```bash
# Clone the repository
git clone <repo-url>
cd legal-due-diligence-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and fill in your API key and project OCID:
#   OPENAI_API_KEY_CHICAGO=sk-your-api-key-here
#   CHICAGO_PROJECT_OCID=ocid1.generativeaiproject.oc1.us-chicago-1.your-project-ocid

# Run the app
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`.

### Changing the Model

The default model is `xai.grok-4.20-reasoning`. To use a different model, update the `MODEL` constant near the top of `app.py`:

```python
MODEL = "openai.gpt-oss-120b"          # OpenAI gpt-oss on OCI
MODEL = "xai.grok-4-1-fast-reasoning"  # Grok 4.1 fast
MODEL = "google.gemini-2.5-pro"        # Google Gemini 2.5 Pro
```

---

## Useful Links

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [QuickStart Guide for Building Agents](https://docs.oracle.com/en-us/iaas/Content/generative-ai/get-started-agents.htm)
- [OCI Responses API (oci-openai)](https://docs.oracle.com/en-us/iaas/Content/generative-ai/oci-openai.htm)
- [OCI Generative AI API Keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm)

---

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](./LICENSE) for more details.