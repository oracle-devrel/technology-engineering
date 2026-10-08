"""One chat client for every model in the registry — on-demand or dedicated.

Selects the serving mode from a `ModelSpec`, targets the regional service
endpoint, sends text + images (base64 data URIs), and returns a `ChatResult`
with text, log-probs, token usage and finish_reason. Cohere models use their
own request format; everything else goes through the GENERIC chat request.

Errors are captured into `ChatResult.error` rather than raised, so a batch of
verification calls reports failures per candidate instead of aborting.
"""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ChatDetails,
    CohereChatRequestV2,
    CohereImageContentV2,
    CohereImageUrlV2,
    CohereResponseJsonFormat,
    CohereTextContentV2,
    CohereUserMessageV2,
    DedicatedServingMode,
    GenericChatRequest,
    ImageContent,
    ImageUrl,
    JsonObjectResponseFormat,
    JsonSchemaResponseFormat,
    Message,
    OnDemandServingMode,
    ResponseJsonSchema,
    TextContent,
)

from doccompare.models.registry import ModelSpec

# cache one OCI SDK client per (region, profile) — cheap reuse across models
_CLIENT_CACHE: dict[tuple[str, str], GenerativeAiInferenceClient] = {}


def _sdk_client(spec: ModelSpec, timeout: tuple[int, int]) -> GenerativeAiInferenceClient:
    key = (spec.service_endpoint, spec.config_profile)
    cli = _CLIENT_CACHE.get(key)
    if cli is None:
        config = oci.config.from_file("~/.oci/config", spec.config_profile)
        cli = GenerativeAiInferenceClient(
            config=config,
            service_endpoint=spec.service_endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=timeout,
        )
        _CLIENT_CACHE[key] = cli
    return cli


def _data_uri(image: bytes | str | Path, mime: str = "image/png") -> str:
    data = Path(image).read_bytes() if isinstance(image, (str, Path)) else image
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


@dataclass
class ChatResult:
    slug: str
    text: str = ""
    error: str | None = None
    finish_reason: str | None = None
    logprobs: object | None = None      # raw logprobs payload if the server returned one
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    latency_s: float | None = None
    raw: object = field(default=None, repr=False)

    @property
    def ok(self) -> bool:
        return self.error is None


