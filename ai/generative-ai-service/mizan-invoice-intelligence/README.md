# OCI Enterprise AI — Mizan Invoice Intelligence

Mizan turns multilingual invoices into validated, reviewable records with **OCI Generative AI**. The Streamlit experience combines structured extraction, deterministic finance checks, page-level evidence, targeted verification, typed human review, and audit-ready exports behind a simple four-step flow.

*Author:* Ali Ottoman

## When to Use This Asset

### The Challenge

Invoices arrive as digital PDFs, scans, phone photos, dense tables, and mixed-language documents. A plausible model response is not enough: finance teams need the numbers reconciled, important values grounded in the source, and every human correction recorded before data is posted downstream.

### Who Is This For?

- Finance and accounts-payable teams automating invoice capture and review.
- Banks and trade-finance teams reading commercial invoices and payment references.
- Government and regulated organizations evaluating an OCI-hosted model route.
- System integrators building an invoice-to-ERP proof of concept.

### When to Use It

- Invoice layouts vary and template-specific rules are too brittle.
- Line items, tax, totals, and balances must reconcile before approval.
- Arabic, English, or mixed-language documents need one normalized contract.
- Reviewers need page-level evidence and an auditable decision trail.
- A reusable demonstration is needed before live OCI credentials are configured.

### Key Capabilities

- Four-stage journey: **Set up → Read → Check → Review**.
- Imported multimodal model on an OCI Dedicated AI Cluster (DAC), or an on-demand model through the OCI Responses API.
- Selectable on-demand models: Gemini 2.5 Pro and Grok 4.3.
- Editable required-field policy and up to 12 custom fields without code changes.
- Strict Pydantic contract with JSON Schema requests where supported.
- Deterministic validation for identifiers, dates, line math, tax, totals, balance, IBAN, SWIFT/BIC, confidence, evidence, and duplicates.
- Targeted re-reading of model-checkable exceptions; revisions are never silently accepted.
- Typed corrections, revalidation, change history, named approval, and approval invalidation after later edits.
- JSON, protected CSV, and formatted multi-sheet Excel downloads.
- Clearly labelled synthetic sample requiring no credentials.

## How to Use This Asset

### For a Quick Demo

1. **Set up** — choose **Imported DAC** or **On-demand**, then use the synthetic invoice or upload documents. Select the required fields and add any custom fields.
2. **Read** — choose **Analyze invoice**. Mizan renders and normalizes each page, then calls the selected extraction route.
3. **Check** — deterministic rules reconcile identifiers, line items, tax, totals, confidence, and page evidence. Optional targeted verification re-reads only relevant exceptions.
4. **Review** — compare the source with the typed record, save corrections, inspect exceptions, record a decision, and download the audit output.

The bundled sample replays a recorded two-pass extraction. When credentials are configured, the same sample can be analyzed live with the selected route.

### For a PoC

- Extend the AP or ERP contract in `src/models.py` while preserving the validation and export boundaries.
- Add local VAT formats, purchase-order tolerances, supplier policies, or three-way matching in `src/validators.py`.
- Map approved output to Oracle Fusion Cloud ERP, NetSuite, SAP, OCI Queue, or an approval API.
- Add OCI Document Understanding before model inference when polygon coordinates or service-provided OCR confidence are required.
- Benchmark representative invoices and negative controls using field accuracy, line-item recall, arithmetic accuracy, evidence-page accuracy, latency, and cost.
- Add persistence, access control, observability, queueing, and retry policy at the deployment layer when moving beyond a PoC.

### Customizing

- `config.py` owns supported model choices, endpoint settings, document limits, and validation thresholds.
- `src/models.py` defines the canonical invoice and audit contract.
- `src/prompts.py` controls source-grounded extraction and targeted re-reading.
- `src/validators.py` contains deterministic business checks and the required-field policy.
- `src/review.py` owns correction, revalidation, duplicate, and approval transitions.
- `src/review_ui.py` contains the editable review workspace and export controls.
- `src/ui.py` contains the Mizan visual system and reusable UI helpers.

## Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│ Streamlit UI                                                    │
│ Set up → Read → Check → Review, approve, and export            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ PDF or image, held in memory
                                ▼
                    ┌────────────────────────┐
                    │ PyMuPDF + Pillow       │
                    │ page images + PDF text │
                    └───────────┬────────────┘
                                │ selected route
                  ┌─────────────┴──────────────┐
                  ▼                            ▼
       ┌──────────────────────┐    ┌───────────────────────────┐
       │ Imported model DAC   │    │ OCI Responses API        │
       │ dedicated endpoint   │    │ Gemini 2.5 Pro / Grok 4.3│
       └──────────┬───────────┘    └────────────┬──────────────┘
                  └─────────────┬───────────────┘
                                │ candidate structured record
                                ▼
                  ┌──────────────────────────────┐
                  │ Pydantic contract + checks  │
                  │ fields · math · evidence    │
                  └─────────────┬────────────────┘
                                │ selected exceptions
                                ├──────────────▶ targeted re-read
                                ▼
                  ┌──────────────────────────────┐
                  │ Typed review + audit trail   │
                  │ named decision + export     │
                  └─────────────┬────────────────┘
                                ▼
                         JSON · CSV · Excel
```

The imported adapter uses the OCI Python SDK with `DedicatedServingMode.endpoint_id`; the configured endpoint selects the deployed model. The on-demand adapter uses the OpenAI SDK against the OCI Responses API. Both routes receive numbered page images, run at temperature zero, and pass results through the same typed validation and review layer.

Embedded PDF text is auxiliary evidence. The model still inspects the rendered page, and unresolved conflicts remain visible for reviewer confirmation.

## File Structure

```text
mizan-invoice-intelligence/
├── app.py                 # Streamlit workflow
├── config.py              # OCI routes, models, and limits
├── requirements.txt
├── README.md
├── .env.example           # Placeholder configuration only
├── .gitignore
├── sample_invoice.pdf     # Clearly marked fictional demo invoice
└── src/
    ├── __init__.py
    ├── documents.py       # In-memory PDF and image normalization
    ├── models.py          # Typed invoice and audit contracts
    ├── paths.py           # Nested-field path helpers
    ├── prompts.py         # Extraction and verification prompts
    ├── providers.py       # Imported DAC and Responses adapters
    ├── extractor.py       # Shared extraction workflow
    ├── validators.py      # Deterministic checks
    ├── review.py          # Review and approval state transitions
    ├── review_ui.py       # Typed correction and export workspace
    ├── exporters.py       # JSON, CSV, and Excel outputs
    ├── sample_data.py     # Recorded guided-sample result
    └── ui.py              # Theme and escaped HTML helpers
```

## Setup

### Prerequisites

- Python 3.10 or later.
- An OCI tenancy and API-signing profile for the imported DAC route.
- An active imported-model endpoint for the DAC route.
- An OCI Generative AI project in Chicago for the on-demand route.
- Appropriate OCI IAM policies and service limits.

PyMuPDF renders PDFs directly; Poppler is not required by the application.

### Step 1 — Prepare an Inference Route

#### Imported DAC

1. In the OCI Console, open **Generative AI → Imported models**.
2. Import a currently supported multimodal model. The sample configuration uses `Qwen/Qwen3.6-35B-A3B`.
3. Create a compatible hosting DAC and an endpoint in `us-chicago-1`.
4. Wait until the model, cluster, and endpoint are active.
5. Copy the endpoint identifier into your local `.env` file.

The endpoint selects the actual deployed model. The model ID and label in `config.py` are display metadata and should always match that endpoint. Recheck the OCI compatibility table, available shapes, quota, capacity, and pricing before deployment.

#### On-demand Responses API

1. In Chicago, create or open an OCI Generative AI project.
2. Create a Generative AI API key for evaluation, or configure supported OCI IAM authentication.
3. Add the project identifier and authentication values to your local `.env` file.
4. Select **Gemini 2.5 Pro** or **Grok 4.3** in the application.

No dedicated endpoint or DAC is required for the on-demand route.

### Step 2 — Configure Credentials

```bash
cp .env.example .env
```

Replace the placeholders in `.env` with values from your own tenancy. Do not commit the file.

```dotenv
OCI_CONFIG_PROFILE=DEFAULT
OCI_REGION=us-chicago-1
INVOICE_INFERENCE_MODE=dac

