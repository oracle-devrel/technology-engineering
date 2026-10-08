"""Domain adapter loader — reads schema/prompts/rules/lessons from JSON config files."""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

ADAPTERS_DIR = str(Path(__file__).parent.parent / "adapters")
DEFAULT_DOMAIN = "generic"

_adapters: dict = {}
_RULE_TYPES = {"keyword_present", "required_field", "standard_reference"}
_SEVERITIES = {"low", "medium", "high", "critical"}
_MISSING_STATUSES = {"warning", "review", "fail"}


def _load_json(path: str) -> dict | list:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def load_adapter(domain: str) -> dict:
    """Load a domain adapter config. Reloads each time for dev, cache in production."""
    if domain in _adapters and os.getenv("CACHE_ADAPTERS") == "1":
        return _adapters[domain]

    adapter_dir = os.path.join(ADAPTERS_DIR, domain)
    if not os.path.isdir(adapter_dir):
        raise ValueError(f"Domain adapter '{domain}' not found in {ADAPTERS_DIR}/")

    adapter = {
        "domain": domain,
        "schema": _load_json(os.path.join(adapter_dir, "schema.json")),
        "prompts": _load_json(os.path.join(adapter_dir, "prompts.json")),
        "rules": _load_json(os.path.join(adapter_dir, "rules.json")),
        "lessons": _load_json(os.path.join(adapter_dir, "lessons.json")),
    }
    _adapters[domain] = adapter
    return adapter


def invalidate_cache(domain: str | None = None):
    """Clear cached adapter data. If domain is None, clear all."""
    if domain:
        _adapters.pop(domain, None)
    else:
        _adapters.clear()


def get_extraction_prompt(domain: str) -> str:
    adapter = load_adapter(domain)
    return adapter["prompts"].get("extraction", "Extract all key information from this document.")


def get_chat_prompt(domain: str) -> str:
    adapter = load_adapter(domain)
    return adapter["prompts"].get("chat", "You are a helpful document analysis assistant.")


def get_compliance_rules(domain: str) -> list[dict]:
    adapter = load_adapter(domain)
    return adapter.get("rules", {}).get("checks", [])


def get_extraction_schema(domain: str) -> list[dict]:
    adapter = load_adapter(domain)
    return adapter.get("schema", {}).get("fields", [])


def get_lessons(domain: str) -> list[dict]:
    adapter = load_adapter(domain)
    return adapter.get("lessons", {}).get("items", [])


def list_domains() -> list[str]:
    """List all available domain adapters."""
    if not os.path.isdir(ADAPTERS_DIR):
        return [DEFAULT_DOMAIN]
    return sorted([
        d for d in os.listdir(ADAPTERS_DIR)
        if os.path.isdir(os.path.join(ADAPTERS_DIR, d)) and not d.startswith(".")
    ])


def save_adapter_file(domain: str, file_type: str, data: dict | list) -> None:
    """Save updated adapter configuration to disk.

    Args:
        domain: The adapter domain name.
        file_type: One of 'rules', 'prompts', 'lessons', 'schema'.
        data: The full JSON data to write.
    """
    adapter_dir = os.path.join(ADAPTERS_DIR, domain)
    if not os.path.isdir(adapter_dir):
        raise ValueError(f"Domain adapter '{domain}' not found")

    valid_types = {"rules", "prompts", "lessons", "schema"}
    if file_type not in valid_types:
        raise ValueError(f"Invalid file_type '{file_type}', must be one of {valid_types}")

    if file_type == "rules":
        if not isinstance(data, dict) or not isinstance(data.get("checks"), list):
            raise ValueError("Rules configuration must contain a 'checks' array")
        for rule in data["checks"]:
            if not isinstance(rule, dict):
                raise ValueError("Each compliance rule must be an object")
            if not isinstance(rule.get("id"), str) or not rule["id"].strip():
                raise ValueError("Each compliance rule needs a non-empty id")
            if rule.get("type") not in _RULE_TYPES:
                raise ValueError(f"Rule {rule['id']} has an unsupported type")
            if rule.get("severity") not in _SEVERITIES:
                raise ValueError(f"Rule {rule['id']} has an unsupported severity")
            primary_key = {
                "keyword_present": "keyword",
                "required_field": "field_name",
                "standard_reference": "standard",
            }[rule["type"]]
            if not isinstance(rule.get(primary_key), str) or not rule[primary_key].strip():
                raise ValueError(f"Rule {rule['id']} needs a non-empty {primary_key}")
            if "aliases" in rule and (
                not isinstance(rule["aliases"], list)
                or not all(isinstance(alias, str) and alias.strip() for alias in rule["aliases"])
            ):
                raise ValueError(f"Rule {rule['id']} aliases must be non-empty strings")
            if rule.get("missing_status", "warning") not in _MISSING_STATUSES:
                raise ValueError(f"Rule {rule['id']} has an unsupported missing_status")

    file_path = os.path.join(adapter_dir, f"{file_type}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)

    # Invalidate cache so next load picks up changes
    invalidate_cache(domain)
    logger.info(f"Saved adapter config: {domain}/{file_type}.json")
