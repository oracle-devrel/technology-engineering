"""Domain adapter management endpoints — list, toggle, inspect, and edit adapters."""

import json
import logging
import os
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.adapter_service import (
    ADAPTERS_DIR,
    list_domains,
    load_adapter,
    get_extraction_schema,
    get_compliance_rules,
    get_lessons,
    save_adapter_file,
    invalidate_cache,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/domains", tags=["domains"])

# ── Persisted enabled/disabled state ──────────────────────────────────────

_state_file = os.path.join(ADAPTERS_DIR, ".domain_state.json")


def _load_state() -> dict:
    if os.path.exists(_state_file):
        with open(_state_file) as f:
            return json.load(f)
    return {}


def _save_state(state: dict):
    os.makedirs(os.path.dirname(_state_file), exist_ok=True)
    with open(_state_file, "w") as f:
        json.dump(state, f)


def _is_enabled(domain: str) -> bool:
    if domain == "generic":
        return True
    state = _load_state()
    return state.get(domain, True)  # enabled by default


# ── Request / response models ─────────────────────────────────────────────

class DomainToggle(BaseModel):
    enabled: bool


class AdapterUpdateRequest(BaseModel):
    file_type: str  # "rules" | "prompts" | "lessons" | "schema"
    data: Any       # full JSON payload for the file


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.get("")
async def get_domains():
    """List all available domain adapters with metadata and enabled state."""
    domains = list_domains()
    result = []
    for d in domains:
        try:
            adapter = load_adapter(d)
            schema_info = adapter.get("schema", {})
            result.append({
                "name": d,
                "display_name": schema_info.get("name", d.replace("-", " ").title()),
                "description": schema_info.get("description", ""),
                "field_count": len(adapter.get("schema", {}).get("fields", [])),
                "rule_count": len(adapter.get("rules", {}).get("checks", [])),
                "lesson_count": len(adapter.get("lessons", {}).get("items", [])),
                "enabled": _is_enabled(d),
            })
        except Exception:
            result.append({
                "name": d,
                "display_name": d.replace("-", " ").title(),
                "description": "",
                "field_count": 0,
                "rule_count": 0,
                "lesson_count": 0,
                "enabled": False,
            })
    return {"domains": result}


@router.patch("/{domain}/toggle")
async def toggle_domain(domain: str, body: DomainToggle):
    """Enable or disable a domain adapter. Generic cannot be disabled."""
    if domain == "generic":
        return {"domain": domain, "enabled": True, "message": "Generic domain is always enabled"}
    # Verify domain exists
    if domain not in list_domains():
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    state = _load_state()
    state[domain] = body.enabled
    _save_state(state)
    return {"domain": domain, "enabled": body.enabled}


@router.get("/{domain}")
async def get_domain_detail(domain: str):
    """Get full domain adapter configuration (schema, rules, prompts, lessons)."""
    try:
        adapter = load_adapter(domain)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    return adapter


@router.get("/{domain}/schema")
async def get_schema(domain: str):
    """Get extraction schema for a domain."""
    try:
        return {"fields": get_extraction_schema(domain)}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")


@router.get("/{domain}/rules")
async def get_rules(domain: str):
    """Get compliance rules for a domain."""
    try:
        return {"rules": get_compliance_rules(domain)}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")


@router.get("/{domain}/lessons")
async def get_domain_lessons(domain: str):
    """Get lessons learned for a domain."""
    try:
        return {"lessons": get_lessons(domain)}
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")


@router.put("/{domain}/config")
async def update_domain_config(domain: str, body: AdapterUpdateRequest):
    """Update a domain adapter configuration file (rules, prompts, lessons, or schema).

    This allows manual editing of per-industry compliance configuration.
    """
    if domain not in list_domains():
        raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found")
    try:
        save_adapter_file(domain, body.file_type, body.data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"domain": domain, "file_type": body.file_type, "message": "Configuration updated successfully"}
