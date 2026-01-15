# app/api/routers/chat.py
from __future__ import annotations

import os
import time
import json
import yaml
import logging
from urllib.parse import urlparse
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

def _normalize_source_location(source_location: Any) -> dict:
    """
    Returns a dict with display_name and url (when present).
    Handles:
      - OCI SDK objects with .url
      - dict-like with 'url'
      - JSON-stringified dicts
      - raw URLs
      - plain strings / paths
    """
    display_name = None
    url_value = None

    try:
        # 1) SDK object with attribute 'url'
        if hasattr(source_location, "url"):
            url_value = getattr(source_location, "url") or None

        # 2) dict-like
        if url_value is None:
            if isinstance(source_location, dict):
                url_value = source_location.get("url")
            else:
                # 3) JSON-like string? try parse
                if isinstance(source_location, str) and source_location.strip().startswith("{"):
                    try:
                        parsed = json.loads(source_location)
                        if isinstance(parsed, dict):
                            url_value = parsed.get("url")
                            source_location = parsed
                    except Exception:
                        pass

        # 4) If it's a URL string
        if url_value is None and isinstance(source_location, str):
            if source_location.startswith("http://") or source_location.startswith("https://"):
                url_value = source_location

        # Decide display_name
        candidate_for_name = url_value or (source_location if isinstance(source_location, str) else None)
        if candidate_for_name:
            if isinstance(candidate_for_name, str) and (
                candidate_for_name.startswith("http://") or candidate_for_name.startswith("https://")
            ):
                path = urlparse(candidate_for_name).path or ""
                base = os.path.basename(path) or path.strip("/")
                display_name = base or candidate_for_name
            else:
                display_name = os.path.basename(candidate_for_name) or str(candidate_for_name)
        else:
            display_name = None

    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to normalize source_location: {e}")
        display_name = None
        url_value = None

    return {"display_name": display_name, "url": url_value}

def _extract_citations_from_response(result, agent_name: str = "OCI Agent") -> Optional[Dict[str, Any]]:
    try:
        if not result or not hasattr(result, 'message') or not result.message:
            return None
        
        message = result.message
        if not hasattr(message, 'content') or not message.content:
            return None
        
        content = message.content
        if not hasattr(content, 'paragraph_citations') or not content.paragraph_citations:
            return None
        
        paragraph_citations = []
        for para_citation in content.paragraph_citations:
            if hasattr(para_citation, 'paragraph') and hasattr(para_citation, 'citations'):
                paragraph = para_citation.paragraph
                citations = para_citation.citations
                
                citation_list = []
                for citation in citations:
                    normalized_loc = _normalize_source_location(getattr(citation, 'source_location', None))
                    citation_dict = {
                        "source_text": getattr(citation, 'source_text', None),
                        "title": getattr(citation, 'title', None),
                        "doc_id": getattr(citation, 'doc_id', None),
                        "page_numbers": getattr(citation, 'page_numbers', None),
                        "metadata": getattr(citation, 'metadata', None),
                        "location_display": normalized_loc.get("display_name"),
                        "location_url": normalized_loc.get("url"),
                    }
                    citation_list.append(citation_dict)
                
                paragraph_dict = {
                    "paragraph": {
                        "text": getattr(paragraph, 'text', '') or '',
                        "start": getattr(paragraph, 'start', 0),
                        "end": getattr(paragraph, 'end', 0)
                    },
                    "citations": citation_list
                }
                paragraph_citations.append(paragraph_dict)
        
        if paragraph_citations:
            return {"paragraph_citations": paragraph_citations, "agent_name": agent_name}
        
        return None
    except Exception as e:
        logging.getLogger(__name__).warning(f"Failed to extract citations: {e}")
        return None

def _format_citations_for_display(citations: Dict[str, Any], agent_name: str = "OCI Agent") -> str:
    """
    Renders like:

    --- Citations from [Agent Name] ---

    1. Text: "..."
       Sources:
       1. Title: ...
          Location: document.pdf
          Document ID: ...
          Pages: [1, 2]
          Source: ...
          Metadata: {...}

    --- End Citations ---
    """
    if not citations or "paragraph_citations" not in citations:
        return ""
    
    agent = citations.get("agent_name") or agent_name
    blocks = []
    blocks.append(f"\n\n--- Citations from [{agent}] ---\n")
    
    for idx, para_citation in enumerate(citations["paragraph_citations"], start=1):
        p = para_citation.get("paragraph", {}) or {}
        text = (p.get("text") or "").strip()
        
        line = []
        # Ensure quoted text; json.dumps gives safe quoting and escapes
        #line.append(f"{idx}. Text: {json.dumps(text) if text else '\"\"'}")
        line.append("   Sources:")
        
        for jdx, c in enumerate(para_citation.get("citations", []) or [], start=1):
            title = c.get("title")
            loc_display = c.get("location_display")
            doc_id = c.get("doc_id")
            pages = c.get("page_numbers")
            source_text = c.get("source_text")
            metadata = c.get("metadata")
            
            line.append(f"   {jdx}. " + (f"Title: {title}" if title else "Title: (unknown)"))
            if loc_display:
                line.append(f"      Location: {loc_display}")
            if doc_id:
                line.append(f"      Document ID: {doc_id}")
            if pages:
                try:
                    pages_str = json.dumps(pages, ensure_ascii=False)
                except Exception:
                    pages_str = str(pages)
                line.append(f"      Pages: {pages_str}")
            if source_text:
                st = (source_text or "").strip()
                if len(st) > 500:
                    st = st[:500].rstrip() + "…"
                #line.append(f"      Source: {st}")
            if metadata:
                try:
                    md_str = json.dumps(metadata, ensure_ascii=False)
                    line.append(f"      Metadata: {md_str}")
                except Exception:
                    pass
        
        blocks.append("\n".join(line) + "\n")
    
    blocks.append("--- End Citations ---")
    return "\n".join(blocks)

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
            
            agent_name = agent_cfg.get("name", "OCI Agent")
            citations = _extract_citations_from_response(result, agent_name)
            
            if citations:
                citation_text = _format_citations_for_display(citations, agent_name)
                text += citation_text
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
        
        citations = _extract_citations_from_response(result, "OCI Agent")
        
        if citations:
            citation_text = _format_citations_for_display(citations, "OCI Agent")
            text += citation_text
        
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
