"""Runtime configuration for Mizan Invoice Intelligence.

Author: Ali Ottoman
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
SAMPLE_INVOICE = PROJECT_ROOT / "sample_invoice.pdf"

InferenceMode = Literal["dac", "on_demand"]

DEFAULT_DAC_MODEL_ID = "Qwen/Qwen3.6-35B-A3B"
DEFAULT_DAC_MODEL_LABEL = "Qwen 3.6 35B A3B"
DEFAULT_ON_DEMAND_MODEL_ID = "google.gemini-2.5-pro"


@dataclass(frozen=True)
class ModelOption:
    id: str
    label: str
    note: str


ON_DEMAND_MODELS = (
    ModelOption(
        id="google.gemini-2.5-pro",
        label="Gemini 2.5 Pro",
        note="Recommended · document understanding and structured extraction",
    ),
    ModelOption(
        id="xai.grok-4.3",
        label="Grok 4.3",
        note="Challenger · strong reasoning with image and structured output",
    ),
)


def on_demand_model(model_id: str) -> ModelOption:
    """Resolve one UI model choice without allowing its label to drift."""

    return next(
        (option for option in ON_DEMAND_MODELS if option.id == model_id),
        ModelOption(id=model_id, label=model_id, note="Custom on-demand model"),
    )


@dataclass(frozen=True)
class Settings:
    region: str
    service_endpoint: str
    responses_base_url: str
    compartment_id: str
    dac_endpoint_id: str
    dac_model_id: str
    dac_model_label: str
    on_demand_project_id: str
    on_demand_api_key: str
    on_demand_model_id: str
    on_demand_model_label: str
    inference_mode: InferenceMode
    oci_profile: str
    oci_config_file: str | None
    max_tokens: int
    request_timeout_seconds: int
    pdf_dpi: int
    max_pages: int
    max_image_dimension: int
    jpeg_quality: int
    tolerance: float
    confidence_floor: float
    use_json_schema: bool

    @property
    def oci_config_path(self) -> Path:
        return Path(self.oci_config_file or "~/.oci/config").expanduser()

    @property
    def is_dac_ready(self) -> bool:
        values = (self.compartment_id, self.dac_endpoint_id)
        return self.oci_config_path.exists() and all(map(_configured, values))

    @property
    def is_on_demand_ready(self) -> bool:
        has_auth = _configured(self.on_demand_api_key) or self.oci_config_path.exists()
        return _configured(self.on_demand_project_id) and has_auth

    @property
    def is_live_ready(self) -> bool:
        return (
            self.is_on_demand_ready
            if self.inference_mode == "on_demand"
            else self.is_dac_ready
        )

    @property
    def active_model_id(self) -> str:
        return (
            self.on_demand_model_id
            if self.inference_mode == "on_demand"
            else self.dac_model_id
        )

    @property
    def active_model_label(self) -> str:
        return (
            self.on_demand_model_label
            if self.inference_mode == "on_demand"
            else self.dac_model_label
        )

    @property
    def serving_label(self) -> str:
        return "On-demand" if self.inference_mode == "on_demand" else "Imported DAC"

    @property
    def route_region(self) -> str | None:
        """Read an OCI region from the endpoint used by the selected route."""

        endpoint = (
            self.responses_base_url
            if self.inference_mode == "on_demand"
            else self.service_endpoint
        )
        return _endpoint_region(endpoint)

    @property
    def route_location(self) -> str:
        """Return a truthful compact location label for the application header."""

        return self.route_region or "Custom endpoint"

    @property
    def processing_boundary(self) -> str:
        region = self.route_region
        if self.inference_mode == "dac":
            return (
                f"OCI-hosted · {region}"
                if region
                else "Configured endpoint · verify boundary"
            )
        route = "via OCI" if region else "via configured endpoint"
        if self.on_demand_model_id.startswith("google."):
            if region and region.startswith("us-"):
                return "Google Americas · via OCI"
            if region and region.startswith("eu-"):
                return "Google EU · via OCI"
            return f"Google-hosted · {route}"
        if self.on_demand_model_id.startswith("xai."):
            return f"xAI-hosted · {route}"
        return f"External model · {route}"

    @property
    def configuration_hint(self) -> str:
        if self.inference_mode == "on_demand":
            return (
                "Set CHICAGO_PROJECT_OCID plus OPENAI_API_KEY_CHICAGO or a valid "
                "OCI_CONFIG_PROFILE before on-demand extraction."
            )
        return (
            "Set OCI_COMPARTMENT_ID, INVOICE_DAC_ENDPOINT_OCID, and a valid "
            "OCI_CONFIG_PROFILE before dedicated extraction."
        )


def _flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _configured(value: str) -> bool:
    """Return whether a secret or OCID contains a real configured value."""

    value = value.strip()
    return bool(value and not value.startswith("<"))


def _endpoint_region(endpoint: str) -> str | None:
    """Extract the region only from a standard OCI Generative AI hostname."""

    hostname = (urlparse(endpoint).hostname or "").casefold()
    prefix = "inference.generativeai."
    oci_suffixes = (".oci.oraclecloud.com", ".oci.oraclecloud.eu")
    if not hostname.startswith(prefix) or not hostname.endswith(oci_suffixes):
        return None
    return hostname.removeprefix(prefix).split(".", maxsplit=1)[0] or None


def _inference_mode() -> InferenceMode:
    value = os.getenv("INVOICE_INFERENCE_MODE", "dac").strip().lower()
    return "on_demand" if value == "on_demand" else "dac"


def _integer(name: str, default: int, minimum: int, maximum: int) -> int:
    """Read one bounded integer setting with a useful startup error."""

    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def _number(name: str, default: float, minimum: float, maximum: float) -> float:
    """Read one finite bounded numeric setting with a useful startup error."""

    raw = os.getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number.") from exc
    if not isfinite(value) or not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}.")
    return value


def load_settings() -> Settings:
    """Load optional local overrides without requiring secrets at import time."""

    load_dotenv(PROJECT_ROOT / ".env")
    region = os.getenv("OCI_REGION", "us-chicago-1")
    realm_domain = (
        "oci.oraclecloud.eu" if region == "eu-frankfurt-2" else "oci.oraclecloud.com"
    )
    endpoint = os.getenv(
        "OCI_GENAI_ENDPOINT",
        f"https://inference.generativeai.{region}.{realm_domain}",
    )
    responses_base = os.getenv(
        "OCI_OPENAI_BASE_URL",
        f"https://inference.generativeai.{region}.{realm_domain}/openai/v1",
    )
    dac_model_id = os.getenv(
        "INVOICE_DAC_MODEL_ID",
        os.getenv("INVOICE_MODEL_IMPORT_ID", DEFAULT_DAC_MODEL_ID),
    )
    on_demand_model_id = os.getenv(
        "INVOICE_ON_DEMAND_MODEL_ID", DEFAULT_ON_DEMAND_MODEL_ID
    )
    on_demand_option = on_demand_model(on_demand_model_id)
    return Settings(
        region=region,
        service_endpoint=endpoint,
        responses_base_url=responses_base,
        compartment_id=os.getenv("OCI_COMPARTMENT_ID", ""),
        dac_endpoint_id=os.getenv("INVOICE_DAC_ENDPOINT_OCID", ""),
        dac_model_id=dac_model_id,
        dac_model_label=os.getenv(
            "INVOICE_DAC_MODEL_LABEL",
            os.getenv("INVOICE_MODEL_LABEL", DEFAULT_DAC_MODEL_LABEL),
        ),
        on_demand_project_id=os.getenv("CHICAGO_PROJECT_OCID", ""),
        on_demand_api_key=os.getenv("OPENAI_API_KEY_CHICAGO", ""),
        on_demand_model_id=on_demand_model_id,
        on_demand_model_label=on_demand_option.label,
        inference_mode=_inference_mode(),
        oci_profile=os.getenv("OCI_CONFIG_PROFILE", "DEFAULT"),
        oci_config_file=os.getenv("OCI_CONFIG_FILE") or None,
        max_tokens=_integer("INVOICE_MAX_TOKENS", 16_000, 256, 65_536),
        request_timeout_seconds=_integer("OCI_REQUEST_TIMEOUT", 300, 10, 1_800),
        pdf_dpi=_integer("INVOICE_PDF_DPI", 170, 72, 600),
        max_pages=_integer("INVOICE_MAX_PAGES", 12, 1, 100),
        max_image_dimension=_integer("INVOICE_MAX_IMAGE_DIMENSION", 2_400, 512, 8_192),
        jpeg_quality=_integer("INVOICE_JPEG_QUALITY", 88, 40, 100),
        tolerance=_number("INVOICE_MATH_TOLERANCE", 0.02, 0, 1_000),
        confidence_floor=_number("INVOICE_CONFIDENCE_FLOOR", 0.80, 0, 1),
        use_json_schema=_flag("OCI_USE_JSON_SCHEMA", True),
    )