OCI_COMPARTMENT_ID=<YOUR_COMPARTMENT_OCID_HERE>
INVOICE_DAC_ENDPOINT_OCID=<YOUR_GENERATIVE_AI_ENDPOINT_OCID_HERE>
INVOICE_DAC_MODEL_ID=Qwen/Qwen3.6-35B-A3B
INVOICE_DAC_MODEL_LABEL=Qwen 3.6 35B A3B

CHICAGO_PROJECT_OCID=<YOUR_GENERATIVE_AI_PROJECT_OCID_HERE>
OPENAI_API_KEY_CHICAGO=<YOUR_GENERATIVE_AI_API_KEY_HERE>
INVOICE_ON_DEMAND_MODEL_ID=google.gemini-2.5-pro
```

`OPENAI_API_KEY_CHICAGO` is the simplest option for evaluation. When it is omitted, the application can use `oci-genai-auth` with `OCI_CONFIG_PROFILE`. The UI controls the inference route and supported on-demand model for each run.

### Step 3 — Install and Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`. The guided sample works immediately; uploaded documents require the selected live route to be configured.

### Model Alternatives

| Route | Configured option | Guidance |
|---|---|---|
| Imported DAC | `Qwen/Qwen3.6-35B-A3B` | Documented multimodal baseline; verify the current compatibility table and benchmark your invoices. |
| On-demand | `google.gemini-2.5-pro` | Default document-understanding option. |
| On-demand | `xai.grok-4.3` | Selectable image and structured-output alternative. |

Model availability changes. Validate the exact model ID, region, and API capabilities in the current OCI documentation before deployment.

### Security and Data Handling

- The application processes uploads in memory and does not write uploaded documents to disk.
- On-demand requests set `store=False`.
- `.env`, OCI configuration folders, private keys, and security tokens are excluded by `.gitignore`.
- Never commit credentials, tenancy identifiers, customer documents, or generated audit exports.
- The bundled invoice is synthetic; every organization, identifier, bank, and transaction is fictional.
- Confirm the processing boundary and obtain the required approval before sending sensitive data to any model route. The imported DAC runs on the configured OCI endpoint. On-demand models are accessed through OCI but may be processed in the model provider's external environment.

## Useful Links

- [OCI Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Responses API](https://docs.oracle.com/en-us/iaas/Content/generative-ai/responses-api.htm)
- [Using an OCI Generative AI project](https://docs.oracle.com/en-us/iaas/Content/generative-ai/use-project.htm)
- [OCI Generative AI API keys](https://docs.oracle.com/en-us/iaas/Content/generative-ai/api-keys.htm)
- [Models by region](https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-endpoint-regions.htm)
- [Compatible imported Alibaba models](https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-alibaba-models.htm)
- [Import a model from Hugging Face](https://docs.oracle.com/en-us/iaas/Content/generative-ai/import-model-from-hugging-face.htm)
- [Create a hosting Dedicated AI Cluster](https://docs.oracle.com/en-us/iaas/Content/generative-ai/create-ai-cluster-hosting.htm)
- [Create an imported-model endpoint](https://docs.oracle.com/en-us/iaas/Content/generative-ai/create-endpoint.htm)
- [Generative AI IAM policy examples](https://docs.oracle.com/en-us/iaas/Content/generative-ai/model-permissions.htm)
- [Generative AI data handling](https://docs.oracle.com/en-us/iaas/Content/generative-ai/data-handling.htm)

## License

Copyright (c) 2026 Oracle and/or its affiliates.

The asset code is licensed under the Universal Permissive License (UPL), Version 1.0. See [UPL 1.0](https://oss.oracle.com/licenses/upl/). Imported model weights and on-demand services remain subject to their provider licences and terms.


