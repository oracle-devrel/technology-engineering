"""
File name: docgen_utils.py
Author: L. Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Text generation utilities

"""

import asyncio
from typing import Any, Optional
from langchain_core.messages import HumanMessage


def _dig_for_string(obj: Any, depth: int = 0) -> Optional[str]:
    """Recursively search nested dict/list structures for a likely content string."""
    if depth > 6:
        return None

    if isinstance(obj, str):
        return obj

    if isinstance(obj, dict):
        # Prefer message.content if present
        msg = obj.get("message")
        if isinstance(msg, dict):
            c = msg.get("content")
            if isinstance(c, str):
                return c
        # Common "choices" shape
        ch = obj.get("choices")
        if isinstance(ch, list):
            for it in ch:
                s = _dig_for_string(it, depth + 1)
                if s:
                    return s
        # Generic scan
        for _, v in obj.items():
            s = _dig_for_string(v, depth + 1)
            if s:
                return s

    if isinstance(obj, list):
        for it in obj:
            s = _dig_for_string(it, depth + 1)
            if s:
                return s

    return None


def extract_text(resp: Any) -> str:
    """
    Normalize LLM outputs across:
    - str
    - LangChain messages (.content as str)
    - Responses-style content blocks (list of {"type": "text", "text": ...})
    - dict-like OpenAI / OCI shapes

    this version manages also Responses-style content blocks
    """

    if resp is None:
        return ""

    # 1. Plain string
    if isinstance(resp, str):
        return resp

    # 2. Responses API / LC adapters: content=[{type: "text", text: "..."}]
    content = getattr(resp, "content", None)
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and isinstance(item.get("text"), str):
                    parts.append(item["text"])
        if parts:
            return "\n".join(parts)

    # 3. LangChain message: .content is str
    if isinstance(content, str):
        return content

    # 4. Dict-like payloads
    if isinstance(resp, dict):
        # Direct keys
        for k in ("content", "text", "output", "message"):
            v = resp.get(k)
            if isinstance(v, str):
                return v

        # Nested Responses-like structure
        v = _dig_for_string(resp)
        if isinstance(v, str):
            return v

    # 5. Fallback (last resort)
    return str(resp)


def extract_model_hint(resp: Any) -> Optional[str]:
    """Best-effort model hint extraction (optional)."""
    for attr in ("model", "model_name"):
        v = getattr(resp, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()

    if isinstance(resp, dict):
        for k in ("model", "model_name"):
            v = resp.get(k)
            if isinstance(v, str) and v.strip():
                return v.strip()

    return None


async def call_llm_normalized(llm: Any, prompt: str) -> tuple[str, Optional[str]]:
    """
    Call the LLM using *sync* invoke(), but keep this function async by
    running the blocking call in a worker thread.

    Returns (text, model_hint).

    Rewritten using invoke (not ainvoke) for better compatibility.
    """
    msg = [HumanMessage(content=prompt)]

    def _sync_call():
        # Prefer invoke() if available; fallback to calling the object directly.
        if hasattr(llm, "invoke"):
            return llm.invoke(msg)
        return llm(msg)

    try:
        resp = await asyncio.to_thread(_sync_call)
    except Exception as e:
        raise RuntimeError(f"LLM invocation failed: {e}") from e

    text = extract_text(resp)
    model_hint = extract_model_hint(resp)
    return text, model_hint
