# cuOPT Route Optimizer

This repository separates the runnable web application from supporting artifacts.

- [`app/`](app/README.md) contains the React/Vite application, Express API proxy, and local configuration.
- [`scripts/`](scripts/run.sh) contains the local launcher, which starts the backend before the frontend.
- [`deploy/`](deploy/OKE_DEPLOYMENT_PLAN.md) contains Docker Compose, Docker, and OKE deployment assets.
- `architecture/` contains editable architecture diagrams and their guide.
- `demo/` contains example delivery and route data.
- `genai/` contains the standalone Python OCI Generative AI helper.

To run the application locally, change to `app/`, install dependencies, configure `.env`, and run `../scripts/run.sh`.
