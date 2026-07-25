# Translation API for OCI

Translates between multiple language pairs using OCI Generative AI models, with a
pluggable domain-specific glossary (the included example glossary covers online
gaming / finance terminology — swap it for your own domain).

## Deployment

The service is a **FastAPI** app providing sync and streaming (SSE) translation.
Run it locally for development, or deploy it to OCI as an always-on **Container
Instance behind a Load Balancer** using the included Terraform / Resource Manager
Stack (`terraform`).

## Quick Start — Run Locally

Prerequisites:

1. Your OCI user/group must be authorized to use the services this asset needs
   (Container Instances, Load Balancer, Vault, Resource Manager, Generative AI, …).
2. Install and configure the OCI CLI for your tenancy —
   [installation guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm).
3. Create an Object Storage bucket named `bucket-glossary` and upload a file named
   `glossary.json` to it (see the example at `core/glossary.json`). Validate the
   JSON first — e.g. with <https://jsonformatter.curiousconcept.com/> — so an
   invalid file doesn't reach the bucket.

```bash
# Environment variables — Linux / macOS
export OCI_COMPARTMENT_ID="ocid1.compartment.oc1..xxxxxxxxxxxx"
export OCI_CONFIG_FILE="~/.oci/config"
```

```powershell
# Environment variables — Windows (PowerShell)
$env:OCI_COMPARTMENT_ID = "ocid1.compartment.oc1..xxxxxxxxxxxx"
$env:OCI_CONFIG_FILE = "C:\Users\xxxx\.oci\config"
```

```bash
# Install dependencies
pip install -r app/requirements.txt

# Run
uvicorn app.main:app --reload
```

## API Usage

### Sync Translation
```bash
curl -X POST http://localhost:8000/translate \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "spanish-mx"
  }'
```

### Streaming (SSE)
```bash
curl -N -X POST http://localhost:8000/translate/stream \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "spanish-mx"
  }'
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OCI_COMPARTMENT_ID` | (required) | OCI compartment OCID |
| `OCI_GENAI_ENDPOINT` | `https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com` | GenAI endpoint |
| `OCI_DEFAULT_MODEL` | `cohere.command-a-03-2025` | Default model ID |
| `OCI_CONFIG_FILE` | `~/.oci/config` | OCI config file path |
| `OCI_CONFIG_PROFILE` | `DEFAULT` | OCI config profile |
| `MAX_TOKENS` | `2048` | Max output tokens |
| `TEMPERATURE` | `0.0` | Sampling temperature |
| `TOP_P` | `0.8` | Top-p sampling |
| `OCI_AUTH` | `auto` | Set to `api_key` to skip Resource Principals and use `~/.oci/config` directly |

See `core/config.py` for the full list of settings.

## Supported Language Pairs
`english`, `german`, `spanish-mx`, `polish`, `portuguese-br`, `swedish`

| Source / Target | English | German | Spanish (MX) | Polish | Portuguese (BR) | Swedish |
|-----------------|:-------:|:------:|:------------:|:------:|:---------------:|:-------:|
| **English**     |    —    |   ✓    |      ✓       |   ✓    |        ✓        |    ✓    |
| **German**      |    ✓    |   —    |      ✓       |   ✓    |        ✓        |    ✓    |
| **Spanish (MX)**|    ✓    |   ✓    |      —       |   ✓    |                 |    ✓    |
| **Polish**      |    ✓    |   ✓    |      ✓       |   —    |                 |         |
| **Portuguese (BR)** | ✓   |   ✓    |              |        |        —        |         |
| **Swedish**     |    ✓    |   ✓    |      ✓       |        |                 |    —    |

## Supported Models
Any OCI GenAI on-demand model. The API auto-detects the correct request format from
the model ID: GENERIC (Llama/Meta), COHERE (Command R/R+), or COHEREV2 (Command A).

## Tests

```bash
pip install pytest
pytest tests/
```

By default the suite mocks the OCI client. To also run the integration test that
fetches the glossary from a real OCI bucket, set `RUN_OCI_INTEGRATION_TESTS=1`
(Linux/macOS) or `$env:RUN_OCI_INTEGRATION_TESTS="1"` (Windows) before running.

