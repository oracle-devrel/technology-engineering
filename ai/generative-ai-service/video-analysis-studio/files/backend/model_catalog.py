# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

try:
    from langchain_oci import VISION_MODELS
except Exception:
    VISION_MODELS = []

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegionCatalogEntry:
    label: str
    region: str
    endpoint: str
    supported_models: tuple[str, ...]
    source: str = "oracle_docs_static"


@dataclass(frozen=True)
class ModelCatalogEntry:
    label: str
    value: str
    detail: str
    provider: str = "Google"
    capabilities: tuple[str, ...] = ("CHAT", "VIDEO_UNDERSTANDING")
    available_regions: tuple[str, ...] = field(default_factory=tuple)
    pricing: dict[str, float | str | None] = field(default_factory=dict)
    features: dict[str, Any] = field(default_factory=dict)
    source: str = "langchain_oci_vision_models"


KNOWN_VIDEO_MODEL_DETAILS: dict[str, tuple[str, str]] = {
    "google.gemini-2.5-pro": ("Gemini 2.5 Pro", "Highest quality reasoning"),
    "google.gemini-2.5-flash": ("Gemini 2.5 Flash", "Balanced latency and quality"),
    "google.gemini-2.5-flash-lite": (
        "Gemini 2.5 Flash-Lite",
        "Fastest lightweight analysis",
    ),
}

DEFAULT_VIDEO_MODEL_METADATA: dict[str, dict[str, Any]] = {
    "google.gemini-2.5-pro": {
        "pricing": {
            "input_per_million": 1.25,
            "output_per_million": 10.0,
            "long_context_input_per_million": 2.5,
            "long_context_output_per_million": 15.0,
            "long_context_threshold_tokens": 200000,
            "currency": "USD",
            "source": "oracle_price_list_env",
        },
        "features": {
            "input_modalities": ["text", "image", "video", "audio"],
            "output_modalities": ["text"],
            "max_input_tokens": 1048576,
            "max_output_tokens": 65536,
            "supports_tools": True,
            "structured_output": True,
            "context_caching": True,
            "thinking": True,
            "source": "oracle_model_docs_env",
        },
    },
    "google.gemini-2.5-flash": {
        "pricing": {
            "input_per_million": 0.3,
            "audio_input_per_million": 1.0,
            "output_per_million": 2.5,
            "currency": "USD",
            "source": "oracle_price_list_env",
        },
        "features": {
            "input_modalities": ["text", "image", "video", "audio"],
            "output_modalities": ["text"],
            "max_input_tokens": 1048576,
            "max_output_tokens": 65536,
            "supports_tools": True,
            "structured_output": True,
            "context_caching": True,
            "thinking": True,
            "source": "oracle_model_docs_env",
        },
    },
    "google.gemini-2.5-flash-lite": {
        "pricing": {
            "input_per_million": 0.1,
            "audio_input_per_million": 0.5,
            "output_per_million": 0.4,
            "currency": "USD",
            "source": "oracle_price_list_env",
        },
        "features": {
            "input_modalities": ["text", "image", "video", "audio"],
            "output_modalities": ["text"],
            "max_input_tokens": 1048576,
            "max_output_tokens": 65536,
            "supports_tools": True,
            "structured_output": True,
            "context_caching": True,
            "thinking": False,
            "source": "oracle_model_docs_env",
        },
    },
}


def _env_model_prefix(model_id: str) -> str:
    safe_model_id = (
        model_id.upper()
        .replace(".", "_")
        .replace("-", "_")
        .replace("/", "_")
    )
    return f"OCI_VIDEO_MODEL_{safe_model_id}"


def _env_value(model_id: str, suffix: str, default: Any) -> Any:
    value = os.getenv(f"{_env_model_prefix(model_id)}_{suffix}")
    return default if value is None or value == "" else value


def _env_float(model_id: str, suffix: str, default: float | None) -> float | None:
    value = _env_value(model_id, suffix, default)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _env_int(model_id: str, suffix: str, default: int | None) -> int | None:
    value = _env_value(model_id, suffix, default)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _env_bool(model_id: str, suffix: str, default: bool | None) -> bool | None:
    value = _env_value(model_id, suffix, default)
    if isinstance(value, bool) or value is None:
        return value

    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_list(model_id: str, suffix: str, default: list[str]) -> list[str]:
    value = _env_value(model_id, suffix, ",".join(default))
    if isinstance(value, list):
        return value

    return [item.strip() for item in str(value).split(",") if item.strip()]


