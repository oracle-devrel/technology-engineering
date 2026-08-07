# LiteLLM Gateway for OCI Generative AI — Developer Guide

The gateway is a [LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy) configured for OCI. Everything lives in `config/config.yaml`; the asset is organized in four stages that layer on top of each other — start with Stage 1 and enable the rest as you need them.

| Stage | Capability | Where |
|-------|-----------|-------|
| 1 | Unified OpenAI-compatible endpoint + virtual API keys | `model_list`, `general_settings` |
| 2 | Automatic complexity-based routing (`model="auto"`) | `auto` entry + `router_settings` |
| 3 | OCI Guardrails (moderation, PII, prompt injection) | `guardrails:` + `guardrails/oci_guardrails.py` |
| 4 | Observability for agentic workflows (Langfuse) | `litellm_settings.callbacks` |

## Prerequisites

- An OCI tenancy with Generative AI access and an API signing key ([setup docs](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm))
- Docker (recommended) or Python 3.11+
- Optional: a Dedicated AI Cluster hosting an imported model, keys for external providers, Langfuse keys

## Quick start (Docker)

```bash
cp .env.example .env   # fill in tenancy OCIDs, fingerprint, key path
docker compose up --build
```

This starts the gateway on `http://localhost:4000` plus a Postgres instance for virtual keys and spend tracking. Smoke test:

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "grok-4-fast", "messages": [{"role": "user", "content": "hello"}]}'
```

The LiteLLM admin UI is at `http://localhost:4000/ui` (log in with the master key).

### Running without Docker

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
set -a; source .env; set +a
litellm --config config/config.yaml --port 4000
```

Without Postgres, comment out `database_url` in `general_settings` — the gateway still works with the master key, you just lose virtual keys and spend tracking.

## Stage 1 — Unified endpoint and virtual keys

`model_list` exposes three kinds of models behind identical OpenAI semantics:

1. **OCI on-demand models** (`oci/xai.grok-4`, `oci/meta.llama-4-scout...`) through LiteLLM's native OCI provider, signed with your API key.
2. **Imported models on a Dedicated AI Cluster.** OCI serves these behind its OpenAI-compatible endpoint (`.../20231130/actions/v1`), authenticated with a plain OCI GenAI API key (`sk-...`) where the *model name is the DAC endpoint OCID*. The `qwen3-dac` entry shows the pattern — swap in your own endpoint OCID via `OCI_DAC_MODEL`. Run `examples/03_dac_imported_model.py` to see both the gateway route and the direct call.
3. **External providers** (OpenAI, Anthropic) — uncomment the entries and set keys.

Mint a virtual key for a team (works for **all** models, with budget and rate limits):

```bash
curl -X POST http://localhost:4000/key/generate \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"key_alias": "team-alpha", "max_budget": 50.0, "rpm_limit": 100, "models": ["auto", "grok-4-fast", "llama-4-scout", "qwen3-dac"]}'
```

Try it: `python examples/01_basic_chat.py`

## Stage 2 — Automatic routing

Applications call `model="auto"`. The complexity router (LiteLLM ≥ 1.94) scores each request — token count, code presence, reasoning markers, multi-step patterns — in sub-millisecond time and routes to the tier configured in the `auto` entry:

| Tier | Routed to | Typical request |
|------|-----------|-----------------|
| SIMPLE | `llama-4-scout` | short factual questions |
| MEDIUM | `grok-4-fast` | everyday tasks |
| COMPLEX | `grok-4` | long, multi-part, code-heavy |
| REASONING | `grok-4-fast-reasoning` | step-by-step logic |

The serving model is returned in the `x-litellm-model` response header. Requests can also *constrain* routing with tags (`enable_tag_filtering`), e.g. `tags: ["oci"]` to guarantee data never leaves OCI even when external providers are configured.

Try it: `python examples/02_auto_routing.py`

## Stage 3 — OCI Guardrails

`guardrails/oci_guardrails.py` wraps the OCI `apply_guardrails` API as a LiteLLM `CustomGuardrail`. Because it runs in the gateway, it protects **every** model — including external providers OCI Guardrails could not otherwise see.

- **PII** (`EMAIL`, `TELEPHONE_NUMBER`, `ADDRESS`, `PERSON`) → masked to `[EMAIL_REDACTED]` etc. before the model sees the prompt
- **Prompt injection** → HTTP 400
- **Content moderation** → HTTP 400
- `oci-guardrails-output` (post_call) applies the same checks to model *responses*

Opt in per request:

```python
client.chat.completions.create(
    model="grok-4-fast",
    messages=[...],
    extra_body={"guardrails": ["oci-guardrails"]},
)
```

or set `default_on: true` in `config.yaml` to enforce for all traffic. Thresholds, PII types and actions (`block` / `mask` / `log`) are configured per guardrail in `config.yaml`.

Try it: `python examples/04_guardrails.py`

## Stage 4 — Observability for agentic workflows

Three options, in increasing order of effort — pick the first one that satisfies you:

1. **Built-in (already on).** With Postgres, LiteLLM records every request: model, tokens, cost, latency, virtual key. The admin UI at `/ui` shows spend per key/team/model. Good enough for cost governance; no per-trace view of agent runs.
2. **Langfuse Cloud (recommended for agent traces).** Set `LANGFUSE_PUBLIC_KEY`/`LANGFUSE_SECRET_KEY` in `.env` and uncomment `callbacks: ["langfuse_otel"]` in `config.yaml`. Multi-step agent runs appear as single traces with nested LLM calls, tool calls, cost and latency. Zero client-side code — the gateway reports server-side; clients may pass `metadata` (trace name, user id, tags) to group calls.
3. **Self-hosted Langfuse v3.** Only if data residency requires it: it needs its own stack (Postgres, ClickHouse, Redis, MinIO) — deliberately **not** bundled in this compose file. Deploy it separately (e.g. on OKE from Langfuse's charts) and point `LANGFUSE_HOST` at it.

Try it: `python examples/05_agentic_observability.py`

## Playground UI

Open `ui/playground.html` in a browser (no build, no dependencies): connect with the gateway URL and any key, pick a model or `auto`, toggle OCI Guardrails, and chat with streaming. Each response shows which model actually served it, latency and token usage — handy for demoing auto-routing.

## Deploying on OCI

Run the container on an OCI compute instance or OKE. On OCI you can drop the user API key entirely:

- For the guardrails hook set `auth_type: instance_principal` in the guardrail's `litellm_params`.
- For the `oci/` models switch the auth block to LiteLLM's OCI-SDK-signer mode (see the [LiteLLM OCI docs](https://docs.litellm.ai/docs/providers/oci)).
- Front the gateway with an OCI Load Balancer + WAF; store `.env` secrets in OCI Vault.

## Troubleshooting

- **DAC model returns 404/401** — the model name must be the *endpoint* OCID (`ocid1.generativeaiendpoint...`), not the model OCID, and the API base must end in `/20231130/actions/v1`. The `sk-` key must be created in the same region.
- **`auto` model missing** — requires LiteLLM ≥ 1.94 (`pip install -U "litellm[proxy]"` or a current Docker tag).
- **Guardrail errors on startup** — the hook needs the OCI SDK (`pip install oci`, already in the Dockerfile) and valid `OCI_*` env vars or an `~/.oci/config`.
- **On-demand model 404** — check the model is available in your `OCI_REGION` (availability differs per region).

## Security notes

- No OCIDs, keys or customer data are committed — everything sensitive comes from `.env` (gitignored).
- The master key is for admins only; hand applications virtual keys with budgets.
