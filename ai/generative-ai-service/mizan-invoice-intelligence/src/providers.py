"""Model adapters for imported DAC and on-demand invoice extraction.

Author: Ali Ottoman
"""

from __future__ import annotations

import base64
import json
import re
from typing import Any, Protocol

import httpx
import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ChatDetails,
    DedicatedServingMode,
    GenericChatRequest,
    ImageContent,
    ImageUrl,
    JsonSchemaResponseFormat,
    Message,
    ResponseJsonSchema,
    TextContent,
)
from openai import OpenAI
from pydantic import ValidationError

import config

from .models import InvoiceExtraction
from .prompts import SYSTEM_PROMPT

Usage = tuple[int, int]


class InvoiceProvider(Protocol):
    """Small shared contract used by the extraction workflow."""

    def invoke(
        self, prompt: str, images: list[bytes]
    ) -> tuple[InvoiceExtraction, Usage]: ...


class DedicatedProvider:
    """Call an imported multimodal model through its DAC endpoint OCID."""

    def __init__(self, settings: config.Settings):
        self.settings = settings
        oci_config = oci.config.from_file(
            file_location=settings.oci_config_file or oci.config.DEFAULT_LOCATION,
            profile_name=settings.oci_profile,
        )
        self.client = GenerativeAiInferenceClient(
            config=oci_config,
            service_endpoint=settings.service_endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, settings.request_timeout_seconds),
        )

    def invoke(
        self, prompt: str, images: list[bytes]
    ) -> tuple[InvoiceExtraction, Usage]:
        """Prefer JSON Schema, then retry without it when unsupported."""

        try:
            return self._chat(prompt, images, structured=self.settings.use_json_schema)
        except oci.exceptions.ServiceError as exc:
            if self.settings.use_json_schema and _schema_rejected(exc):
                return self._chat(prompt, images, structured=False)
            raise

    def _chat(
        self, prompt: str, images: list[bytes], *, structured: bool
    ) -> tuple[InvoiceExtraction, Usage]:
        if not structured:
            prompt = _with_schema(prompt)
        content: list[Any] = [TextContent(text=prompt)]
        for index, image in enumerate(images, start=1):
            content.append(TextContent(text=f"PAGE {index} IMAGE"))
            content.append(ImageContent(image_url=ImageUrl(url=_data_url(image))))

        request: dict[str, Any] = {
            "api_format": GenericChatRequest.API_FORMAT_GENERIC,
            "messages": [
                Message(role="SYSTEM", content=[TextContent(text=SYSTEM_PROMPT)]),
                Message(role="USER", content=content),
            ],
            "max_tokens": self.settings.max_tokens,
            "temperature": 0,
            "top_p": 1,
            "is_stream": False,
        }
        if structured:
            request["response_format"] = JsonSchemaResponseFormat(
                json_schema=ResponseJsonSchema(
                    name="invoice_extraction",
                    description="A complete, source-grounded invoice extraction.",
                    schema=InvoiceExtraction.model_json_schema(),
                    is_strict=True,
                )
            )

        details = ChatDetails(
            compartment_id=self.settings.compartment_id,
            serving_mode=DedicatedServingMode(
                endpoint_id=self.settings.dac_endpoint_id
            ),
            chat_request=GenericChatRequest(**request),
        )
        response = self.client.chat(details)
        chat_response = response.data.chat_response
        result = _validate_payload(_parse_json(_native_response_text(chat_response)))
        usage = getattr(chat_response, "usage", None)
        return result, (
            int(getattr(usage, "prompt_tokens", 0) or 0),
            int(getattr(usage, "completion_tokens", 0) or 0),
        )


