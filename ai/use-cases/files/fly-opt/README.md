# Fly-Opt — AI-Powered Flight & Route Optimization

Fly-Opt is a web application for flight operations and route optimization. It combines NVIDIA cuOpt GPU-accelerated solving with OCI Generative AI so that users can plan, optimize, and analyse routes — including airline and air-traffic scenarios — through either a visual dashboard or plain-language queries.

## Capabilities

The application addresses airline and fleet operations questions such as:

- **Live air traffic monitoring** — Track aircraft in real time on an interactive map using OpenSky Network state vectors, with per-aircraft details and bounding-box queries.
- **Route optimization** — Solve large vehicle-routing and scheduling problems (thousands of stops) with NVIDIA cuOpt, honouring constraints such as time windows, capacities, and fleet size.
- **Natural-language queries** — Ask questions like *"optimize routes for 50 stops with 5 vehicles"* in an AI chat powered by OCI Generative AI; prompts are translated automatically into cuOpt requests and results are explained back in plain language.
- **Weather-aware planning** — Assess adverse weather conditions along routes and their impact on routing decisions.

## Repository Layout

- [`app/`](app/README.md) — The React/Vite frontend, Express API proxy (cuOpt, OCI GenAI, OpenSky), and local configuration.
- [`scripts/`](scripts/run.sh) — The local launcher, which starts the backend before the frontend.
- [`deploy/`](deploy/OKE_DEPLOYMENT_PLAN.md) — Docker Compose, Docker, and OKE (Oracle Kubernetes Engine) deployment assets.
- `architecture/` — Editable architecture diagrams and their guide.
- `demo/` — Example delivery and route data.
- `genai/` — The standalone Python OCI Generative AI helper.

## Running Locally

### Prerequisites

- **Node.js 18+** — check with `node -v`.
- **OCI CLI configured** — the app authenticates to OCI Generative AI through the OCI SDK, which reads `~/.oci/config`. If you don't have it yet, run `oci setup config` and confirm the `DEFAULT` profile has a valid `user`, `fingerprint`, `tenancy`, `region`, and `key_file`.
- **Access to a cuOpt endpoint** — a reachable NVIDIA cuOpt server (on the same network/VPN if it's hosted on OKE).
- *(Optional)* An [OpenWeatherMap](https://openweathermap.org/api) API key for live weather; leave it blank to use mock weather data.

### Setup (both options)

```bash
# 1. Move into the frontend application
cd app

# 2. Install dependencies
npm install

# 3. Create your local configuration from the template
cp .env.example .env
#    then edit .env to set your cuOpt endpoint, OCI GenAI endpoint,
#    model OCID, and compartment OCID (see below)
```

Then choose one of the two ways to start the app.

### Option 1 — Run with the launcher script (recommended)

Starts the Express API proxy first, waits until it's healthy, then starts the Vite frontend:

```bash
../scripts/run.sh
#    or, equivalently:
npm run start
```

### Option 2 — Run the services individually

Useful when you want each process in its own terminal (e.g. to read logs separately). Start the proxy first, then the frontend:

```bash
npm run server   # API proxy only, on port 3001
npm run dev      # frontend only, on port 5173
```

With either option, once both are up open **http://localhost:5173** in your browser.

### Local endpoints

| Service | URL |
|---------|-----|
| Frontend (Vite) | http://localhost:5173 |
| API proxy (Express) | http://localhost:3001 |

### Key `.env` values

```env
# cuOpt server
VITE_CUOPT_ENDPOINT=https://cuopt-2-cuopt.<vm>.nip.io
CUOPT_ENDPOINT=https://cuopt-2-cuopt.<vm>.nip.io

# OCI Generative AI (authenticated via ~/.oci/config — no API key in .env)
OCI_GENAI_ENDPOINT=https://inference.generativeai.<region>.oci.oraclecloud.com
OCI_GENAI_MODEL_ID=ocid1.generativeaimodel.oc1.<region>.your-model-ocid
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..your-compartment-ocid
OCI_CONFIG_PROFILE=DEFAULT
```

### Verifying it works

```bash
# Backend health, then the proxied cuOpt and GenAI health checks
curl http://localhost:3001/health
curl http://localhost:3001/api/cuopt-health
curl http://localhost:3001/api/genai/health
```

If a port is already taken, free it with `lsof -ti:5173 | xargs kill -9` (or `:3001`).

For the full prerequisite, environment, and troubleshooting reference see [`app/README.md`](app/README.md), and for sample AI assistant queries see [`app/AI_ASSISTANT_PROMPTS.md`](app/AI_ASSISTANT_PROMPTS.md).

## License
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [`License`](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) file for details.