def _model_metadata(model_id: str) -> dict[str, Any]:
    defaults = DEFAULT_VIDEO_MODEL_METADATA.get(model_id, {})
    pricing_defaults = defaults.get("pricing", {})
    feature_defaults = defaults.get("features", {})

    return {
        "pricing": {
            "input_per_million": _env_float(
                model_id,
                "INPUT_PRICE_PER_MILLION",
                pricing_defaults.get("input_per_million"),
            ),
            "output_per_million": _env_float(
                model_id,
                "OUTPUT_PRICE_PER_MILLION",
                pricing_defaults.get("output_per_million"),
            ),
            "audio_input_per_million": _env_float(
                model_id,
                "AUDIO_INPUT_PRICE_PER_MILLION",
                pricing_defaults.get("audio_input_per_million"),
            ),
            "long_context_input_per_million": _env_float(
                model_id,
                "LONG_CONTEXT_INPUT_PRICE_PER_MILLION",
                pricing_defaults.get("long_context_input_per_million"),
            ),
            "long_context_output_per_million": _env_float(
                model_id,
                "LONG_CONTEXT_OUTPUT_PRICE_PER_MILLION",
                pricing_defaults.get("long_context_output_per_million"),
            ),
            "long_context_threshold_tokens": _env_int(
                model_id,
                "LONG_CONTEXT_THRESHOLD_TOKENS",
                pricing_defaults.get("long_context_threshold_tokens"),
            ),
            "currency": _env_value(
                model_id,
                "PRICE_CURRENCY",
                pricing_defaults.get("currency", "USD"),
            ),
            "source": _env_value(
                model_id,
                "PRICING_SOURCE",
                pricing_defaults.get("source", "env"),
            ),
        },
        "features": {
            "input_modalities": _env_list(
                model_id,
                "INPUT_MODALITIES",
                feature_defaults.get("input_modalities", []),
            ),
            "output_modalities": _env_list(
                model_id,
                "OUTPUT_MODALITIES",
                feature_defaults.get("output_modalities", []),
            ),
            "max_input_tokens": _env_int(
                model_id,
                "MAX_INPUT_TOKENS",
                feature_defaults.get("max_input_tokens"),
            ),
            "max_output_tokens": _env_int(
                model_id,
                "MAX_OUTPUT_TOKENS",
                feature_defaults.get("max_output_tokens"),
            ),
            "supports_tools": _env_bool(
                model_id,
                "SUPPORTS_TOOLS",
                feature_defaults.get("supports_tools"),
            ),
            "structured_output": _env_bool(
                model_id,
                "STRUCTURED_OUTPUT",
                feature_defaults.get("structured_output"),
            ),
            "context_caching": _env_bool(
                model_id,
                "CONTEXT_CACHING",
                feature_defaults.get("context_caching"),
            ),
            "thinking": _env_bool(
                model_id,
                "THINKING",
                feature_defaults.get("thinking"),
            ),
            "source": _env_value(
                model_id,
                "FEATURE_SOURCE",
                feature_defaults.get("source", "env"),
            ),
        },
    }

