# app.py
import os
import sys
import logging
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse

API_ROUTE_PREFIX = "/v1"
TITLE = "OCI OpenAI-Compatible Gateway"
DESCRIPTION = "FastAPI service that proxies OCI models/agents behind OpenAI-style endpoints"
SUMMARY = "OpenAI-style API over OCI backends"

# ---------- App ----------
app = FastAPI(title=TITLE, description=DESCRIPTION, summary=SUMMARY)

# CORS (open defaults; tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# ---------- Mount routers if available ----------
have_models_router = False

try:
    # /v1/models (usually backed by models.yaml)
    from api.routers import model  # type: ignore
    app.include_router(model.router, prefix=API_ROUTE_PREFIX)
    have_models_router = True
except Exception as e:
    logging.getLogger(__name__).warning("Models router not loaded: %s", e)

try:
    # /v1/chat/completions (your handler; now supports agent_ocid if you added that branch)
    from api.routers import chat  # type: ignore
    app.include_router(chat.router, prefix=API_ROUTE_PREFIX)
except Exception as e:
    logging.getLogger(__name__).warning("Chat router not loaded: %s", e)

try:
    # /v1/embeddings
    from api.routers import embeddings  # type: ignore
    app.include_router(embeddings.router, prefix=API_ROUTE_PREFIX)
except Exception as e:
    logging.getLogger(__name__).warning("Embeddings router not loaded: %s", e)

try:
    # Optional: /v1/oci/agents (list/health/chat via agent endpoint OCIDs)
    from api.routers import oci_agents  # type: ignore
    app.include_router(oci_agents.router, prefix=API_ROUTE_PREFIX)
except Exception as e:
    logging.getLogger(__name__).info("OCI agents router not loaded (optional): %s", e)

# ---------- Fallback /v1/models (if no models router present) ----------
if not have_models_router:
    try:
        import yaml  # lazy import to avoid dependency if router exists

        def _models_yaml_paths() -> List[str]:
            here = os.path.dirname(os.path.abspath(__file__))
            return [
                os.path.join(here, "models.yaml"),
                os.path.join(os.path.dirname(here), "models.yaml"),
            ]

        def _load_models_flat() -> List[Dict[str, Any]]:
            path = None
            for p in _models_yaml_paths():
                if os.path.exists(p):
                    path = p
                    break
            if not path:
                return []
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            def flatten(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
                out: List[Dict[str, Any]] = []
                models = (entry or {}).get("models") or {}
                for bucket in ("ondemand", "dedicated", "datascience"):
                    for m in (models.get(bucket) or []):
                        m2 = dict(m)
                        m2["_bucket"] = bucket
                        m2["_region"] = entry.get("region")
                        m2["_compartment_id"] = entry.get("compartment_id")
                        out.append(m2)
                return out

            if isinstance(data, list):
                flat: List[Dict[str, Any]] = []
                for ent in data:
                    if isinstance(ent, dict):
                        flat.extend(flatten(ent))
                return flat
            if isinstance(data, dict):
                return flatten(data)
            return []

        @app.get(f"{API_ROUTE_PREFIX}/models")
        def list_models_fallback():
            try:
                models = _load_models_flat()
                return {
                    "object": "list",
                    "data": [
                        {
                            "id": m.get("name") or m.get("model_id") or "unknown",
                            "object": "model",
                            "owned_by": "oci-local",
                            "permission": [],
                            "metadata": {
                                "region": m.get("_region"),
                                "bucket": m.get("_bucket"),
                                "model_id": m.get("model_id"),
                                "endpoint": m.get("endpoint"),
                                "description": m.get("description"),
                            },
                        }
                        for m in models
                    ],
                }
            except Exception as e:
                logging.exception("Failed to read models.yaml: %s", e)
                return {"object": "list", "data": []}
    except Exception as e:
        logging.getLogger(__name__).warning("Fallback /v1/models not available: %s", e)

# ---------- Health & basic routes ----------
@app.get("/")
def root_ok():
    return {"ok": True, "service": TITLE}

@app.get("/health")
def health_ok():
    return {"status": "ok"}

# ---------- Error handler ----------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logging.exception("Unhandled error: %s", exc)
    return PlainTextResponse(str(exc), status_code=500)

# ---------- Startup banner ----------
@app.on_event("startup")
def show_routes():
    try:
        print("✅ Available routes:")
        for r in app.routes:
            print(f"  {r.path:30s} → {r.name}")
    except Exception:
        pass

# ---------- Entrypoint (exact launcher you requested) ----------
PORT = int(os.getenv("PORT", "8088"))
RELOAD = os.getenv("RELOAD", "false").lower() in ("1", "true", "yes")

if __name__ == "__main__":
    # Make sure the string target "app:app" resolves to THIS module when run as a script.
    # This avoids the common folder/file name collision on Windows.
    sys.modules.setdefault("app", sys.modules[__name__])
    uvicorn.run("app:app", host="0.0.0.0", port=PORT, reload=RELOAD)
