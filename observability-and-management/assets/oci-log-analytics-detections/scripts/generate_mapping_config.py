#!/usr/bin/env python3
"""Generate Sentinel mapping shards and compatibility exports."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.kql.mapping_loader import DEFAULT_COMPAT_PATH, DEFAULT_ROOT_PATH, load_mapping, write_compat_mapping

TABLE_SHARDS = {
    "identity": "tables/identity.yaml",
    "endpoint": "tables/endpoint.yaml",
    "azure_cloud": "tables/cloud_azure.yaml",
    "m365": "tables/cloud_office.yaml",
    "network": "tables/network.yaml",
}

FIELD_SHARDS = {
    "common": "fields/common.yaml",
    "subject": "fields/subject.yaml",
    "process": "fields/process.yaml",
    "office": "fields/office.yaml",
    "network": "fields/network.yaml",
}

ROOT_PAYLOAD = {
    "version": 1,
    "table_shards": [
        "tables/identity.yaml",
        "tables/endpoint.yaml",
        "tables/cloud_azure.yaml",
        "tables/cloud_office.yaml",
        "tables/network.yaml",
    ],
    "field_shards": [
        "fields/common.yaml",
        "fields/subject.yaml",
        "fields/process.yaml",
        "fields/office.yaml",
        "fields/network.yaml",
    ],
}


def _load_source(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"expected mapping object in {path}")
    return payload


def _contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def infer_role(field: str, target: str) -> str:
    """Infer the role metadata for existing mappings."""

    text = f"{field} {target}".lower()
    if _contains_any(text, ("timegenerated", "timestamp", "creationtime", "endtime", "time'")):
        return "time"
    if _contains_any(text, ("hash", "md5", "sha1", "sha256", "hashes")):
        return "hash"
    field_l = field.lower()
    target_l = target.lower()
    if (
        re.search(r"(?:^|[^a-z])ip(?:address|addr)?(?:$|[^a-z])", field_l)
        or _contains_any(
            field_l,
            (
                "sourceip",
                "srcip",
                "destinationip",
                "dstip",
                "remoteip",
                "clientip",
                "dvcip",
                "port",
                "url",
                "uri",
                "host",
                "http",
                "waf",
                "dns",
            ),
        )
        or _contains_any(
            target_l,
            (
                " ip",
                " port",
                "url",
                "uri",
                "host",
                "http",
                "waf",
                "dns",
                "network",
                "user agent",
            ),
        )
    ):
        return "network"
    if field.startswith(("Target", "Dst", "Destination", "Recipient", "Object")):
        return "target"
    if field.startswith(("InitiatingProcess", "ActingProcess", "Parent")):
        return "initiator"
    if _contains_any(text, ("process", "commandline", "image", "filename", "filepath", "folderpath", "exe")):
        return "initiator"
    if field.startswith(("Subject", "SrcUser", "SourceLogin")):
        return "subject"
    if _contains_any(
        text,
        (
            "account",
            "actor",
            "sender",
            "upn",
            "user",
            "source login",
            "principal",
        ),
    ):
        return "subject"
    return "resource"


def infer_field_shard(field: str, target: str, role: str) -> str:
    text = f"{field} {target}".lower()
    if role == "network":
        return "network"
    if _contains_any(text, ("mail", "email", "office", "cloudapp", "clientapp", "sender", "recipient")):
        return "office"
    if role in {"initiator", "hash"} or _contains_any(
        text,
        ("process", "commandline", "image", "filename", "filepath", "folderpath", "eventid", "logon"),
    ):
        return "process"
    if role in {"subject", "target"}:
        return "subject"
    return "common"


def _normalise_field_value(field: str, value: Any, field_roles: dict[str, str]) -> dict[str, Any]:
    if isinstance(value, dict):
        target = value.get("target")
        role = value.get("role")
        spec = {key: val for key, val in value.items() if key not in {"target", "role"}}
    else:
        target = value
        role = field_roles.get(field)
        spec = {}
    if not isinstance(target, str):
        raise ValueError(f"invalid target for {field}")
    role = role if isinstance(role, str) and role else infer_role(field, target)
    return {"target": target, "role": role, **spec}


def write_shards(source_path: Path, root_path: Path = DEFAULT_ROOT_PATH) -> None:
    """Write shard files from a monolithic mapping source."""

    payload = _load_source(source_path)
    root_path.parent.mkdir(parents=True, exist_ok=True)
    (root_path.parent / "tables").mkdir(parents=True, exist_ok=True)
    (root_path.parent / "fields").mkdir(parents=True, exist_ok=True)
    root_path.write_text(yaml.safe_dump(ROOT_PAYLOAD, sort_keys=False), encoding="utf-8")

    table_groups = {key: {} for key in TABLE_SHARDS}
    for table, spec in (payload.get("tables") or {}).items():
        category = spec.get("category") if isinstance(spec, dict) else None
        group = category if category in table_groups else "network"
        table_groups[group][table] = spec

    for group, relative in TABLE_SHARDS.items():
        path = root_path.parent / relative
        path.write_text(
            yaml.safe_dump({"tables": table_groups[group]}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

    field_roles = payload.get("field_roles") or {}
    field_groups = {key: {} for key in FIELD_SHARDS}
    for field, value in (payload.get("fields") or {}).items():
        spec = _normalise_field_value(field, value, field_roles)
        group = infer_field_shard(field, spec["target"], spec["role"])
        field_groups[group][field] = spec

    for group, relative in FIELD_SHARDS.items():
        path = root_path.parent / relative
        path.write_text(
            yaml.safe_dump({"fields": field_groups[group]}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-monolith",
        type=Path,
        default=None,
        help="Generate config/mapping shards from a monolithic mapping file.",
    )
    parser.add_argument(
        "--export-compat",
        action="store_true",
        help="Export config/sentinel_oci_mapping.yaml from the current shards.",
    )
    args = parser.parse_args()

    if args.from_monolith:
        write_shards(args.from_monolith)
    if args.export_compat or args.from_monolith:
        write_compat_mapping(DEFAULT_COMPAT_PATH, load_mapping())
    if not args.from_monolith and not args.export_compat:
        parser.error("choose --from-monolith or --export-compat")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
