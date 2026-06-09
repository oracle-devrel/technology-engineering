# OCI GenAI Video Analysis Studio

## Publication Status

- Confidentiality: Public
- Content type: Example application
- License: UPL-1.0

## Reusable Asset Overview

OCI GenAI Video Analysis Studio is an example local web application for analyzing uploaded video files with Gemini models on Oracle Cloud Infrastructure Generative AI. The application keeps OCI API key profile authentication on the local Python backend and sends only non-secret connection settings, prompts, and the selected video from the browser.

## Files

- [files/README.md](./files/README.md) - setup, run, and usage instructions.
- [files/context.md](./files/context.md) - implementation notes and API details.
- [files/backend](./files/backend) - FastAPI backend and OCI Generative AI integration.
- [files/src](./files/src) - React frontend source.
- [files/assets/video-analysis-studio-screenshot.png](./files/assets/video-analysis-studio-screenshot.png) - application screenshot.
- [THIRD_PARTY_LICENSES](./THIRD_PARTY_LICENSES) - direct third-party dependency license summary.

## Requirements

- Node.js for the React frontend.
- Python for the FastAPI backend.
- OCI API key profile authentication configured on the local machine.
- Access to an OCI compartment and a Gemini-supported OCI Generative AI endpoint.

## License

Copyright (c) 2026 Oracle and/or its affiliates.

Released under the Universal Permissive License v1.0. See [LICENSE](./LICENSE).
