#!/usr/bin/env python3
"""Tests for sharded Sentinel mapping config loading and linting."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from scripts.kql.mapping_loader import (  # noqa: E402
    ALLOWED_FIELD_ROLES,
    MappingConfigError,
    build_collision_report,
    load_compat_mapping,
    load_mapping,
    load_sharded_mapping,
)


def test_sharded_mapping_matches_compat_projection() -> None:
    sharded = load_mapping()
    compat = load_compat_mapping()

    assert sharded["tables"] == compat["tables"]
    assert sharded["fields"] == compat["fields"]
    assert sharded["field_roles"] == compat["field_roles"]
    assert len(sharded["tables"]) >= 367
    assert sharded["tables"]["BHEAttackPathsData_CL"]["sources"][0] == "Azure Log Analytics Custom Logs"
    assert len(sharded["fields"]) == 185


def test_all_field_mappings_have_allowed_roles() -> None:
    mapping = load_mapping()

    assert set(mapping["field_roles"]) == set(mapping["fields"])
    assert set(mapping["field_roles"].values()) <= ALLOWED_FIELD_ROLES
    assert mapping["field_roles"]["SubjectUserName"] == "subject"
    assert mapping["field_roles"]["TargetUserName"] == "target"


def test_map05_field_cluster_is_present_or_parser_pending() -> None:
    mapping = load_mapping()
    expected = {
        "SubjectAccount",
        "SubjectDomainName",
        "SubjectLogonId",
        "SubjectUserSid",
        "SubjectUserName",
        "InitiatingProcessAccountDomain",
        "InitiatingProcessAccountName",
        "InitiatingProcessSHA256",
        "InitiatingProcessId",
        "MailboxOwnerUPN",
        "OfficeWorkload",
        "OrganizationName",
        "ClientInfoString",
        "UserType",
        "ParentProcessName",
        "ProcessId",
        "Exe",
        "LocalFile",
        "ActingProcessFileInternalName",
        "Logon_Type",
        "ObjectDN",
        "ObjectName",
        "AttributeLDAPDisplayName",
        "EventData",
    }

    assert expected <= set(mapping["fields"])
    for field in ("ObjectDN", "ObjectName", "AttributeLDAPDisplayName", "EventData"):
        assert mapping["field_specs"][field]["parser_change_required"] is True


def test_duplicate_yaml_key_fails_with_structured_reason(tmp_path: Path) -> None:
    root = tmp_path / "_root.yaml"
    fields = tmp_path / "fields"
    fields.mkdir()
    root.write_text(
        "version: 1\n"
        "table_shards: []\n"
        "field_shards:\n"
        "- fields/common.yaml\n",
        encoding="utf-8",
    )
    (fields / "common.yaml").write_text(
        "fields:\n"
        "  Account:\n"
        "    target: User\n"
        "    role: subject\n"
        "  Account:\n"
        "    target: User\n"
        "    role: subject\n",
        encoding="utf-8",
    )

    with pytest.raises(MappingConfigError, match=r"duplicate_key:.*Account"):
        load_sharded_mapping(root)


def test_collision_report_contains_known_many_to_one_reasons() -> None:
    report = build_collision_report(load_mapping())
    reasons = {
        reason
        for collision in report["collisions"]
        for reason in collision["reasons"]
    }

    assert "lossy_mapping_collision:Computer+DeviceId→Entity" in reasons
    assert "lossy_mapping_collision:AccountUpn+ActorUsername→User Name" in reasons
    assert report["summary"]["collision_count"] > 0
