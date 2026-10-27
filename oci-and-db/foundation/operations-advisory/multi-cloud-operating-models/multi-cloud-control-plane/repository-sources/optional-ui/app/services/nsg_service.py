"""Catalog-shaped OCI Network Security Group rendering and additive updates."""
from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Iterable, Mapping

from app.helpers import fill_template_with_missing


class NsgRequestError(ValueError):
    """Raised when an NSG request cannot be rendered or merged safely."""


_NEW_NSG_FIELDS = {
    "category": "__PROJECT_NSG_CATEGORY__",
    "vcn_key": "__PROJECT_VCN_KEY__",
    "vcn_ocid": "__PROJECT_VCN_OCID__",
    "key": "__NSG_KEY__",
    "compartment_ocid": "__NSG_COMPARTMENT_OCID__",
    "display_name": "__NSG_DISPLAY_NAME__",
    "project_name": "__PROJECT_NAME__",
    "tier": "__NSG_TIER__",
}
_RULE_FIELDS = {
    "ingress": {
        "key": "__INGRESS_RULE_KEY__",
        "description": "__INGRESS_RULE_DESCRIPTION__",
        "source": "__INGRESS_RULE_SOURCE__",
        "source_type": "__INGRESS_RULE_SOURCE_TYPE__",
        "port_min": "__INGRESS_RULE_DST_PORT_MIN__",
        "port_max": "__INGRESS_RULE_DST_PORT_MAX__",
    },
    "egress": {
        "key": "__EGRESS_RULE_KEY__",
        "description": "__EGRESS_RULE_DESCRIPTION__",
        "destination": "__EGRESS_RULE_DESTINATION__",
        "destination_type": "__EGRESS_RULE_DESTINATION_TYPE__",
        "port_min": "__EGRESS_RULE_DST_PORT_MIN__",
        "port_max": "__EGRESS_RULE_DST_PORT_MAX__",
    },
}
_ROW_FIELD_PATTERN = re.compile(
    r"^nsg_(ingress|egress)_(\d+)_(key|description|source|source_type|destination|destination_type|port_min|port_max)$"
)


def _single_entry(mapping: Any, label: str) -> tuple[str, dict[str, Any]]:
    if not isinstance(mapping, dict) or len(mapping) != 1:
        raise NsgRequestError(f"Catalog must contain exactly one {label} pattern")
    key, value = next(iter(mapping.items()))
    if not isinstance(key, str) or not isinstance(value, dict):
        raise NsgRequestError(f"Catalog {label} pattern is invalid")
    return key, value


