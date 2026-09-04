# Copyright (c) 2026 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/.

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from workshop_helpers.oci_genai_helpers import (
    chat_once,
    create_genai_client,
    load_workshop_env,
)


class ChatMessage(BaseModel):
    role: str
    content: str | list[Any] | None = ""


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool = False


app = FastAPI(
    title="OCI Generative AI Workshop Gateway",
    description="Small OpenAI-compatible gateway for n8n workshop examples.",
    version="0.1.0",
)


def ensure_env_loaded() -> None:
    """Load .env once from the repository root when the server starts."""
    if not os.getenv("OCI_COMPARTMENT_ID"):
        load_workshop_env()


@app.on_event("startup")
def startup() -> None:
    ensure_env_loaded()


def message_content_to_text(content: str | list[Any] | None) -> str:
    """Convert OpenAI-style message content into simple text for the OCI prompt."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts = []
    for item in content:
        if isinstance(item, dict):
            if item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif item.get("text"):
                parts.append(str(item["text"]))
    return "\n".join(part for part in parts if part)


def messages_to_prompt(messages: list[ChatMessage]) -> str:
    """Flatten chat messages into a prompt that works across OCI chat providers."""
    prompt_parts = []
    for message in messages:
        role = message.role.upper()
        text = message_content_to_text(message.content).strip()
        if text:
            prompt_parts.append(f"{role}:\n{text}")
    prompt_parts.append("ASSISTANT:")
    return "\n\n".join(prompt_parts)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "OCI Generative AI OpenAI-compatible workshop gateway",
    }


@app.get("/health")
def health() -> dict[str, str]:
    ensure_env_loaded()
    return {
        "status": "ok",
        "chat_model": os.getenv("CHAT_MODEL_ID", ""),
        "endpoint": os.getenv("GENAI_ENDPOINT", ""),
    }


@app.get("/v1/models")
def list_models() -> dict[str, Any]:
    ensure_env_loaded()
    model_ids = [
        model_id
        for model_id in [os.getenv("CHAT_MODEL_ID"), os.getenv("EMBED_MODEL_ID")]
        if model_id
    ]
    return {
        "object": "list",
        "data": [
            {
                "id": model_id,
                "object": "model",
                "created": 0,
                "owned_by": "oci-generative-ai",
            }
            for model_id in model_ids
        ],
    }


@app.post("/v1/chat/completions")
def chat_completions(request: ChatCompletionRequest) -> dict[str, Any]:
    ensure_env_loaded()
    if request.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming is not implemented in the workshop gateway.",
        )
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    model = request.model or os.environ["CHAT_MODEL_ID"]
    if model != os.environ["CHAT_MODEL_ID"]:
        raise HTTPException(
            status_code=400,
            detail=f"This workshop gateway is configured for {os.environ['CHAT_MODEL_ID']}",
        )

    prompt = messages_to_prompt(request.messages)
    client = create_genai_client()
    content = chat_once(client, prompt)

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        },
    }


if __name__ == "__main__":
    import uvicorn

    load_workshop_env()
    uvicorn.run(
        "workshop_gateway.app:app",
        host=os.getenv("GATEWAY_HOST", "localhost"),
        port=int(os.getenv("GATEWAY_PORT", "8088")),
        reload=False,
    )
