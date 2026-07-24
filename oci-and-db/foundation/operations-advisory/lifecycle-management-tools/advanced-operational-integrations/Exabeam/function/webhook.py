import gzip
import json
import logging
import random
import re
import time
from typing import Any
from urllib.parse import urlsplit

import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

DEFAULT_CONNECT_TIMEOUT_SECONDS = 3.05
DEFAULT_READ_TIMEOUT_SECONDS = 20.0
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_RETRY_DELAY_SECONDS = 2.0

RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
BEARER_PREFIX = "bearer "


class WebhookDeliveryError(RuntimeError):
    """Raised when the webhook cannot accept the payload."""


def _prepare_json_body(payload: Any, gzip_enabled: bool) -> tuple[bytes, dict[str, str]]:
    body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    headers = {
        "Accept": "application/json",
        "User-Agent": "oci-audit-exabeam-forwarder/1.0",
    }

    if gzip_enabled:
        body = gzip.compress(body)
        headers["Content-Encoding"] = "gzip"
        headers["Content-Type"] = "application/gzip"
    else:
        headers["Content-Type"] = "application/json"

    return body, headers


def _should_retry(status_code: int) -> bool:
    return status_code in RETRYABLE_STATUS_CODES


def _safe_endpoint(url: str) -> str:
    parsed = urlsplit(url)
    return f"{parsed.netloc}{parsed.path}"


def _payload_event_count(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    return 1


def _normalize_bearer_token(bearer_token: str) -> str:
    token = bearer_token.strip()

    if token.lower().startswith(BEARER_PREFIX):
        token = token[len(BEARER_PREFIX) :].strip()

    parts = token.split(".")
    if len(parts) != 3 or not all(parts) or re.search(r"\s", token):
        raise WebhookDeliveryError(
            "Bearer token must be a single-line JWT in header.payload.signature format. "
            "Configure only the token value, without quotes, spaces, newlines, or an extra Bearer prefix."
        )

    return token


def forward_to_webhook(
    url: str,
    payload: Any,
    bearer_token: str,
    *,
    gzip_enabled: bool = False,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    connect_timeout_seconds: float = DEFAULT_CONNECT_TIMEOUT_SECONDS,
    read_timeout_seconds: float = DEFAULT_READ_TIMEOUT_SECONDS,
    retry_delay_seconds: float = DEFAULT_RETRY_DELAY_SECONDS,
) -> None:
    """Forward OCI Audit log payloads to an Exabeam JSON Webhook Collector."""
    if not bearer_token or not bearer_token.strip():
        raise WebhookDeliveryError("Bearer token is required for Exabeam webhook delivery")

    token = _normalize_bearer_token(bearer_token)

    if "/logs/json" not in url:
        raise WebhookDeliveryError("This function supports JSON collectors only. Configure WEBHOOK_URL with /logs/json.")

    body, headers = _prepare_json_body(payload, gzip_enabled=gzip_enabled)
    headers["Authorization"] = f"Bearer {token}"

    attempts = max(1, max_attempts)
    last_error = "unknown error"
    endpoint = _safe_endpoint(url)
    payload_type = type(payload).__name__
    event_count = _payload_event_count(payload)
    content_type = headers["Content-Type"]

    for attempt in range(1, attempts + 1):
        logger.info(
            "Webhook delivery attempt %s/%s: endpoint=%s payload_type=%s event_count=%s bytes=%s gzip=%s "
            "format=%s content_type=%s",
            attempt,
            attempts,
            endpoint,
            payload_type,
            event_count,
            len(body),
            gzip_enabled,
            "json",
            content_type,
        )

        try:
            response = requests.post(
                url,
                data=body,
                headers=headers,
                timeout=(connect_timeout_seconds, read_timeout_seconds),
            )

            if 200 <= response.status_code < 300:
                logger.info(
                    "Webhook delivery succeeded: status=%s bytes=%s gzip=%s",
                    response.status_code,
                    len(body),
                    gzip_enabled,
                )
                return

            last_error = f"HTTP {response.status_code}; response body suppressed"
            logger.error("Webhook delivery failed on attempt %s/%s: %s", attempt, attempts, last_error)

            if not _should_retry(response.status_code):
                break

        except (requests.Timeout, requests.ConnectionError) as exc:
            last_error = repr(exc)
            logger.warning(
                "Webhook transient exception on attempt %s/%s: %s",
                attempt,
                attempts,
                last_error,
                exc_info=True,
            )
        except requests.RequestException as exc:
            last_error = repr(exc)
            logger.exception("Webhook non-retryable request exception on attempt %s/%s", attempt, attempts)
            break

        if attempt < attempts:
            jitter_seconds = random.uniform(0, 0.5)
            time.sleep(retry_delay_seconds + jitter_seconds)

    logger.error("Webhook delivery exhausted after %s attempt(s): %s", attempt, last_error)
    raise WebhookDeliveryError(f"Webhook delivery failed after {attempt} attempt(s): {last_error}")