class OnDemandProvider:
    """Call an on-demand model through OCI's Responses API."""

    def __init__(self, settings: config.Settings):
        self.settings = settings
        client_options: dict[str, Any] = {
            "base_url": settings.responses_base_url,
            "project": settings.on_demand_project_id,
            "timeout": settings.request_timeout_seconds,
            "max_retries": 0,
        }
        if settings.on_demand_api_key.strip():
            self.client = OpenAI(
                api_key=settings.on_demand_api_key,
                **client_options,
            )
            return

        try:
            from oci_genai_auth import OciUserPrincipalAuth
        except ImportError as exc:
            raise RuntimeError(
                "Set OPENAI_API_KEY_CHICAGO or install oci-genai-auth for "
                "on-demand inference."
            ) from exc

        auth = OciUserPrincipalAuth(
            config_file=settings.oci_config_file or "~/.oci/config",
            profile_name=settings.oci_profile,
        )
        http_client = httpx.Client(auth=auth)
        self.client = OpenAI(
            api_key="oci-iam-signing",
            http_client=http_client,
            **client_options,
        )

    def invoke(
        self, prompt: str, images: list[bytes]
    ) -> tuple[InvoiceExtraction, Usage]:
        """Use structured output when available and retain a validated fallback."""

        try:
            return self._respond(
                prompt, images, structured=self.settings.use_json_schema
            )
        except Exception as exc:
            if self.settings.use_json_schema and _schema_rejected(exc):
                return self._respond(prompt, images, structured=False)
            raise

    def _respond(
        self, prompt: str, images: list[bytes], *, structured: bool
    ) -> tuple[InvoiceExtraction, Usage]:
        content: list[dict[str, Any]] = [
            {
                "type": "input_text",
                "text": prompt if structured else _with_schema(prompt),
            }
        ]
        for index, image in enumerate(images, start=1):
            content.extend(
                [
                    {"type": "input_text", "text": f"PAGE {index} IMAGE"},
                    {
                        "type": "input_image",
                        "image_url": _data_url(image),
                        "detail": "high",
                    },
                ]
            )
        common: dict[str, Any] = {
            "model": self.settings.on_demand_model_id,
            "instructions": SYSTEM_PROMPT,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": self.settings.max_tokens,
            "temperature": 0,
            "store": False,
        }
        if structured:
            response = self.client.responses.parse(
                **common,
                text_format=InvoiceExtraction,
            )
            result = response.output_parsed
            if result is None:
                raw = (getattr(response, "output_text", "") or "").strip()
                if not raw:
                    raise ValueError(
                        "The on-demand model returned no structured invoice."
                    )
                result = _validate_payload(_parse_json(raw))
        else:
            response = self.client.responses.create(**common)
            result = _validate_payload(_parse_json(response.output_text))

        usage = getattr(response, "usage", None)
        return result, (
            int(getattr(usage, "input_tokens", 0) or 0),
            int(getattr(usage, "output_tokens", 0) or 0),
        )


def build_provider(settings: config.Settings) -> InvoiceProvider:
    """Create only the adapter selected in the application controls."""

    if settings.inference_mode == "on_demand":
        return OnDemandProvider(settings)
    return DedicatedProvider(settings)


def _data_url(image: bytes) -> str:
    encoded = base64.b64encode(image).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def _with_schema(prompt: str) -> str:
    schema = json.dumps(
        InvoiceExtraction.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return f"{prompt}\n\nRequired JSON Schema (return this object only):\n{schema}"


def _schema_rejected(exc: Exception) -> bool:
    status = getattr(exc, "status", None) or getattr(exc, "status_code", None)
    details = f"{getattr(exc, 'code', '')} {exc}".lower()
    markers = ("schema", "response_format", "response format", "responseformat")
    return status in {400, 422} and any(marker in details for marker in markers)


def _native_response_text(chat_response: Any) -> str:
    choices = getattr(chat_response, "choices", None) or []
    if not choices:
        raise ValueError("The dedicated endpoint returned no choices.")
    parts = getattr(choices[0].message, "content", None) or []
    text = "".join(getattr(part, "text", "") or "" for part in parts).strip()
    if not text:
        raise ValueError("The dedicated endpoint returned an empty response.")
    return text


def _parse_json(raw: str) -> dict:
    """Read one JSON object without brittle brace slicing."""

    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.DOTALL)
    candidate = fenced.group(1).strip() if fenced else raw.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        decoder = json.JSONDecoder()
        if start < 0:
            raise ValueError("The model response did not contain a JSON object.")
        try:
            value, _ = decoder.raw_decode(candidate[start:])
        except json.JSONDecodeError as exc:
            raise ValueError("The model returned malformed JSON.") from exc
    if not isinstance(value, dict):
        raise TypeError("The model response must be one JSON object.")
    return value


def _validate_payload(payload: dict) -> InvoiceExtraction:
    try:
        return InvoiceExtraction.model_validate(payload)
    except ValidationError as exc:
        raise ValueError(
            "The model JSON does not match the invoice contract: "
            f"{exc.error_count()} validation issue(s)."
        ) from exc
