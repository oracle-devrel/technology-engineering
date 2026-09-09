# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0

import base64
import time
from dataclasses import dataclass
from typing import Any
from pathlib import Path

from langchain_core.messages import HumanMessage
from langchain_oci import ChatOCIGenAI

from .model_catalog import get_supported_model_ids, is_supported_public_model_id

@dataclass
class VideoAnalysisResult:
    output: str
    metadata: dict[str, Any]


class VideoAnalysisConfigurationError(ValueError):
    """Raised when required non-secret OCI settings are missing or invalid."""


def _to_plain_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}

    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump(exclude_none=True)

    if hasattr(value, "dict"):
        return value.dict()

    return {}


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, str | int | float | bool):
        return value

    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}

    if isinstance(value, list | tuple | set):
        return [_json_safe(item) for item in value]

    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(exclude_none=True))

    if hasattr(value, "dict"):
        return _json_safe(value.dict())

    return str(value)


def _first_number(*values: Any) -> int | float | None:
    for value in values:
        if isinstance(value, bool):
            continue

        if isinstance(value, int | float):
            return value

    return None


def _extract_token_metadata(
    usage_metadata: dict[str, Any], response_metadata: dict[str, Any]
) -> dict[str, int | float | None]:
    token_usage = response_metadata.get("token_usage")
    if not isinstance(token_usage, dict):
        token_usage = {}

    usage = response_metadata.get("usage")
    if not isinstance(usage, dict):
        usage = {}

    return {
        "input_tokens": _first_number(
            usage_metadata.get("input_tokens"),
            usage_metadata.get("prompt_tokens"),
            token_usage.get("prompt_tokens"),
            token_usage.get("input_tokens"),
            usage.get("prompt_tokens"),
            usage.get("input_tokens"),
        ),
        "output_tokens": _first_number(
            usage_metadata.get("output_tokens"),
            usage_metadata.get("completion_tokens"),
            token_usage.get("completion_tokens"),
            token_usage.get("output_tokens"),
            usage.get("completion_tokens"),
            usage.get("output_tokens"),
        ),
    }


def analyze_video_with_oci_gemini(
    video_path: str | Path,
    prompt: str,
    model_id: str,
    mime_type: str,
    compartment_id: str,
    service_endpoint: str,
    auth_profile: str,
    auth_file_location: str,
) -> VideoAnalysisResult:
    """Analyze a local video file with Gemini on OCI GenAI through langchain-oci."""
    clean_prompt = prompt.strip()
    clean_model_id = model_id.strip()
    clean_compartment_id = compartment_id.strip()
    clean_service_endpoint = service_endpoint.strip()
    clean_mime_type = (mime_type or "video/mp4").strip()
    clean_auth_profile = auth_profile.strip() or "DEFAULT"
    clean_auth_file_location = auth_file_location.strip() or "~/.oci/config"

    if not clean_prompt:
        raise VideoAnalysisConfigurationError("Prompt is required.")

    is_model_ocid = clean_model_id.startswith("ocid1.")

    if not is_model_ocid and not is_supported_public_model_id(clean_model_id):
        supported = ", ".join(sorted(get_supported_model_ids()))
        raise VideoAnalysisConfigurationError(
            f"Unsupported model_id '{clean_model_id}'. Supported model IDs: {supported}, "
            "or provide a valid model OCID."
        )

    if not clean_compartment_id:
        raise VideoAnalysisConfigurationError("OCI compartment OCID is required.")

    if not clean_service_endpoint:
        raise VideoAnalysisConfigurationError("OCI GenAI service endpoint is required.")

    source_path = Path(video_path)
    if not source_path.exists() or not source_path.is_file():
        raise VideoAnalysisConfigurationError("Uploaded video file was not found.")

    try:
        video_data = base64.b64encode(source_path.read_bytes()).decode("utf-8")

        message = HumanMessage(
            content=[
                {"type": "text", "text": clean_prompt},
                {
                    "type": "media",
                    "data": video_data,
                    "mime_type": clean_mime_type,
                },
            ]
        )

        llm = ChatOCIGenAI(
            model_id=clean_model_id,
            service_endpoint=clean_service_endpoint,
            compartment_id=clean_compartment_id,
            auth_type="API_KEY",
            auth_profile=clean_auth_profile,
            auth_file_location=clean_auth_file_location,
        )

        start_time = time.perf_counter()
        response = llm.invoke([message])
        latency_ms = round((time.perf_counter() - start_time) * 1000)
        usage_metadata = _json_safe(_to_plain_dict(getattr(response, "usage_metadata", None)))
        response_metadata = _json_safe(
            _to_plain_dict(getattr(response, "response_metadata", None))
        )
        token_metadata = _extract_token_metadata(usage_metadata, response_metadata)

        return VideoAnalysisResult(
            output=str(response.content),
            metadata={
                "latency_ms": latency_ms,
                "input_tokens": token_metadata["input_tokens"],
                "output_tokens": token_metadata["output_tokens"],
            },
        )
    except VideoAnalysisConfigurationError:
        raise
    except Exception as exc:
        raise RuntimeError(
            "OCI GenAI video analysis failed with API key profile authentication. "
            f"Confirm OCI config profile '{clean_auth_profile}', config file path "
            f"'{clean_auth_file_location}', compartment, endpoint, region, and model ID."
        ) from exc