def _nsg_template_node(template: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    network = template.get("network_configuration")
    if not isinstance(network, dict):
        raise NsgRequestError("Catalog is not an OCI project NSG template")
    _, category = _single_entry(network.get("network_configuration_categories"), "NSG category")
    _, vcn = _single_entry(category.get("inject_into_existing_vcns"), "VCN")
    _, nsg = _single_entry(vcn.get("network_security_groups"), "NSG")
    return category, vcn, nsg


def _required_text(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise NsgRequestError(f"NSG {field} is required")
    return text


def _integer_port(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise NsgRequestError(f"NSG {field} must be an integer port")
    text = str(value).strip()
    if not text.isdecimal():
        raise NsgRequestError(f"NSG {field} must be an integer port")
    port = int(text)
    if not 0 <= port <= 65535:
        raise NsgRequestError(f"NSG {field} must be between 0 and 65535")
    return port


def _rule_context(direction: str, rule: Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    fields = _RULE_FIELDS[direction]
    required = set(fields)
    missing = sorted(required - set(rule))
    if missing:
        raise NsgRequestError(f"NSG {direction} rule is missing: {', '.join(missing)}")

    context = {
        fields["key"]: _required_text(rule["key"], f"{direction} rule key"),
        fields["description"]: _required_text(rule["description"], f"{direction} rule description"),
        fields["port_min"]: _integer_port(rule["port_min"], f"{direction} rule port minimum"),
        fields["port_max"]: _integer_port(rule["port_max"], f"{direction} rule port maximum"),
    }
    if context[fields["port_min"]] > context[fields["port_max"]]:
        raise NsgRequestError(f"NSG {direction} rule port minimum exceeds port maximum")

    address_name = "source" if direction == "ingress" else "destination"
    address_type_name = f"{address_name}_type"
    context[fields[address_name]] = _required_text(rule[address_name], f"{direction} rule {address_name}")
    context[fields[address_type_name]] = _required_text(
        rule[address_type_name], f"{direction} rule {address_type_name}"
    )
    return context[fields["key"]], context


def _render_rules(direction: str, pattern: Any, rules: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    _, rule_pattern = _single_entry(pattern, f"{direction} rule")
    rendered_rules: dict[str, Any] = {}
    for rule in rules:
        key, context = _rule_context(direction, rule)
        if key in rendered_rules:
            raise NsgRequestError(f"Duplicate {direction} NSG rule: {key}")
        rendered, missing = fill_template_with_missing(deepcopy(rule_pattern), context)
        if missing:
            raise NsgRequestError(f"Catalog {direction} rule has unresolved placeholders")
        rendered_rules[key] = rendered
    return rendered_rules


def render_new_nsg(
    template: dict[str, Any],
    values: Mapping[str, Any],
    ingress_rules: Iterable[Mapping[str, Any]],
    egress_rules: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Render one new NSG and its explicitly requested optional child rules."""
    rendered_template = deepcopy(template)
    _, _, nsg = _nsg_template_node(rendered_template)
    ingress_pattern = deepcopy(nsg.get("ingress_rules"))
    egress_pattern = deepcopy(nsg.get("egress_rules"))
    nsg["ingress_rules"] = {}
    nsg["egress_rules"] = {}

    missing_fields = sorted(set(_NEW_NSG_FIELDS) - set(values))
    if missing_fields:
        raise NsgRequestError(f"NSG creation is missing: {', '.join(missing_fields)}")
    context = {
        placeholder: _required_text(values[field], field)
        for field, placeholder in _NEW_NSG_FIELDS.items()
    }
    rendered, missing = fill_template_with_missing(rendered_template, context)
    if missing:
        raise NsgRequestError("Catalog NSG creation has unresolved placeholders")
    if not isinstance(rendered, dict):
        raise NsgRequestError("Catalog NSG creation did not render to an object")

    _, _, rendered_nsg = _nsg_template_node(rendered)
    rendered_nsg["ingress_rules"] = _render_rules("ingress", ingress_pattern, ingress_rules)
    rendered_nsg["egress_rules"] = _render_rules("egress", egress_pattern, egress_rules)
    return rendered


def _find_nsg_entries(node: Any, nsg_key: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    if isinstance(node, dict):
        nsgs = node.get("network_security_groups")
        if isinstance(nsgs, dict) and isinstance(nsgs.get(nsg_key), dict):
            matches.append(nsgs[nsg_key])
        for value in node.values():
            matches.extend(_find_nsg_entries(value, nsg_key))
    elif isinstance(node, list):
        for value in node:
            matches.extend(_find_nsg_entries(value, nsg_key))
    return matches


def add_rules_to_existing_nsg(
    template: dict[str, Any],
    manifest: dict[str, Any],
    nsg_key: str,
    ingress_rules: Iterable[Mapping[str, Any]],
    egress_rules: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Add catalog-rendered rules to exactly one existing NSG without replacement."""
    updated = deepcopy(manifest)
    _, _, template_nsg = _nsg_template_node(template)
    matches = _find_nsg_entries(updated, nsg_key)
    if not matches:
        raise NsgRequestError(f"NSG was not found: {nsg_key}")
    if len(matches) != 1:
        raise NsgRequestError(f"NSG appears in multiple project network maps: {nsg_key}")

    nsg = matches[0]
    for direction, rules, pattern in (
        ("ingress", ingress_rules, template_nsg.get("ingress_rules")),
        ("egress", egress_rules, template_nsg.get("egress_rules")),
    ):
        collection_name = f"{direction}_rules"
        existing_rules = nsg.setdefault(collection_name, {})
        if not isinstance(existing_rules, dict):
            raise NsgRequestError(f"Existing NSG {collection_name} is invalid")
        for key, rule in _render_rules(direction, pattern, rules).items():
            if key in existing_rules:
                raise NsgRequestError(f"NSG rule already exists: {key}")
            existing_rules[key] = rule
    return updated


def parse_rule_rows(payload: Mapping[str, Any], direction: str) -> list[dict[str, Any]]:
    """Parse indexed optional NSG rule rows submitted by the specialized form."""
    rows: dict[int, dict[str, Any]] = {}
    for field, value in payload.items():
        match = _ROW_FIELD_PATTERN.fullmatch(field)
        if not match or match.group(1) != direction:
            continue
        index = int(match.group(2))
        rows.setdefault(index, {})[match.group(3)] = value
    return [rows[index] for index in sorted(rows)]