class ModelClient:
    def __init__(self, spec: ModelSpec, *, timeout: tuple[int, int] = (10, 300)):
        self.spec = spec
        self._client = _sdk_client(spec, timeout)
        # Cohere models on OCI reject GenericChatRequest ("Chat request type does
        # not match serving model") — they need the Cohere-native V2 format.
        self._is_cohere = (spec.model_id or "").startswith("cohere.")

    def _serving_mode(self):
        if self.spec.mode == "dedicated":
            return DedicatedServingMode(endpoint_id=self.spec.endpoint_ocid)
        return OnDemandServingMode(model_id=self.spec.model_id)

    def _build_cohere_request(self, *, prompt, images, max_tokens, temperature,
                              top_p, seed, json_mode, json_schema, log_probs):
        content = [CohereTextContentV2(type="TEXT", text=prompt)]
        for img in images:
            content.append(CohereImageContentV2(
                type="IMAGE_URL", image_url=CohereImageUrlV2(url=_data_uri(img))))
        req = CohereChatRequestV2()
        req.messages = [CohereUserMessageV2(role="USER", content=content)]
        req.max_tokens = max_tokens
        req.temperature = temperature
        req.top_p = top_p
        if seed is not None:
            req.seed = seed
        if log_probs is not None:
            req.is_log_probs_enabled = True
        if json_mode:
            req.response_format = CohereResponseJsonFormat(
                type="JSON_OBJECT", schema=json_schema)
        return req

    def _build_generic_request(self, *, prompt, images, system, max_tokens,
                               temperature, top_p, seed, json_mode, json_schema,
                               json_schema_name, log_probs, reasoning_effort):
        content: list = []
        for img in images:
            content.append(ImageContent(image_url=ImageUrl(url=_data_uri(img))))
        content.append(TextContent(text=prompt))
        messages = []
        if system:
            messages.append(Message(role=Message.ROLE_SYSTEM, content=[TextContent(text=system)]))
        messages.append(Message(role=Message.ROLE_USER, content=content))
        req = GenericChatRequest()  # api_format defaults to GENERIC
        req.messages = messages
        req.max_tokens = max_tokens
        req.temperature = temperature
        req.top_p = top_p
        if seed is not None:
            req.seed = seed
        if log_probs is not None:
            req.log_probs = log_probs
        if reasoning_effort is not None:
            req.reasoning_effort = reasoning_effort
        if json_mode:
            if json_schema is not None:
                req.response_format = JsonSchemaResponseFormat(
                    json_schema=ResponseJsonSchema(
                        name=json_schema_name, schema=json_schema, is_strict=False))
            else:
                req.response_format = JsonObjectResponseFormat()
        return req

    def chat(
        self,
        *,
        prompt: str,
        images: Iterable[bytes | str | Path] = (),
        system: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.0,
        top_p: float = 1.0,
        seed: int | None = 7,
        json_mode: bool = False,
        json_schema: dict | None = None,
        json_schema_name: str = "extraction",
        log_probs: int | None = None,
        reasoning_effort: str | None = None,
    ) -> ChatResult:
        if self._is_cohere:
            req = self._build_cohere_request(
                prompt=prompt, images=images, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p, seed=seed,
                json_mode=json_mode, json_schema=json_schema, log_probs=log_probs)
        else:
            req = self._build_generic_request(
                prompt=prompt, images=images, system=system, max_tokens=max_tokens,
                temperature=temperature, top_p=top_p, seed=seed, json_mode=json_mode,
                json_schema=json_schema, json_schema_name=json_schema_name,
                log_probs=log_probs, reasoning_effort=reasoning_effort)

        detail = ChatDetails()
        detail.serving_mode = self._serving_mode()
        detail.chat_request = req
        detail.compartment_id = self.spec.compartment_id

        t0 = time.time()
        try:
            resp = self._client.chat(detail)
        except Exception as e:  # noqa: BLE001 — tabulate, don't abort the matrix
            return ChatResult(
                slug=self.spec.slug,
                error=f"{type(e).__name__}: {e}",
                latency_s=round(time.time() - t0, 2),
            )
        dt = round(time.time() - t0, 2)
        return _parse_response(self.spec.slug, resp, dt)


def _parse_response(slug: str, resp, latency_s: float) -> ChatResult:
    data = getattr(resp, "data", resp)
    chat_response = getattr(data, "chat_response", data)
    text, finish, logprobs = "", None, None

    choices = getattr(chat_response, "choices", None) or []
    if choices:
        # GENERIC format (Gemma / Gemini / Grok): choices[0].message.content[]
        choice = choices[0]
        finish = getattr(choice, "finish_reason", None)
        logprobs = getattr(choice, "logprobs", None)
        msg = getattr(choice, "message", None)
        for part in (getattr(msg, "content", None) or []):
            t = getattr(part, "text", None)
            if t:
                text += t
    elif getattr(chat_response, "message", None) is not None:
        # COHERE V2 format: chat_response.message.content[], finish_reason &
        # log_probabilities hang off chat_response directly.
        finish = getattr(chat_response, "finish_reason", None)
        logprobs = getattr(chat_response, "log_probabilities", None)
        msg = chat_response.message
        for part in (getattr(msg, "content", None) or []):
            t = getattr(part, "text", None)
            if t:
                text += t

    usage = getattr(chat_response, "usage", None)
    return ChatResult(
        slug=slug,
        text=text,
        finish_reason=finish,
        logprobs=logprobs,
        prompt_tokens=getattr(usage, "prompt_tokens", None) if usage else None,
        completion_tokens=getattr(usage, "completion_tokens", None) if usage else None,
        latency_s=latency_s,
        raw=resp,
    )


def client_for(spec: ModelSpec, **kw) -> ModelClient:
    return ModelClient(spec, **kw)
