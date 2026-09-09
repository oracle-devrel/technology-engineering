from __future__ import annotations

import base64
import io
import json
import logging
import os
import time
from typing import Any

import fdk.response

try:
    import oci
except ImportError:  # pragma: no cover - oci SDK may not be installed in local tests
    oci = None  # type: ignore[assignment]

from webhook import WebhookDeliveryError, forward_to_webhook

LOG_LEVEL = (os.environ.get("LOG_LEVEL") or "INFO").strip().upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(levelname)s:%(name)s:%(message)s",
)

logger = logging.getLogger(__name__)

DEFAULT_TOKEN_CACHE_TTL_SECONDS = 300

_TOKEN_CACHE: str | None = None
_TOKEN_CACHE_EXPIRES_AT = 0.0


def _env_bool(name: str, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def _env_float(name: str, default: float) -> float:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc


def _get_vault_secret(secret_ocid: str) -> str:
    if oci is None:
        raise RuntimeError("OCI SDK is not installed; cannot resolve VAULT_SECRET_OCID")

    signer = oci.auth.signers.get_resource_principals_signer()
    client = oci.secrets.SecretsClient(config={}, signer=signer)
    bundle = client.get_secret_bundle(secret_ocid)
    encoded_secret = bundle.data.secret_bundle_content.content

    if not encoded_secret:
        raise RuntimeError("Vault secret has empty content")

    return base64.b64decode(encoded_secret).decode("utf-8").strip()


def _resolve_bearer_token() -> str:
    global _TOKEN_CACHE, _TOKEN_CACHE_EXPIRES_AT

    now = time.time()
    if _TOKEN_CACHE and now < _TOKEN_CACHE_EXPIRES_AT:
        return _TOKEN_CACHE

    vault_ocid = os.environ.get("VAULT_SECRET_OCID")
    if vault_ocid:
        token = _get_vault_secret(vault_ocid)
    else:
        token = (os.environ.get("BEARER_TOKEN") or "").strip()

    if not token:
        raise RuntimeError("Bearer token is required. Set VAULT_SECRET_OCID or BEARER_TOKEN.")

    ttl_seconds = _env_int("TOKEN_CACHE_TTL_SECONDS", DEFAULT_TOKEN_CACHE_TTL_SECONDS)
    _TOKEN_CACHE = token
    _TOKEN_CACHE_EXPIRES_AT = now + max(0, ttl_seconds)
    return token


def _resolve_webhook_url() -> str:
    webhook_url = (os.environ.get("WEBHOOK_URL") or "").strip()
    if not webhook_url:
        raise RuntimeError("WEBHOOK_URL is required. Configure the Exabeam collector-generated /logs/json endpoint.")
    return webhook_url


def _read_payload(data: io.IOBase | None) -> Any:
    if data is None:
        return []

    body = data.read()
    if not body:
        return []

    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON payload from Service Connector Hub: {exc}") from exc


def _event_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    return 1


def _response(ctx) -> fdk.response.Response:
    return fdk.response.Response(ctx, response_data="")


def handler(ctx, data: io.IOBase | None = None):
    webhook_url = _resolve_webhook_url()

    payload = _read_payload(data)
    event_count = _event_count(payload)

    if event_count == 0:
        logger.info("Empty event batch received; nothing to forward")
        return _response(ctx)

    logger.info("Forwarding %s audit event(s) to Exabeam webhook", event_count)

    try:
        forward_to_webhook(
            webhook_url,
            payload,
            _resolve_bearer_token(),
            gzip_enabled=_env_bool("WEBHOOK_GZIP", False),
            max_attempts=_env_int("WEBHOOK_MAX_ATTEMPTS", 2),
            connect_timeout_seconds=_env_float("WEBHOOK_CONNECT_TIMEOUT_SECONDS", 3.05),
            read_timeout_seconds=_env_float("WEBHOOK_READ_TIMEOUT_SECONDS", 20.0),
            retry_delay_seconds=_env_float("WEBHOOK_RETRY_DELAY_SECONDS", 2.0),
        )
    except WebhookDeliveryError:
        logger.exception("Failed to forward audit event batch to Exabeam")
        raise

    return _response(ctx)
