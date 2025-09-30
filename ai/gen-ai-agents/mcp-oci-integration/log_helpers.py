"""
log helpers, to help debugging
"""

from __future__ import annotations
import json
import logging
from typing import Any, Dict, List, Sequence
from langchain_core.messages import BaseMessage, AIMessage, ToolMessage

logger = logging.getLogger(__name__)  # module-level logger


def short(s: str, n: int = 500) -> str:
    """
    shorten a msg
    """
    return s if len(s) <= n else s[:n] + f"... <{len(s)-n} more>"


def msg_summary(m: BaseMessage) -> Dict[str, Any]:
    """
    provide the msg in a structured format for logging
    """
    d = {"type": m.__class__.__name__}
    if hasattr(m, "content"):
        content = getattr(m, "content") or ""
        d["content.len"] = len(content)
        d["content.preview"] = short(content, 200)
    if isinstance(m, AIMessage):
        d["tool_calls.count"] = len(getattr(m, "tool_calls", []) or [])
    if isinstance(m, ToolMessage):
        d["tool_call_id"] = getattr(m, "tool_call_id", None)
    return d


def log_tool_schemas(schemas: List[Any], log: logging.Logger | None = None) -> None:
    """
    log schemas
    """
    log = log or logger
    log.info("=== Bound tool schemas (%d) ===", len(schemas))
    for i, s in enumerate(schemas):
        name = (
            getattr(s, "__name__", None)
            or getattr(s, "name", None)
            or getattr(s, "title", "<dict>")
        )
        log.info("[%d] %s | type=%s", i, name, type(s))


def log_history_tail(
    messages: Sequence[BaseMessage], k: int = 6, log: logging.Logger | None = None
) -> None:
    """
    log history tail
    """
    log = log or logger
    log.info(
        "=== History tail (last %d of %d) ===", min(k, len(messages)), len(messages)
    )
    for i, m in enumerate(messages[-k:]):
        log.info("  %d: %s", len(messages) - k + i, msg_summary(m))


def log_ai_tool_calls(ai: AIMessage, log: logging.Logger | None = None) -> None:
    """
    log tool calls
    """
    log = log or logger
    calls = getattr(ai, "tool_calls", []) or []
    log.info("=== Assistant tool_calls (%d) ===", len(calls))
    for i, c in enumerate(calls):
        log.info(
            "  #%d id=%s name=%s args=%s",
            i,
            c.get("id"),
            c.get("name"),
            json.dumps(c.get("args") or {}, ensure_ascii=False),
        )
    raw = getattr(ai, "additional_kwargs", None)
    if raw:
        log.info(
            "additional_kwargs (assistant): %s",
            short(json.dumps(raw, ensure_ascii=False), 1000),
        )


def check_linkage_or_die(
    ai: AIMessage, tool_msgs: List[ToolMessage], log: logging.Logger | None = None
) -> None:
    """
    further check and logs
    """
    log = log or logger
    want = {c["id"] for c in (getattr(ai, "tool_calls", []) or []) if "id" in c}
    got = {tm.tool_call_id for tm in tool_msgs}
    missing = want - got
    extra = got - want
    log.info(
        "=== Linkage check === want=%s got=%s missing=%s extra=%s",
        list(want),
        list(got),
        list(missing),
        list(extra),
    )
    if missing:
        raise RuntimeError(f"Missing ToolMessage(s) for ids: {list(missing)}")
    if extra:
        raise RuntimeError(f"ToolMessage(s) reference unknown ids: {list(extra)}")


def _dump_pair_for_oci_debug(messages, log):
    """
    Find the last assistant message and the following tool messages
    """
    last_ai = None
    tools_for_last_ai = []
    for m in reversed(messages):
        if isinstance(m, ToolMessage):
            tools_for_last_ai.append(
                {"tool_call_id": m.tool_call_id, "content.len": len(m.content or "")}
            )
            continue
        if isinstance(m, AIMessage):
            last_ai = m
            break
        # stop scan if we encounter another role before reaching an AIMessage
        break

    log.info("=== OCI preflight pair ===")
    if last_ai is None:
        log.warning("No trailing AIMessage found before tool messages.")
        return
    log.info(
        "AIMessage: content.len=%s, tool_calls=%s",
        len(last_ai.content or ""),
        [
            {"id": c.get("id"), "name": c.get("name")}
            for c in (last_ai.tool_calls or [])
        ],
    )
    log.info("ToolMessages: %s", tools_for_last_ai)
