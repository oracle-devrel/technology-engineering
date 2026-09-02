# Fly-Opt — AI-Powered Flight & Route Optimization

Fly-Opt is a web application for flight operations and route optimization. It combines NVIDIA cuOpt GPU-accelerated solving with OCI Generative AI so that users can plan, optimize, and analyse routes — including airline and air-traffic scenarios — through either a visual dashboard or plain-language queries.

## Purpose

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

## Getting Started

To run the application locally, change to `app/`, install dependencies, configure `.env`, and run `../scripts/run.sh`. See [`app/README.md`](app/README.md) for prerequisites, environment configuration, and troubleshooting, and [`app/AI_ASSISTANT_PROMPTS.md`](app/AI_ASSISTANT_PROMPTS.md) for sample AI assistant prompts.

## License
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [`License`](LICENSE) file for details.
