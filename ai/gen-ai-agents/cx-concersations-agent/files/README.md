# CX Conversations Analyzer Agent

The **CX Conversations Analyzer** is an AI agent that listens to your call center recordings and tells you what happened — automatically, at scale.

Drop in one audio file or a full batch. The agent transcribes each call using **OCI AI Speech**, separates the two speakers, and then uses **OCI Generative AI** with OpenAI GPT-OSS models to extract:

- **Why the customer called** — the explicit call reason
- **Whether the issue was resolved** — yes or no
- **What information the agent requested** during the call
- **A concise summary** of the interaction
- **How the customer felt** — a sentiment score from 1 (very negative) to 10 (very positive)

When processing a batch, the agent automatically groups calls into topic categories and produces an aggregated report with resolution rates, sentiment averages, and key operational insights across all calls.

**Example dataset:** [Gridspace-Stanford Harper Valley](https://github.com/cricketclub/gridspace-stanford-harper-valley)

---

## About the Example Dataset

If you want to test the agent with the provided example dataset instead of your own recordings, two options are available:

- Use the pre-selected samples in the `selected_samples/` folder.
- Use the preparation notebooks:
  - `1_check_dataset.ipynb` — downloads the dataset, runs statistics, and selects samples.
  - `2_prepare_files.ipynb` — generates a `dataset/` folder with mixed audio (agent + caller in a single file).

---

## Project Structure

```
files/
├── app.py                        # Streamlit UI entry point
├── requirements.txt              # Python dependencies
├── backend/
│   └── prompts.py                # All LLM prompt strings
├── frontend/
│   ├── navbar.py                 # Sidebar layout and controls
│   ├── display_widgets.py        # Transcript and summary rendering
│   └── styles.css                # Custom CSS
└── cx_tools/                     # Reusable tools package
    ├── __init__.py
    ├── config.py                 # OCIConfig dataclass
    ├── llm_factory.py            # ChatOCIGenAI factory
    ├── speech_tools.py           # OCI AI Speech pipeline + tool
    ├── genai_tools.py            # Sentiment / summary / intent / topic tools
    └── agent.py                  # AI agent
```

---

## How to Run the Agent

### Prerequisites

- Python 3.13.5 or later
- An OCI account with access to:
  - OCI Generative AI Service (eu-frankfurt-1 or another supported region)
  - OCI AI Speech
  - OCI Object Storage bucket

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure OCI Credentials

Create a `.env` file in the `files/` directory and fill in your values:


```ini
# OCI identity
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..xxxxx
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT

# Generative AI endpoint — change to match your region
OCI_GENAI_ENDPOINT=https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com

# Object Storage — required by OCI AI Speech for audio upload and transcript output
OCI_BUCKET_NS=<your-namespace>
OCI_BUCKET_NAME=<your-bucket-name>
OCI_BUCKET_PREFIX=audio/
OCI_SPEECH_OUTPUT_PREFIX=transcripts/
```

The OCI SDK reads authentication from the standard `~/.oci/config` file. See [OCI SDK authentication methods](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm) for setup instructions.

### 3. Start the Agent

```bash
cd files
streamlit run app.py
```

---

## What the Agent Does

### Per-Call Analysis

Upload one or more audio files via the sidebar and select a model. For each file, the agent:

1. Uploads the audio to OCI Object Storage.
2. Submits a transcription job to OCI AI Speech with speaker diarization (2 speakers).
3. Passes the diarized transcript to OCI Generative AI and extracts a structured summary:

| Field | Description |
|---|---|
| `call_reason` | Why the customer called |
| `issue_solved` | Yes / No |
| `info_asked` | Information the agent requested |
| `summary` | 1–2 sentence description of the interaction |
| `sentiment_score` | 1 (very negative) to 10 (very positive) |

### Batch Analysis

After processing individual calls, switch to **Batch overview** in the sidebar. The agent runs two additional passes over the full batch:

- **Categorization** — automatically groups calls into up to 15 topic categories (e.g. Billing, Card Replacement, Technical Support).
- **Report generation** — produces per-category aggregates: average sentiment, issue resolution rate, highest/lowest sentiment call, and key insights.

### LLM Call Budget per Session

| Action | LLM calls |
|---|---|
| Run with N files | N (one summarization per file) |
| Open Batch overview | 2 (categorization + report) |
| **Total for N files** | **N + 2** |

---

## Deploying the Agent

The `cx_tools` package is designed to be reused across multiple deployment targets:

| Target | Entry point | Description |
|---|---|---|
| Streamlit UI | `app.py` | Interactive per-call and batch analysis |
| Full agent | `cx_tools.build_cx_agent(config)` | AI agent with all tools registered |
| Individual tools | `cx_tools.build_tool_registry(config)` | Register each `@tool` separately |

The agent tools available for Hub registration:

| Tool | What it does |
|---|---|
| `transcribe_audio` | Transcribes audio with speaker diarization |
| `analyze_sentiment` | Classifies sentiment with confidence score |
| `summarize_conversation` | Produces a 3–5 sentence summary |
| `extract_intent` | Identifies primary and secondary customer intents |
| `classify_topic` | Classifies into a configurable topic taxonomy |
| `analyze_conversation` | Runs all of the above in a single LLM call |

---

## Useful Documentation

- [OCI Generative AI documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI AI Speech documentation](https://docs.oracle.com/en-us/iaas/Content/speech/home.htm)
- [OCI Python SDK documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- [LangChain OCI GenAI integration](https://docs.langchain.com/oss/python/integrations/chat/oci_generative_ai)

---

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](../LICENSE) for more details.