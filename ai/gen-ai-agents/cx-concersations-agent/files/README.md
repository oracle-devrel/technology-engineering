# CX Conversations Analysis

Transcribes call center audio using **OCI AI Speech** and extracts insights using **OCI Generative AI** with OpenAI GPT-OSS models. Built with Streamlit and LangChain.

**Example dataset:** [Gridspace-Stanford Harper Valley](https://github.com/cricketclub/gridspace-stanford-harper-valley)

---

## About the Example Dataset

If you want to use the provided example dataset instead of your own recordings, two options are available:

- Use the pre-selected samples in the `selected_samples/` folder.
- Use the preparation notebooks:
  - `1_check_dataset.ipynb` — downloads the dataset, runs statistics, and selects samples.
  - `2_prepare_files.ipynb` — generates a `dataset/` folder with mixed audio (agent + caller in a single file).

---

## Project Structure

```
files/
├── app.py                        # Streamlit UI entry point
├── backend/
│   └── prompts.py                # All LLM prompt strings
├── frontend/
│   ├── navbar.py                 # Sidebar layout and controls
│   ├── display_widgets.py        # Transcript and summary rendering
│   └── styles.css                # Custom CSS
└── cx_tools/                     # Reusable LangChain tools package
    ├── __init__.py
    ├── config.py                 # OCIConfig dataclass
    ├── llm_factory.py            # ChatOCIGenAI factory
    ├── speech_tools.py           # OCI AI Speech pipeline + LangChain tool
    ├── genai_tools.py            # Sentiment / summary / intent / topic tools
    └── agent.py                  # LangGraph agent (OCI Agents Hub entry point)
```

---

## How to Run the App

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

```bash
cp .env.example .env
```

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

### 3. Run the App

```bash
cd files
streamlit run app.py
```

---

## How It Works

### Per-Call Processing

1. **Upload** one or more audio files (`.wav`, `.mp3`, `.m4a`) via the sidebar.
2. **Select a model** — OpenAI GPT-OSS 120b or GPT-OSS 20b.
3. Click **Run**. For each file:
   - The audio is uploaded to OCI Object Storage.
   - OCI AI Speech creates a transcription job with speaker diarization (2 speakers).
   - The transcript is passed to OCI Generative AI to produce a structured JSON summary:
     - `call_reason` — why the customer called
     - `issue_solved` — Yes / No
     - `info_asked` — information requested by the agent
     - `summary` — 1–2 sentence description
     - `sentiment_score` — 1 (very negative) to 10 (very positive)

### Batch Overview

After processing, switch to **Batch overview** in the sidebar to run two additional LLM calls over the full batch:

- **Categorization** — groups calls into up to 15 auto-generated topic categories (e.g. Billing, Card Replacement, Technical Support).
- **Report generation** — aggregates per-category metrics: average sentiment, issue resolution rate, highest/lowest sentiment call, and key insights.

### LLM Call Budget per Session

| Action | LLM calls |
|---|---|
| Run with N files | N (one summarization per file) |
| Open Batch overview | 2 (categorization + report) |
| **Total for N files** | **N + 2** |

---

## Architecture

The `cx_tools` package is designed to be reused across multiple deployment targets:

| Target | Entry point | Description |
|---|---|---|
| Streamlit UI | `app.py` | Direct chain calls via `_invoke_chain()` |
| OCI Agents Hub (full agent) | `cx_tools.build_cx_agent(config)` | LangGraph agent with all tools |
| OCI Agents Hub (individual tools) | `cx_tools.build_tool_registry(config)` | Register each `@tool` separately |

The `cx_tools/agent.py` module uses the LangChain 1.0 `create_agent()` API (replacing the deprecated `AgentExecutor` + `create_tool_calling_agent`). The available tools are:

- `transcribe_audio` — OCI AI Speech transcription with diarization
- `analyze_sentiment` — sentiment classification
- `summarize_conversation` — 3–5 sentence summary
- `extract_intent` — primary and secondary customer intents
- `classify_topic` — topic classification into a configurable taxonomy
- `analyze_conversation` — all of the above in a single LLM call (token-efficient)

---

## Useful Documentation

- [OCI Generative AI documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI AI Speech documentation](https://docs.oracle.com/en-us/iaas/Content/speech/home.htm)
- [OCI Python SDK documentation](https://docs.oracle.com/en-us/iaas/tools/python/latest/)
- [LangChain OCI GenAI integration](https://docs.langchain.com/oss/python/integrations/chat/oci_generative_ai)

---

## Contributing

Contributions are welcome. Please fork the repository and submit a pull request with your changes.

---

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](../LICENSE) for more details.