STATIC_REGION_CATALOG: tuple[RegionCatalogEntry, ...] = (
    RegionCatalogEntry(
        label="US Midwest (Chicago)",
        region="us-chicago-1",
        endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
        supported_models=(
            "google.gemini-2.5-pro",
            "google.gemini-2.5-flash",
            "google.gemini-2.5-flash-lite",
        ),
    ),
    RegionCatalogEntry(
        label="US East (Ashburn, identity domain G)",
        region="us-ashburn-1",
        endpoint="https://inference.generativeai.us-ashburn-1.oci.oraclecloud.com",
        supported_models=(
            "google.gemini-2.5-pro",
            "google.gemini-2.5-flash",
            "google.gemini-2.5-flash-lite",
        ),
    ),
    RegionCatalogEntry(
        label="US West (Phoenix)",
        region="us-phoenix-1",
        endpoint="https://inference.generativeai.us-phoenix-1.oci.oraclecloud.com",
        supported_models=(
            "google.gemini-2.5-pro",
            "google.gemini-2.5-flash",
            "google.gemini-2.5-flash-lite",
        ),
    ),
    RegionCatalogEntry(
        label="Germany Central (Frankfurt, identity domain G)",
        region="eu-frankfurt-1",
        endpoint="https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com",
        supported_models=(
            "google.gemini-2.5-pro",
            "google.gemini-2.5-flash",
            "google.gemini-2.5-flash-lite",
        ),
    ),
    RegionCatalogEntry(
        label="India South (Hyderabad)",
        region="ap-hyderabad-1",
        endpoint="https://inference.generativeai.ap-hyderabad-1.oci.oraclecloud.com",
        supported_models=("google.gemini-2.5-flash",),
    ),
    RegionCatalogEntry(
        label="Japan Central (Osaka)",
        region="ap-osaka-1",
        endpoint="https://inference.generativeai.ap-osaka-1.oci.oraclecloud.com",
        supported_models=("google.gemini-2.5-pro", "google.gemini-2.5-flash"),
    ),
)

DEFAULT_MODEL_ID = "google.gemini-2.5-flash"
DEFAULT_REGION = "eu-frankfurt-1"
DISCOVERED_MODEL_IDS: set[str] = set()


def _label_from_model_id(model_id: str) -> str:
    label = model_id.removeprefix("google.")
    return " ".join(part.capitalize() for part in label.replace("_", "-").split("-"))


def _is_gemini_vision_model(model_id: str) -> bool:
    return model_id.startswith("google.gemini-")


def _static_model_ids() -> list[str]:
    langchain_ids = [model_id for model_id in VISION_MODELS if _is_gemini_vision_model(model_id)]
    known_ids = [model_id for model_id in KNOWN_VIDEO_MODEL_DETAILS if model_id in langchain_ids]
    return known_ids or list(KNOWN_VIDEO_MODEL_DETAILS)


def get_supported_model_ids() -> set[str]:
    return set(_static_model_ids()) | DISCOVERED_MODEL_IDS


def is_supported_public_model_id(model_id: str) -> bool:
    return model_id in get_supported_model_ids()


def _model_region_map(regions: tuple[RegionCatalogEntry, ...]) -> dict[str, list[str]]:
    region_map: dict[str, list[str]] = {}
    for region in regions:
        for model_id in region.supported_models:
            region_map.setdefault(model_id, []).append(region.region)
    return region_map


def _catalog_models_from_regions(
    regions: tuple[RegionCatalogEntry, ...],
    *,
    source: str,
) -> list[ModelCatalogEntry]:
    region_map = _model_region_map(regions)
    model_order = {model_id: index for index, model_id in enumerate(KNOWN_VIDEO_MODEL_DETAILS)}
    model_ids = sorted(
        region_map,
        key=lambda value: (0, model_order[value]) if value in model_order else (1, value),
    )

    models: list[ModelCatalogEntry] = []
    for model_id in model_ids:
        label, detail = KNOWN_VIDEO_MODEL_DETAILS.get(
            model_id,
            (_label_from_model_id(model_id), "Discovered OCI Gemini chat model"),
        )
        metadata = _model_metadata(model_id)
        models.append(
            ModelCatalogEntry(
                label=label,
                value=model_id,
                detail=detail,
                available_regions=tuple(region_map[model_id]),
                pricing=metadata["pricing"],
                features=metadata["features"],
                source=source,
            )
        )

    return models


def _serialize_model(entry: ModelCatalogEntry) -> dict[str, Any]:
    data = asdict(entry)
    data["capabilities"] = list(entry.capabilities)
    data["available_regions"] = list(entry.available_regions)
    return data


def _serialize_region(entry: RegionCatalogEntry) -> dict[str, Any]:
    return {
        "label": entry.label,
        "region": entry.region,
        "endpoint": entry.endpoint,
        "supportedModels": list(entry.supported_models),
        "source": entry.source,
    }