The test suite validates:

- **Every allowed language pair** in both directions (22 parametrized cases covering all 11 pairs)
- **Invalid pair rejection** — pairs not in `ALLOWED_PAIRS` (e.g. Polish → Portuguese-BR) are rejected with a clear error
- **Input validation** — unsupported languages, same source/target, empty text
- **OCI chat body construction** — correct API format selection (GENERIC for Llama, COHERE for Command R/R+, COHEREV2 for Command A), stream flag, system/user message structure
- **Sync translation** — end-to-end with a mocked OCI client, or a real call
- **Glossary use** — checks that the glossary is downloaded from the OCI bucket and applied

## Adding a Language Pair

Three files need updating:

1. **`core/config.py`** — Add the language key to `SUPPORTED_LANGUAGES` (if new) and the pair to `ALLOWED_PAIRS`:
   ```python
   SUPPORTED_LANGUAGES = {"english", "german", ..., "italian"}

   ALLOWED_PAIRS: set[frozenset[str]] = {
       ...,
       frozenset({"english", "italian"}),
   }
   ```

2. **`core/glossary.json`** — not used locally; it must be uploaded to the OCI bucket. The service refreshes the glossary from the bucket every 5 minutes.

3. **`tests/test_models.py`** — Add the new pair (both directions) to the `test_valid_language_pair` parametrize list, and remove it from `test_invalid_language_pair_raises` if it was previously listed there.

## Deploying to OCI — Container Instance + Load Balancer

Always-on container (no cold starts) behind a flexible load balancer. The container
authenticates to OCI GenAI with an OCI API key. **No credentials are baked into the
image** — the entrypoint assembles `~/.oci/config` at container start from environment
variables (`OCI_PRIVATE_KEY_CONTENT`, `OCI_TENANCY`, `OCI_USER`, `OCI_FINGERPRINT`,
`OCI_REGION`), which the Terraform stack injects.

### Prerequisites

- **Docker** running locally (Colima, Docker Desktop, or Rancher Desktop).

### Step 1 — Build and push the Docker image

Use the deploy Dockerfile (`Dockerfile.deploy`). Build for AMD64 (OCI Container
Instances run x86), tag, and push:

```bash
# Build for AMD64 (OCI Container Instances run x86)
docker build --platform linux/amd64 -f app/Dockerfile.deploy -t translate-api:deploy .

# Tag for OCIR — pin a version rather than using :latest in production
docker tag translate-api:deploy <region-key>.ocir.io/<namespace>/translate-api:1.0.0

# Push
docker push <region-key>.ocir.io/<namespace>/translate-api:1.0.0
```

### Step 2 — Deploy with Terraform

Go to `terraform` and follow its README.

### Step 3 — Verify

Terraform outputs the load balancer IP. Test it:

```bash
curl -X POST http://<load-balancer-ip>/translate \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Place your wager on the next jackpot draw.",
    "source_language": "english",
    "target_language": "german"
  }'
```

Wait a few seconds after `apply` for the load balancer to discover its backends — a
request sent immediately can return `502 Bad Gateway`.

### Updating the container

After code changes: rebuild, push, update the Terraform stack variables, and apply again.

## Estimated Costs

Indicative only — check the
[Oracle Cloud Cost Estimator](https://www.oracle.com/cloud/costestimator.html) for
current pricing.

| Resource | Spec | ~Monthly (USD) |
|---|---|---|
| Container Instance | 1 OCPU, 2 GB RAM, always-on (×2 for HA) | ~$27 |
| Flexible Load Balancer | 10 Mbps minimum | ~$10 |
| GenAI inference (Command A) | per request | ~$0.0015 / 1K input tokens, ~$0.007 / 1K output tokens |
| OCIR image storage | | negligible |

**Fixed infrastructure: ~$37/month** plus GenAI usage. For light usage (a few
hundred translations/day), GenAI adds a few dollars/month. To save costs when not
in use, tear down with `terraform destroy` and redeploy when needed. You can add an
API Gateway in front for authentication/security if needed.
