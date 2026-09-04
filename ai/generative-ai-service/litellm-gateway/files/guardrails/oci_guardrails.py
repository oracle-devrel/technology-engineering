#!/usr/bin/env python3
"""
OCI Guardrails for the LiteLLM Gateway.

Wraps the OCI Generative AI `apply_guardrails` API in a LiteLLM
CustomGuardrail so any model behind the gateway - OCI on-demand, DAC
imported, or external providers - gets the same protections:

  - content moderation (toxic / unsafe content)   -> block | log
  - prompt injection detection                    -> block | log
  - PII detection (EMAIL, TELEPHONE_NUMBER, ...)  -> mask | block | log

Registered in config.yaml under `guardrails:`; per-request opt-in via
    extra_body={"guardrails": ["oci-guardrails"]}
or enforced globally with `default_on: true`.

Modes:
  pre_call  - checks/masks user messages before they reach the model
  post_call - checks/masks the model response before it reaches the client
"""

import asyncio
import os
from typing import Any, Literal, Optional, Union

from fastapi import HTTPException

import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ApplyGuardrailsDetails,
    ContentModerationConfiguration,
    GuardrailConfigs,
    GuardrailsTextInput,
    PersonallyIdentifiableInformationConfiguration,
    PromptInjectionConfiguration,
)

from litellm._logging import verbose_proxy_logger
from litellm.caching.caching import DualCache
from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.proxy._types import UserAPIKeyAuth
from litellm.types.guardrails import GuardrailEventHooks

DEFAULT_PII_TYPES = ["EMAIL", "TELEPHONE_NUMBER", "ADDRESS", "PERSON"]


def _env(value: Optional[str], var: Optional[str] = None) -> Optional[str]:
    """Resolve 'os.environ/NAME' placeholders that LiteLLM did not expand."""
    if isinstance(value, str) and value.startswith("os.environ/"):
        value = os.getenv(value.split("/", 1)[1])
    if value is None and var:
        value = os.getenv(var)
    return value


