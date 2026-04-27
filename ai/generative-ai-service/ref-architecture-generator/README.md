# OCI Architecture Diagram Generator

A Streamlit demo that turns a natural-language description of an Oracle Cloud Infrastructure workload into a production-quality reference architecture diagram. The user describes the components, zones, and numbered data-flow steps; the app prepends a strict OCI visual style guide and sends the combined prompt to one of three image models on OCI Generative AI: Qwen-Image-Edit on a Dedicated AI Cluster, Grok Imagine. An iterative refinement loop lets the user nudge successive regenerations without losing history, and Qwen runs in style-transfer mode against an uploaded reference architecture image.

## When to Use This Asset?

Use this asset to show enterprise and government clients how OCI Generative AI accelerates solution-architecture work, converting an analyst's written description of a system into a visual reference diagram in seconds with a refinement loop that mirrors the back-and-forth of real architecture-review sessions. It is particularly relevant for:

- Pre-sales and solution-engineering teams producing first-draft reference architectures during workshops
- Internal sales-enablement sessions where reps need to communicate the shape of an OCI solution to a non-technical audience
- Side-by-side comparison of three image model families (Qwen on DAC, Grok Imagine) on the same enterprise prompt
- Demonstrating how a detailed style guide constrains image output to a specific corporate visual language — OCI icon set, compartment, VCN, and subnet conventions, numbered flow steps, monochrome icons with burnt-orange dashed boundaries
- Showing how Qwen-Image-Edit on a Dedicated AI Cluster can act as a style-transfer engine, inheriting the visual language of an existing reference diagram and rendering new ones in the same house style

## How to Use This Asset?

1. Launch the app with `streamlit run app.py`.
2. In the sidebar, choose the image model (Qwen DAC, or Grok Imagine) and the output aspect (landscape recommended for OCI diagrams).
3. On first load, click one of the sample chips (RAG Chatbot, Document Pipeline, Multi-Region HA) to pre-fill the description, or write your own. Name every component, the zones they sit in (On Premises, OCI Region, Availability Domain, LZ Compartment, VCN, Subnet, Oracle Services Network), and number each step of the data flow.
4. If using Qwen, upload a reference architecture image in the sidebar — Qwen runs in image-edit mode and inherits its visual style from the reference.
5. Click **Generate**. The app prepends the OCI style guide to the description and calls the selected model.
6. Once an image is rendered, a second text area appears for **refinement** instructions. Enter a tweak (move a component, add a step, fix labelling) and click **Regenerate** — the prompt is rebuilt with style guide, description, and refinement.
7. Every iteration is kept in session history with its model, timestamp, and refinement note. Download any generation as PNG.
8. Click **Reset session** in the sidebar to clear history and start over.

## File Structure

```
oci-architecture-generator/
├── app.py                    # Streamlit UI, session state, generation dispatch
├── clients.py                # OCI Generative AI clients (openai SDK)
├── prompts.py                # OCI visual style guide prepended to every prompt
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml           # Light theme — Anthropic-inspired warm palette
├── LICENSE
└── README.md
```

## Setup

Prerequisites: Python 3.11 or later, an OCI tenancy with Generative AI access in the Chicago region, an OCI Generative AI API key and project OCID, and a Qwen-Image-Edit model deployed on a Dedicated AI Cluster if Qwen is needed.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your tenancy values:

- `OPENAI_API_KEY_CHICAGO` — OCI Generative AI API key (begins with `sk-…`)
- `CHICAGO_PROJECT_OCID` — OCI Generative AI project OCID
- `OCI_COMPARTMENT_ID` — compartment OCID with Generative AI access
- `OCI_GENAI_BASE` — OCI Generative AI host (e.g. `https://inference.generativeai.us-chicago-1.oci.oraclecloud.com`)
- `OCI_QWEN_DAC_ENDPOINT_OCID` — OCID of the Qwen-Image-Edit Dedicated AI Cluster endpoint, used as the model identifier
- `OCI_CONFIG_PROFILE` — display label for the sidebar status panel

Run:

```bash
streamlit run app.py
```

## Useful Links / License

- OCI Generative AI documentation: https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm
- OCI Generative AI OpenAI-compatible API: https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-api.htm
- OCI architecture and icon reference: https://docs.oracle.com/en/solutions/

Licensed under the Universal Permissive License v 1.0 — see `LICENSE`.