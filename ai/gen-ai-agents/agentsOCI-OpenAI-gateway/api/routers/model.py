# app/api/routers/model.py
from __future__ import annotations

import os
import yaml
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from api.auth import api_key_auth

router = APIRouter(prefix="/models", dependencies=[Depends(api_key_auth)])

# ---- helpers ----
def _here() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load_yaml(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _flatten_models(models_yaml: Any) -> List[Dict[str, Any]]:
    """
    Flattens your existing models.yaml structure into a list of dicts with keys:
    - name/model_id/endpoint, plus inferred _region/_bucket/_compartment_id
    """
    if not models_yaml:
        return []
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

    if isinstance(models_yaml, list):
        flat: List[Dict[str, Any]] = []
        for ent in models_yaml:
            if isinstance(ent, dict):
                flat.extend(flatten(ent))
        return flat
    if isinstance(models_yaml, dict):
        return flatten(models_yaml)
    return []

def _load_agents() -> List[Dict[str, Any]]:
    data = _load_yaml(os.path.join(_here(), "agents.yaml")) or {}
    agents = data.get("agents") or []
    # normalize required fields
    out: List[Dict[str, Any]] = []
    for a in agents:
        entry = {
            "id": a.get("id"),
            "name": a.get("name") or a.get("id"),
            "description": a.get("description"),
            "region": a.get("region"),
            "endpoint_ocid": a.get("endpoint_ocid"),
            "agent_ocid": a.get("agent_ocid"),
            "compartment_ocid": a.get("compartment_ocid"),
        }
        if entry["id"] and entry["region"] and (entry["endpoint_ocid"] or entry["agent_ocid"]):
            out.append(entry)
    return out

# ---- route ----
@router.get("")
def list_models():
    # 1) Your OCI LLM models (unchanged)
    models_yaml = _load_yaml(os.path.join(_here(), "models.yaml"))
    llms = _flatten_models(models_yaml)

    llm_items = [
        {
            "id": m.get("name") or m.get("model_id") or "unknown",
            "object": "model",
            "owned_by": f"oci:{m.get('_bucket')}",
            "permission": [],
            "metadata": {
                "region": m.get("_region"),
                "bucket": m.get("_bucket"),
                "model_id": m.get("model_id"),
                "endpoint": m.get("endpoint"),
                "description": m.get("description"),
            },
        }
        for m in llms
    ]

    # 2) OCI Agents as "virtual models"
    agents = _load_agents()
    agent_items = [
        {
            "id": f"agent:{a['id']}",    # what n8n will select in the dropdown
            "object": "model",
            "owned_by": "oci-agent",
            "permission": [],
            "metadata": {
                "kind": "agent",
                "alias": a["id"],
                "name": a["name"],
                "description": a.get("description"),
                "region": a["region"],
                "endpoint_ocid": a.get("endpoint_ocid"),
                "agent_ocid": a.get("agent_ocid"),
                "compartment_ocid": a.get("compartment_ocid"),
            },
        }
        for a in agents
    ]

    return {"object": "list", "data": llm_items + agent_items}
