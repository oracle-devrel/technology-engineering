# Copyright (c) 2026 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/.

from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import oci
from dotenv import load_dotenv
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ChatDetails,
    CohereChatRequest,
    GenericChatRequest,
    OnDemandServingMode,
    TextContent,
    UserMessage,
)


warnings.filterwarnings(
    "ignore",
    message="The 'strict' parameter is no longer needed*",
    category=FutureWarning,
    module="urllib3.poolmanager",
)


def find_upwards(filename: str, start: Path | None = None) -> Path | None:
    """Find a file in the current directory or one of its parents."""
    current = (start or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / filename
        if candidate.exists():
            return candidate
    return None


def load_workshop_env(filename: str = ".env") -> Path:
    """Load workshop environment variables from the repo-level .env file."""
    env_path = find_upwards(filename)
    if env_path is None:
        raise FileNotFoundError(
            "Could not find a .env file. Copy .env.example to .env at the "
            "repository root, then fill in your OCI values."
        )

    load_dotenv(env_path)
    return env_path


def mask(value: str | None, visible: int = 8) -> str:
    """Mask an identifier before printing it in notebook output."""
    if not value:
        return "<missing>"
    if len(value) <= visible:
        return "*" * len(value)
    return f"{value[:visible]}..."


def load_oci_config() -> dict:
    """Load and validate OCI SDK config using OCI_CONFIG_FILE and OCI_PROFILE."""
    config = oci.config.from_file(
        file_location=os.path.expanduser(os.getenv("OCI_CONFIG_FILE", "~/.oci/config")),
        profile_name=os.getenv("OCI_PROFILE", "DEFAULT"),
    )
    oci.config.validate_config(config)
    return config


def create_genai_client() -> GenerativeAiInferenceClient:
    """Create an OCI Generative AI Inference client from local config-file auth."""
    return GenerativeAiInferenceClient(
        config=load_oci_config(),
        service_endpoint=os.environ["GENAI_ENDPOINT"],
        timeout=(10, 240),
    )


def get_chat_max_tokens() -> int:
    return int(os.getenv("CHAT_MAX_TOKENS", "1024"))


def get_chat_max_completion_tokens() -> int:
    return int(os.getenv("CHAT_MAX_COMPLETION_TOKENS", "8192"))


def build_chat_request(message: str):
    """Build either a Cohere-style or generic chat request from .env settings."""
    request_format = os.getenv("CHAT_REQUEST_FORMAT", "COHERE").upper()

    if request_format == "GENERIC":
        return GenericChatRequest(
            api_format="GENERIC",
            messages=[
                UserMessage(
                    role="USER",
                    content=[TextContent(type="TEXT", text=message)],
                )
            ],
            max_tokens=get_chat_max_tokens(),
            max_completion_tokens=get_chat_max_completion_tokens(),
            reasoning_effort=os.getenv("CHAT_REASONING_EFFORT", "LOW").upper(),
            temperature=0.2,
            top_p=0.75,
        )

    if request_format != "COHERE":
        raise ValueError("CHAT_REQUEST_FORMAT must be COHERE or GENERIC")

    return CohereChatRequest(
        api_format="COHERE",
        message=message,
        max_tokens=get_chat_max_tokens(),
        temperature=0.2,
        top_p=0.75,
    )


def extract_text_from_chat_response(response_data) -> str:
    """Return visible assistant text from common OCI chat response shapes."""
    payload = oci.util.to_dict(response_data)
    chat_response = payload.get("chat_response", {})

    def text_from_content(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("text"):
                        parts.append(item["text"])
                    elif item.get("content"):
                        nested_text = text_from_content(item["content"])
                        if nested_text:
                            parts.append(nested_text)
            return "".join(parts) if parts else None
        return None

    if isinstance(chat_response, dict):
        if chat_response.get("text"):
            return chat_response["text"]

        direct_content = text_from_content(chat_response.get("content"))
        if direct_content:
            return direct_content

        choices = chat_response.get("choices") or []
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            if choice.get("text"):
                return choice["text"]

            message = choice.get("message") or choice.get("delta") or {}
            if isinstance(message, dict):
                content = text_from_content(message.get("content"))
                if content:
                    return content

            content = text_from_content(choice.get("content"))
            if content:
                return content

        finish_reason = choices[0].get("finish_reason") if choices else None
        usage = chat_response.get("usage") or {}
        details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = details.get("reasoning_tokens")

        if finish_reason == "max_tokens":
            raise RuntimeError(
                "The model stopped before returning visible text because it reached "
                "the completion-token limit. For Gemini 2.5, increase "
                "CHAT_MAX_COMPLETION_TOKENS in .env, for example to 8192 or 16384. "
                f"Reasoning tokens used: {reasoning_tokens}."
            )

    return json.dumps(payload, indent=2)[:2000]


def chat_once(genai_client: GenerativeAiInferenceClient, message: str) -> str:
    """Send one prompt to the configured OCI Generative AI chat model."""
    chat_details = ChatDetails(
        compartment_id=os.environ["OCI_COMPARTMENT_ID"],
        serving_mode=OnDemandServingMode(
            serving_type="ON_DEMAND",
            model_id=os.environ["CHAT_MODEL_ID"],
        ),
        chat_request=build_chat_request(message),
    )
    response = genai_client.chat(chat_details)
    return extract_text_from_chat_response(response.data)
