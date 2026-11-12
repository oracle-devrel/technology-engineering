# Clinical Lab Order Assistant (LabSense)

A physician-facing agent that reviews a requested set of blood tests before they are ordered. It reads the patient's record, flags tests whose last result is still within its validity window, shows the cost of what was requested against what is actually needed, and writes the visit back to the record so the next consultation starts informed. The agent runs on an **imported model hosted on a dedicated OCI Generative AI endpoint**, using native function calling through the OpenAI-compatible Chat Completions route.

The user interface is bilingual (English and Arabic, with right-to-left layout) and the model answers in the language of the physician's last message.

Reviewed: 14.10.2026

![Clinical Lab Order Assistant: consultation with the order board showing requested versus recommended tests](files/docs/screenshot.png)

> All patients, results, clinics and prices are fictional. Validity windows are illustrative hospital policy, not clinical guidance.

# When to use this asset?

Use this asset when you need to show or build:

- **Agentic function calling on an imported model** running on a dedicated OCI Generative AI endpoint. Six tools, multi-step tool loops, streamed reasoning with selectable effort, all visible as inspectable steps in the chat.
- **Redundant lab-test avoidance** or any similar "check before you order" workflow where a deterministic policy engine decides and the model explains, handles exceptions and talks to the user.
- **Image understanding on a dedicated endpoint**: a photo or scan of an external lab report is transcribed by the model's vision and its results are imported into the record.
- **Memory across sessions**: orders and visit summaries are persisted per patient and read back on the next visit.
- **Cost justification UI**: requested versus recommended cost, cost by status, cumulative savings per patient.
- **Bilingual (Arabic/English) assistant UI** built with Next.js and the Vercel AI SDK.

The asset is a complete, runnable demo and a reference implementation for healthcare and similar regulated scenarios where credentials stay server-side and the model never does the arithmetic.

# How to use this asset?

## Architecture

```
browser ──► Next.js 16 (web/)            ──► FastAPI gateway (gateway/)        ──► OCI Generative AI
            Vercel AI SDK ToolLoopAgent       /v1/chat/completions  signed proxy      dedicated endpoint, imported model
            six tools, streaming UI           /patients /orders /results            native chat for vision
            order board (Recharts)            SQLite patient record (data/labsense.db)
```

- **Tools** (`files/web/src/lib/agent.ts`): `getPatientRecord`, `searchTestCatalog`, `evaluateOrder`, `placeOrder`, `readReport`, `importResults`. The model never does date arithmetic. `gateway/rules.py` decides needed / still valid / expiring from `data/catalog.json`; the model explains and handles exceptions.
- **Memory**: `gateway/records.py` keeps one JSON record per patient in SQLite. `placeOrder` appends the visit and marks ordered tests as pending results.
- **Reports**: images go straight to the model's vision; PDFs use local text extraction with vision only for scanned pages.
- **Why Chat Completions and not the Responses API**: OCI's Responses API rejects imported models. Function calling through Chat Completions is the supported surface for dedicated endpoints.

An architecture slide is included in `files/docs/labsense-architecture.pptx`.

## Prerequisites

- An OCI tenancy with a **dedicated AI cluster hosting an imported model** that supports function calling and (optionally) vision. The endpoint must answer on the OpenAI-compatible route (`/20231130/actions/v1/chat/completions`).
- An OCI CLI profile in `~/.oci/config` with permission to call the endpoint.
- Python 3.11+ with [`uv`](https://docs.astral.sh/uv/), and Node.js 20+.

## Run it

```bash
cd files
cp .env.example .env            # fill in OCI_ENDPOINT_ID and OCI_COMPARTMENT_ID
uv sync
uv run python scripts/make_sample_report.py
cd web && npm install && npm run build && cd ..
uv run python scripts/serve.py  # gateway :8001 + web :3000, both on loopback
```

Open <http://localhost:3000>. `Ctrl+C` stops both processes.

Verify your endpoint first if unsure:

```bash
uv run python scripts/probe_endpoint.py   # chat, streaming, tools, vision → data/endpoint-capabilities.json
```

## Suggested storyline (about ten minutes)

1. **Fatimah Al-Harbi** (returning, diabetic). Use starter 1. The agent greets her by her last visit, evaluates seven requested tests, and flags five as still valid. The order board shows the requested cost against the recommended cost.
2. Starter 2: she reports palpitations. The agent agrees to repeat the blood count on clinical grounds and says why. Policy guides, the physician decides.
3. Starter 3: confirm. The receipt shows this visit's saving and her lifetime saving. Open the *Visits* tab.
4. **Mohammed Al-Qahtani** (check-up). Starter 1: everything is needed, his results are old. Starter 2 loads the fictional external lab report image. The model reads it with vision, imports the results, re-evaluates, and most tests drop out.
5. **Khalid Al-Dossari** (new patient): nothing on file, nothing flagged. The contrast makes the point.
6. Switch to Arabic and ask a follow-up for any patient.
7. Press the reset button at the bottom of the patient rail to restore the seed data.

## Adapting for a customer

- Replace `data/catalog.json` with the hospital's own test list, validity policy and tariff.
- Replace `data/patients.json` with de-identified or synthetic records in the same shape.
- The system prompt in `web/src/lib/agent.ts` holds the clinical-exception rules; adjust the tone and the escalation questions there.
- Brand tokens live at the top of `web/src/app/globals.css`.

See `files/README.md` for development commands, smoke tests and lint.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
