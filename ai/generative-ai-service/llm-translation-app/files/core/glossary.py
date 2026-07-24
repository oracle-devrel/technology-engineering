import json
import logging
import time
from threading import Lock
from typing import Any

from core.auth import get_oci_config, get_signer

logger = logging.getLogger(__name__)

GLOSSARY_BUCKET_NAME = "bucket-glossary"
GLOSSARY_OBJECT_NAME = "glossary.json"
GLOSSARY_REFRESH_INTERVAL_SECONDS = 5 * 60

Glossary = dict[str, dict[str, str]]

_glossary: Glossary = {}
_last_refresh_at = 0.0
_refresh_lock = Lock()


class GlossaryLoadError(RuntimeError):
    pass


def _get_object_storage_client():
    import oci.object_storage

    signer = get_signer()
    return oci.object_storage.ObjectStorageClient(
        config=get_oci_config(),
        signer=signer,
    )


def _read_object_body(data: Any) -> bytes:
    if hasattr(data, "content"):
        content = data.content
        return content if isinstance(content, bytes) else content.encode("utf-8")

    if hasattr(data, "read"):
        content = data.read()
        return content if isinstance(content, bytes) else content.encode("utf-8")

    if isinstance(data, bytes):
        return data

    if isinstance(data, str):
        return data.encode("utf-8")

    raise TypeError(f"Unsupported OCI object body type: {type(data)!r}")


def _validate_glossary(raw_glossary: Any) -> Glossary:
    if not isinstance(raw_glossary, dict):
        raise ValueError("Glossary JSON must be an object")

    glossary: Glossary = {}
    for term, translations in raw_glossary.items():
        if not isinstance(term, str) or not isinstance(translations, dict):
            raise ValueError("Glossary JSON must map terms to translation objects")

        glossary[term] = {}
        for language, translation in translations.items():
            if not isinstance(language, str) or not isinstance(translation, str):
                raise ValueError("Glossary languages and translations must be strings")
            glossary[term][language] = translation

    return glossary


def _load_glossary_from_bucket() -> Glossary:
    client = _get_object_storage_client()
    namespace = client.get_namespace().data
    response = client.get_object(
        namespace,
        GLOSSARY_BUCKET_NAME,
        GLOSSARY_OBJECT_NAME,
    )
    body = _read_object_body(response.data)
    return _validate_glossary(json.loads(body.decode("utf-8")))


def _is_missing_glossary_error(exc: Exception) -> bool:
    return getattr(exc, "status", None) == 404


def refresh_glossary(force: bool = False) -> None:
    """Refresh the cached glossary from OCI Object Storage when it is stale."""
    global _glossary, _last_refresh_at

    now = time.monotonic()
    if not force and now - _last_refresh_at < GLOSSARY_REFRESH_INTERVAL_SECONDS:
        return

    with _refresh_lock:
        now = time.monotonic()
        if not force and now - _last_refresh_at < GLOSSARY_REFRESH_INTERVAL_SECONDS:
            return

        try:
            _glossary = _load_glossary_from_bucket()
            _last_refresh_at = now
            logger.info(
                "Loaded glossary from OCI Object Storage: bucket=%s object=%s terms=%d",
                GLOSSARY_BUCKET_NAME,
                GLOSSARY_OBJECT_NAME,
                len(_glossary),
            )
        except Exception as exc:
            if _is_missing_glossary_error(exc):
                logger.error(
                    "Glossary object not found yet: bucket=%s object=%s",
                    GLOSSARY_BUCKET_NAME,
                    GLOSSARY_OBJECT_NAME,
                )
            else:
                logger.exception(
                    "Failed to load glossary from OCI Object Storage: bucket=%s object=%s",
                    GLOSSARY_BUCKET_NAME,
                    GLOSSARY_OBJECT_NAME,
                )
            raise GlossaryLoadError(
                f"Failed to load OCI glossary object "
                f"{GLOSSARY_BUCKET_NAME}/{GLOSSARY_OBJECT_NAME}"
            ) from exc


def get_glossary_for_pair(source_language: str, target_language: str) -> dict[str, str]:
    """Return {source_term: target_term} for the given language pair."""
    refresh_glossary()
    return {
        translations[source_language]: translations[target_language]
        for translations in _glossary.values()
        if source_language in translations and target_language in translations
    }
