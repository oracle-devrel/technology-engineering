# Compliance Audit Intelligence

A Streamlit demo that audits video recordings against documented Standard Operating Procedures using **NVIDIA Nemotron 3 Nano Omni 30B (Reasoning)**, deployed on OCI Generative AI as a Dedicated AI Cluster.

## Why this asset

Nemotron 3 Nano Omni's headline architectural claim is that a single 30B-A3B hybrid Mamba-Transformer MoE model handles all four input modalities natively - text, image, video, and audio - within one perception loop. A compliance audit forces every modality to matter:

- **Video** to see whether procedures are physically performed.
- **Audio** to hear what the operator said and when.
- **Document** to ground findings in the SOP text.
- **Reasoning** to map observed behaviour to specific clauses with timestamped evidence.

Pipeline alternatives (Whisper → VLM → LLM) lose context at each hop. A single model maintaining a shared multimodal context across the entire video is the differentiator the demo is designed to expose.

## What it does

1. Upload a video recording —> lab session, screen recording of a customer call, manufacturing line footage, training video, etc.
2. Provide the relevant SOP —> either as a PDF upload (text auto-extracted) or pasted directly.
3. Run the audit.

The model returns a structured compliance report containing:

- Overall verdict - compliant / non-compliant / conditional.
- Timestamped findings, each tied to a specific SOP clause.
- Severity ratings for violations - critical / major / minor.
- Visual and audio evidence supporting each finding.
- Actionable recommendations.


## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your DAC endpoint OCID and OpenAI-compat base URL
streamlit run app.py
```

OCI configuration (`~/.oci/config`) must contain the profile referenced in `OCI_CONFIG_PROFILE` (default `LONDON`). The OCI user principal must have inference permissions on the DAC endpoint.

## Configuration

All knobs live in `config.py`:

| Setting | Default | Purpose |
|---|---|---|
| `TEMPERATURE` | `0.2` | Low for deterministic audit reasoning |
| `MAX_TOKENS` | `8000` | Room for findings + recommendations |
| `MAX_VIDEO_SIZE_MB` | `100` | Inline base64 ceiling (tune up for OS path) |
| `SUPPORTED_VIDEO_TYPES` | mp4, webm, mov, mkv | |

Streamlit's upload ceiling is set to 200 MB in `.streamlit/config.toml` — raise if needed.

## Video transmission

Videos are sent inline as base64 data URIs:

```
data:video/mp4;base64,<encoded bytes>
```

For files larger than ~100 MB, base64 inflation pushes request size past practical inference limits. Fall back to OCI Object Storage with a Pre-Authenticated Request (PAR) URL. With the OpenAI-compat path, a plain HTTPS URL works directly:

```python
video_block = {"type": "video_url", "video_url": {"url": par_url}}
```

(The legacy `data:video/mp4;uri,<url>` form is OCI-native and not used on the OpenAI-compat path.)

## Files

- `app.py` — Streamlit UI and orchestration.
- `config.py` — environment + tunables.
- `prompts.py` — system prompt + audit prompt template.
- `schemas.py` — Pydantic models for the audit report.
- `utils.py` — video encoding, PDF extraction, JSON parsing.
- `.streamlit/config.toml` — upload limit + theme.

## Notes on the model

- DAC endpoint OCID is passed as the `model` parameter to `chat.completions.create`.
- Reasoning: the model has a 16K thinking budget and reasons before producing the final JSON. The parser strips any reasoning prefix automatically.
- Context: 256K tokens — comfortably accommodates long SOPs alongside multi-minute video.

## Useful Links / License

- OCI Generative AI documentation: https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm
- OCI Generative AI OpenAI-compatible API: https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-api.htm
- OCI architecture and icon reference: https://docs.oracle.com/en/solutions/

Licensed under the Universal Permissive License v 1.0 — see `LICENSE`.