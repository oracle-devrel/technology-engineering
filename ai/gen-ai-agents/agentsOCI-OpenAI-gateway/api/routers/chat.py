# app/api/routers/chat.py
from __future__ import annotations

import os
import time
import json
import yaml
import logging
from typing import Annotated, Any, Dict, List, Optional, Tuple, Union

import oci
from fastapi import APIRouter, Depends, Body, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse

from api.auth import api_key_auth
from api.models.ocigenai import OCIGenAIModel
from api.models.ociodsc import OCIOdscModel
from api.schema import ChatRequest, ChatResponse, ChatStreamResponse
from api.setting import (
    SUPPORTED_OCIGENAI_CHAT_MODELS,
    SUPPORTED_OCIODSC_CHAT_MODELS,
    DEFAULT_MODEL,
)

router = APIRouter(prefix="/chat", dependencies=[Depends(api_key_auth)])

# ---------------- paths & loaders ----------------
def _root_dir() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def _load_yaml(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def _load_agents() -> List[Dict[str, Any]]:
    data = _load_yaml(os.path.join(_root_dir(), "agents.yaml")) or {}
    agents = data.get("agents") or []
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

def _match_agent_by_model(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Accepts:
      - "agent:<alias>" (preferred)
      - "<alias>"
      - raw endpoint OCID or agent OCID
    """
    agents = _load_agents()
    # Direct OCIDs?
    if model_name.startswith("ocid1.genaiagentendpoint.") or model_name.startswith("ocid1.genaiagent."):
        for a in agents:
            if model_name in (a.get("endpoint_ocid"), a.get("agent_ocid")):
                return a
    # alias forms
    alias = model_name.split("agent:", 1)[1] if model_name.startswith("agent:") else model_name
    for a in agents:
        if a["id"] == alias:
            return a
    return None

# ---------------- OCI clients ----------------
def _base_cfg(region: str) -> Dict[str, Any]:
    if not region:
        raise HTTPException(status_code=400, detail="`region` is required with agent fields.")
    if os.environ.get("OCI_RESOURCE_PRINCIPAL_VERSION"):
        return {
            "signer": oci.auth.signers.get_resource_principals_signer(),
            "config": {},
            "region": region,
        }
    cfg = oci.config.from_file(
        os.environ.get("OCI_CONFIG_FILE", "~/.oci/config"),
        os.environ.get("OCI_CONFIG_PROFILE", "DEFAULT"),
    )
    cfg["region"] = region
    return {"signer": None, "config": cfg, "region": region}

def _agent_runtime_client(region: str):
    base = _base_cfg(region)
    if base["signer"] is not None:
        return oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(
            config={}, signer=base["signer"], region=base["region"]
        )
    return oci.generative_ai_agent_runtime.GenerativeAiAgentRuntimeClient(base["config"])

def _agent_mgmt_client(region: str):
    base = _base_cfg(region)
    if base["signer"] is not None:
        return oci.generative_ai_agent.GenerativeAiAgentClient(
            config={}, signer=base["signer"], region=base["region"]
        )
    return oci.generative_ai_agent.GenerativeAiAgentClient(base["config"])

# ---------------- utilities ----------------
def _extract_user_text(messages: List[Dict[str, Any]] | List[Any]) -> str:
    if not messages:
        return ""
    # normalize
    norm: List[Dict[str, Any]] = []
    for m in messages:
        if isinstance(m, dict):
            norm.append(m)
        else:
            try:
                norm.append(m.model_dump())
            except Exception:
                try:
                    norm.append(dict(m))
                except Exception:
                    pass
    for m in reversed(norm):
        if m.get("role") == "user":
            c = m.get("content", "")
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return "".join(
                    part.get("text", "") for part in c if isinstance(part, dict) and part.get("type") == "text"
                )
    return ""

def _resolve_endpoint_ocid(region: str, endpoint_ocid: Optional[str], agent_ocid: Optional[str], compartment_ocid: Optional[str]) -> str:
    if endpoint_ocid:
        return endpoint_ocid
    if not agent_ocid:
        raise HTTPException(status_code=400, detail="Provide endpoint OCID or agent OCID.")
    mgmt = _agent_mgmt_client(region)
    comp_id = compartment_ocid
    if not comp_id:
        try:
            agent = mgmt.get_agent(agent_id=agent_ocid).data
            comp_id = getattr(agent, "compartment_id", None)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"Failed to get agent {agent_ocid}: {e}")
        if not comp_id:
            raise HTTPException(status_code=502, detail=f"Agent {agent_ocid} has no compartment_id.")
    try:
        endpoints = oci.pagination.list_call_get_all_results(
            mgmt.list_agent_endpoints,
            compartment_id=comp_id,
            agent_id=agent_ocid,
        ).data
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to list endpoints for agent {agent_ocid}: {e}")
    if not endpoints:
        raise HTTPException(status_code=404, detail=f"No endpoints found for agent {agent_ocid} in {region}.")
    # prefer ACTIVE newest
    active = [ep for ep in endpoints if getattr(ep, "lifecycle_state", "").upper() == "ACTIVE"]
    chosen = sorted(active or endpoints, key=lambda ep: getattr(ep, "time_created", 0), reverse=True)[0]
    eid = getattr(chosen, "id", None)
    if not eid:
        raise HTTPException(status_code=502, detail="Resolved endpoint missing id.")
    return eid

def _openai_like_response(text: str, model_tag: str) -> Dict[str, Any]:
    now = int(time.time())
    return {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion",
        "created": now,
        "model": model_tag,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
    }

def _stream_one_chunk(text: str, model_tag: str):
    now = int(time.time())
    first = {
        "id": f"chatcmpl-{now}",
        "object": "chat.completion.chunk",
        "created": now,
        "model": model_tag,
        "choices": [{"index": 0, "delta": {"role": "assistant", "content": text}, "finish_reason": None}],
    }
    yield f"data: {json.dumps(first, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# ---------------- route ----------------
@router.post("/completions", response_model=ChatResponse | ChatStreamResponse, response_model_exclude_unset=True)
async def chat_completions(
    request: Request,
    chat_request: Annotated[
        ChatRequest,
        Body(examples=[{"model": "agent:sales-kb", "messages": [{"role": "user", "content": "Hello!"}]}]),
    ],
):
    try:
        raw = await request.json()
    except Exception:
        raw = {}

    # ---- A) MODEL == agent from agents.yaml (preferred for n8n) ----
    agent_cfg = _match_agent_by_model(chat_request.model or "")
    if agent_cfg:
        region = agent_cfg["region"]
        endpoint_id = _resolve_endpoint_ocid(region, agent_cfg.get("endpoint_ocid"), agent_cfg.get("agent_ocid"), agent_cfg.get("compartment_ocid"))
        runtime = _agent_runtime_client(region)
        user_text = _extract_user_text(chat_request.messages)

        # Ensure session (allow client-provided via extra_body.session_id too)
        session_id = (raw.get("extra_body") or {}).get("session_id")
        if not session_id:
            create_session_details = oci.generative_ai_agent_runtime.models.CreateSessionDetails(description="Gateway session")
            session_obj = runtime.create_session(create_session_details=create_session_details, agent_endpoint_id=endpoint_id).data
            session_id = getattr(session_obj, "id", None)
        if not session_id:
            raise HTTPException(status_code=502, detail="Failed to acquire sessionId for agent chat.")

        chat_details = oci.generative_ai_agent_runtime.models.ChatDetails(
            user_message=user_text, session_id=session_id, should_stream=False
        )
        try:
            result = runtime.chat(agent_endpoint_id=endpoint_id, chat_details=chat_details).data
            text = ""
            if getattr(result, "message", None) and getattr(result.message, "content", None):
                text = getattr(result.message.content, "text", "") or ""
        except oci.exceptions.ServiceError as se:
            raise HTTPException(status_code=502, detail=f"Agent chat failed ({se.status}): {getattr(se,'message',str(se))}")

        tag = f"oci:agentendpoint:{endpoint_id}"
        if getattr(chat_request, "stream", False):
            return StreamingResponse(_stream_one_chunk(text, tag), media_type="text/event-stream", headers={"x-oci-session-id": session_id})
        return JSONResponse(content=_openai_like_response(text, tag), headers={"x-oci-session-id": session_id})

    # ---- B) EXTRA BODY (agent_ocid/endpoint_ocid) — still supported ----
    extra = (raw.get("extra_body") if isinstance(raw, dict) else None) or {}
    endpoint_ocid = raw.get("agent_endpoint_ocid") or extra.get("agent_endpoint_ocid")
    agent_ocid = raw.get("agent_ocid") or extra.get("agent_ocid")
    region = raw.get("region") or extra.get("region")
    compartment_ocid = raw.get("compartment_ocid") or extra.get("compartment_ocid") or os.getenv("OCI_COMPARTMENT_OCID")

    if endpoint_ocid or agent_ocid:
        endpoint_id = _resolve_endpoint_ocid(region or "", endpoint_ocid, agent_ocid, compartment_ocid)
        runtime = _agent_runtime_client(region or "")
        user_text = _extract_user_text(chat_request.messages)
        session_id = raw.get("session_id") or extra.get("session_id")
        if not session_id:
            create_session_details = oci.generative_ai_agent_runtime.models.CreateSessionDetails(description="Gateway session")
            session_obj = runtime.create_session(create_session_details=create_session_details, agent_endpoint_id=endpoint_id).data
            session_id = getattr(session_obj, "id", None)
        if not session_id:
            raise HTTPException(status_code=502, detail="Failed to acquire sessionId for agent chat.")
        chat_details = oci.generative_ai_agent_runtime.models.ChatDetails(user_message=user_text, session_id=session_id, should_stream=False)
        result = runtime.chat(agent_endpoint_id=endpoint_id, chat_details=chat_details).data
        text = getattr(getattr(result, "message", None), "content", None)
        text = getattr(text, "text", "") if text else ""
        tag = f"oci:agentendpoint:{endpoint_id}"
        if getattr(chat_request, "stream", False):
            return StreamingResponse(_stream_one_chunk(text, tag), media_type="text/event-stream", headers={"x-oci-session-id": session_id})
        return JSONResponse(content=_openai_like_response(text, tag), headers={"x-oci-session-id": session_id})

    # ---- C) FALLBACK: your existing LLM model routing ----
    model_name = chat_request.model or DEFAULT_MODEL
    chat_request.model = model_name

    model_type = None
    if model_name in SUPPORTED_OCIGENAI_CHAT_MODELS:
        model_type = SUPPORTED_OCIGENAI_CHAT_MODELS[model_name]["type"]
    elif model_name in SUPPORTED_OCIODSC_CHAT_MODELS:
        model_type = SUPPORTED_OCIODSC_CHAT_MODELS[model_name]["type"]

    if not model_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown model '{model_name}'. Use an agent (e.g., 'agent:sales-kb') or a supported model.",
        )

    if model_type == "datascience":
        model = OCIOdscModel()
    elif model_type in ("ondemand", "dedicated"):
        model = OCIGenAIModel()
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported model type '{model_type}'")

    model.validate(chat_request)

    if chat_request.stream:
        return StreamingResponse(content=model.chat_stream(chat_request), media_type="text/event-stream")
    return model.chat(chat_request)