class OCIGuardrail(CustomGuardrail):
    def __init__(
        self,
        compartment_id: Optional[str] = None,
        region: Optional[str] = None,
        auth_type: str = "api_key",  # api_key | instance_principal
        oci_config_file: str = "~/.oci/config",
        oci_profile: str = "DEFAULT",
        content_moderation: Optional[dict] = None,
        prompt_injection: Optional[dict] = None,
        pii: Optional[dict] = None,
        language_code: str = "en",
        **kwargs,
    ):
        self.compartment_id = _env(compartment_id, "OCI_COMPARTMENT_ID")
        self.region = _env(region, "OCI_REGION") or "us-chicago-1"
        self.auth_type = _env(auth_type) or "api_key"
        self.oci_config_file = _env(oci_config_file) or "~/.oci/config"
        self.oci_profile = _env(oci_profile) or "DEFAULT"
        self.language_code = language_code
        self.content_moderation = content_moderation or {}
        self.prompt_injection = prompt_injection or {}
        self.pii = pii or {}
        self._client: Optional[GenerativeAiInferenceClient] = None
        super().__init__(**kwargs)

    # ------------------------------------------------------------------ #
    # OCI client + apply_guardrails                                      #
    # ------------------------------------------------------------------ #
    def _get_client(self) -> GenerativeAiInferenceClient:
        if self._client is None:
            endpoint = (
                f"https://inference.generativeai.{self.region}.oci.oraclecloud.com"
            )
            if self.auth_type == "instance_principal":
                signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
                self._client = GenerativeAiInferenceClient(
                    config={}, signer=signer, service_endpoint=endpoint
                )
            elif os.getenv("OCI_USER"):
                # Same env vars the `oci/` models in config.yaml use - works in
                # the container, where there is no ~/.oci/config file.
                config = {
                    "user": os.environ["OCI_USER"],
                    "tenancy": os.environ["OCI_TENANCY"],
                    "fingerprint": os.environ["OCI_FINGERPRINT"],
                    "key_file": os.environ["OCI_KEY_FILE"],
                    "region": self.region,
                }
                oci.config.validate_config(config)
                self._client = GenerativeAiInferenceClient(
                    config=config, service_endpoint=endpoint
                )
            else:
                config = oci.config.from_file(self.oci_config_file, self.oci_profile)
                self._client = GenerativeAiInferenceClient(
                    config=config, service_endpoint=endpoint
                )
        return self._client

    def _apply(self, text: str):
        """Call the OCI apply_guardrails API (sync - run in a thread)."""
        configs = GuardrailConfigs()
        if self.content_moderation.get("enabled"):
            configs.content_moderation_config = ContentModerationConfiguration(
                categories=["OVERALL"]
            )
        if self.pii.get("enabled"):
            configs.personally_identifiable_information_config = (
                PersonallyIdentifiableInformationConfiguration(
                    types=self.pii.get("types", DEFAULT_PII_TYPES)
                )
            )
        if self.prompt_injection.get("enabled"):
            configs.prompt_injection_config = PromptInjectionConfiguration()

        response = self._get_client().apply_guardrails(
            apply_guardrails_details=ApplyGuardrailsDetails(
                input=GuardrailsTextInput(
                    type="TEXT", content=text, language_code=self.language_code
                ),
                guardrail_configs=configs,
                compartment_id=self.compartment_id,
            )
        )
        return response.data

    # ------------------------------------------------------------------ #
    # Enforcement                                                        #
    # ------------------------------------------------------------------ #
    def _enforce(self, text: str, result: Any) -> str:
        """Apply thresholds/actions to a guardrail result. Returns the
        (possibly masked) text, or raises HTTPException on block."""
        r = getattr(result, "results", None)
        if r is None:
            return text
        masked = text

        cm = self.content_moderation
        if cm.get("enabled") and getattr(r, "content_moderation", None):
            threshold = cm.get("threshold", 0.9)
            for cat in r.content_moderation.categories:
                if cat.name == "OVERALL" and cat.score >= threshold:
                    if cm.get("action", "block") == "block":
                        raise HTTPException(
                            status_code=400,
                            detail={
                                "error": "Blocked by OCI Guardrails: content moderation",
                                "guardrail": self.guardrail_name,
                                "score": cat.score,
                            },
                        )
                    verbose_proxy_logger.warning(
                        "OCI Guardrails: unsafe content detected (score=%s)", cat.score
                    )

        pi = self.prompt_injection
        if pi.get("enabled") and getattr(r, "prompt_injection", None):
            score = r.prompt_injection.score
            if score >= pi.get("threshold", 0.9):
                if pi.get("action", "block") == "block":
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": "Blocked by OCI Guardrails: prompt injection",
                            "guardrail": self.guardrail_name,
                            "score": score,
                        },
                    )
                verbose_proxy_logger.warning(
                    "OCI Guardrails: prompt injection detected (score=%s)", score
                )

        pii = self.pii
        entities = getattr(r, "personally_identifiable_information", None)
        if pii.get("enabled") and entities:
            threshold = pii.get("threshold", 0.9)
            action = pii.get("action", "mask")
            for entity in entities:
                if entity.score < threshold:
                    continue
                if action == "block":
                    raise HTTPException(
                        status_code=400,
                        detail={
                            "error": f"Blocked by OCI Guardrails: PII detected ({entity.label})",
                            "guardrail": self.guardrail_name,
                        },
                    )
                if action == "mask":
                    masked = masked.replace(entity.text, f"[{entity.label}_REDACTED]")
                else:
                    verbose_proxy_logger.warning(
                        "OCI Guardrails: PII detected (%s)", entity.label
                    )
        return masked

    async def _check_text(self, text: str) -> str:
        if not text or not text.strip():
            return text
        result = await asyncio.to_thread(self._apply, text)
        return self._enforce(text, result)

    # ------------------------------------------------------------------ #
    # LiteLLM hooks                                                      #
    # ------------------------------------------------------------------ #
    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: DualCache,
        data: dict,
        call_type: str,
    ) -> Optional[Union[Exception, str, dict]]:
        """Check/mask every user message before it reaches the model."""
        if self.should_run_guardrail(data=data, event_type=GuardrailEventHooks.pre_call) is not True:
            return data

        for message in data.get("messages", []):
            if message.get("role") != "user":
                continue
            content = message.get("content")
            if isinstance(content, str):
                message["content"] = await self._check_text(content)
            elif isinstance(content, list):  # multimodal content blocks
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        part["text"] = await self._check_text(part.get("text", ""))
        return data

    async def async_moderation_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        call_type: Literal["completion", "embeddings", "image_generation",
                           "moderation", "audio_transcription", "responses"],
    ):
        """`during_call` mode: check in parallel with the LLM call (block only,
        no masking - the request is already in flight)."""
        if self.should_run_guardrail(data=data, event_type=GuardrailEventHooks.during_call) is not True:
            return
        for message in data.get("messages", []):
            if message.get("role") == "user" and isinstance(message.get("content"), str):
                await self._check_text(message["content"])

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        response,
    ):
        """Check/mask the model response (post_call mode)."""
        if self.should_run_guardrail(data=data, event_type=GuardrailEventHooks.post_call) is not True:
            return response

        for choice in getattr(response, "choices", []) or []:
            message = getattr(choice, "message", None)
            if message is not None and isinstance(message.content, str):
                message.content = await self._check_text(message.content)
        return response