def build_static_model_catalog() -> dict[str, Any]:
    regions = STATIC_REGION_CATALOG
    allowed_ids = set(_static_model_ids())
    filtered_regions = tuple(
        RegionCatalogEntry(
            label=region.label,
            region=region.region,
            endpoint=region.endpoint,
            supported_models=tuple(
                model_id for model_id in region.supported_models if model_id in allowed_ids
            ),
            source=region.source,
        )
        for region in regions
    )
    filtered_regions = tuple(region for region in filtered_regions if region.supported_models)

    return {
        "source": "langchain_oci_vision_models+oracle_docs_static_regions",
        "models": [
            _serialize_model(model)
            for model in _catalog_models_from_regions(
                filtered_regions,
                source="langchain_oci_vision_models",
            )
        ],
        "endpoints": [_serialize_region(region) for region in filtered_regions],
        "default_model_id": DEFAULT_MODEL_ID,
        "default_region": DEFAULT_REGION,
    }


def _management_endpoint(region: str) -> str:
    return f"https://generativeai.{region}.oci.oraclecloud.com"


def _load_oci_config(auth_profile: str, auth_file_location: str) -> dict[str, Any]:
    import oci

    config_path = str(Path(auth_file_location).expanduser())
    return oci.config.from_file(config_path, auth_profile or "DEFAULT")


def _list_google_chat_models_for_region(
    *,
    region: RegionCatalogEntry,
    compartment_id: str,
    auth_profile: str,
    auth_file_location: str,
) -> list[str]:
    import oci

    config = _load_oci_config(auth_profile, auth_file_location)
    config["region"] = region.region
    client = oci.generative_ai.GenerativeAiClient(
        config,
        service_endpoint=_management_endpoint(region.region),
        timeout=(5, 20),
    )

    model_ids: list[str] = []
    page: str | None = None
    while True:
        response = client.list_models(
            compartment_id,
            vendor="google",
            capability=["CHAT"],
            lifecycle_state="ACTIVE",
            limit=100,
            page=page,
        )
        for model in response.data.items or []:
            model_id = (getattr(model, "id", "") or "").strip()
            model_type = (getattr(model, "type", "") or "").strip()
            on_demand_retired = getattr(model, "time_on_demand_retired", None)
            if (
                model_id
                and _is_gemini_vision_model(model_id)
                and model_type in {"", "BASE"}
                and on_demand_retired is None
            ):
                model_ids.append(model_id)

        page = response.headers.get("opc-next-page")
        if not page:
            break

    return sorted(set(model_ids))


def discover_model_catalog(
    *,
    compartment_id: str,
    auth_profile: str,
    auth_file_location: str,
) -> dict[str, Any]:
    clean_compartment_id = compartment_id.strip()
    if not clean_compartment_id:
        raise ValueError("OCI compartment OCID is required to refresh model availability.")

    discovered_regions: list[RegionCatalogEntry] = []
    errors: dict[str, str] = {}

    for region in STATIC_REGION_CATALOG:
        try:
            model_ids = _list_google_chat_models_for_region(
                region=region,
                compartment_id=clean_compartment_id,
                auth_profile=auth_profile.strip() or "DEFAULT",
                auth_file_location=auth_file_location.strip() or "~/.oci/config",
            )
        except Exception as exc:
            errors[region.region] = str(exc)
            logger.warning(
                "OCI model discovery failed for region %s: %s",
                region.region,
                exc,
            )
            continue

        if model_ids:
            discovered_regions.append(
                RegionCatalogEntry(
                    label=region.label,
                    region=region.region,
                    endpoint=region.endpoint,
                    supported_models=tuple(model_ids),
                    source="oci_list_models",
                )
            )

    if not discovered_regions:
        logger.warning(
            "OCI model discovery returned no regions with active Google Gemini chat models. "
            "Using the static model catalog. Errors: %s",
            errors,
        )
        catalog = build_static_model_catalog()
        catalog["source"] = "oracle_docs_static_regions"
        return catalog

    if errors:
        logger.warning(
            "OCI model discovery completed with region errors: %s",
            errors,
        )

    DISCOVERED_MODEL_IDS.update(
        model_id for region in discovered_regions for model_id in region.supported_models
    )
    regions = tuple(discovered_regions)

    return {
        "source": "oci_list_models",
        "models": [
            _serialize_model(model)
            for model in _catalog_models_from_regions(regions, source="oci_list_models")
        ],
        "endpoints": [_serialize_region(region) for region in regions],
        "default_model_id": DEFAULT_MODEL_ID,
        "default_region": DEFAULT_REGION,
    }
