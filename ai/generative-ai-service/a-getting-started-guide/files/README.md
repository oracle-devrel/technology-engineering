# OCI Generative AI Workshop Files

Run commands in this directory.

1. Install dependencies with `uv sync`.
2. Copy `.env.example` to `.env`.
3. Replace placeholder values in `.env`.
4. Open the notebooks in `notebooks` or start the gateway with:

```bash
uv run python -m uvicorn workshop_gateway.app:app --host localhost --port 8088
```

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
