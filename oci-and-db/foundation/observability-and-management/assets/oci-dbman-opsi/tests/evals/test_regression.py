"""Regression evals — defect signatures from live testing, locked forever.

Each test names the session defect it would have caught. These are the
"regression eval" half of the eval-first loop: a fence so a future change can't
silently reintroduce a bug we already paid to find.
"""

from __future__ import annotations

import pathlib

import pytest

from dbman_opsi.config import EnablementConfig, NetworkSelection, Target
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.prerequisites import PrerequisiteService
from dbman_opsi.runner import CommandRunner
from dbman_opsi.validation import ValidationService
from fakes import ReplayOci

pytestmark = pytest.mark.eval

_REPO = pathlib.Path(__file__).resolve().parents[2]
_CDB = "ocid1.database.oc1..cdb"
_ENABLED_DB = {"lifecycle-state": "AVAILABLE", "database-management-config": {"management-status": "ENABLED"}}


def _cfg(target: Target) -> EnablementConfig:
    return EnablementConfig(
        profile="DEFAULT", region="eu-frankfurt-1", compartment_id="cmp", targets=(target,)
    )


# R1 — the headline defect: flaky OPSI LIST must never produce a false NOT_FOUND.
def test_R1_flaky_list_with_known_ocid_is_always_active() -> None:
    """Defect: `validate` reported NOT_FOUND while the insight was ACTIVE because
    the aggregated LIST flapped empty. With the OCID known, GET-by-OCID wins."""
    target = Target(kind="dbcs", name="cdb", resource_id=_CDB, compartment_id="cmp",
                    opsi_database_insight_id="ins-1")
    flap = [([], True), ([], False), ([{"id": "ins-1", "database-id": _CDB, "lifecycle-state": "ACTIVE"}], True)]
    oci = ReplayOci(databases={_CDB: _ENABLED_DB},
                    insight_get={"ins-1": {"lifecycle-state": "ACTIVE", "status": "SUCCESS"}},
                    insight_list_sequence=flap)

    findings = ValidationService(oci, sleeper=lambda _d: None).validate(_cfg(target))  # type: ignore[arg-type]

    assert "Ops Insights ACTIVE (SUCCESS)" in findings[0]


def test_R1_flaky_list_without_ocid_degrades_to_unknown_not_false_not_found() -> None:
    """Defect: an empty/partial/varying LIST must read UNKNOWN, never NOT_FOUND,
    when we have no OCID to fall back to."""
    target = Target(kind="dbcs", name="cdb", resource_id=_CDB, compartment_id="cmp")
    flap = [([], True), ([{"id": "x", "database-id": "ocid1.database.oc1..other"}], True), ([], False)]
    oci = ReplayOci(databases={_CDB: _ENABLED_DB}, insight_list_sequence=flap)

    findings = ValidationService(oci, sleeper=lambda _d: None).validate(_cfg(target))  # type: ignore[arg-type]

    assert "Ops Insights UNKNOWN" in findings[0]
    assert "NOT_FOUND" not in findings[0]


# R2 — the dry-run trap: a dry-run runner stubs every read to {}.
def test_R2_dry_run_runner_stubs_every_read() -> None:
    """Defect: constructing a read client on CommandRunner(dry_run=True) makes
    every read return empty — indistinguishable from a flaky-empty endpoint.
    This pins that behaviour so read paths are knowingly built dry_run=False."""
    oci = OciCli("p", "r", CommandRunner(dry_run=True))

    assert oci.get_database("x") == {}
    assert oci.list_opsi_database_insights("c") == []
    assert oci.list_opsi_database_insights_complete("c") == ([], True)


def test_R2_validate_cli_path_uses_live_reads_not_dry_run_flag() -> None:
    """Defect: `validate` (read-only) built its runner from args.dry_run, so
    `validate --dry-run` stubbed all reads -> bogus NOT_FOUND/empty. Its reads
    must always be live."""
    src = (_REPO / "src" / "dbman_opsi" / "cli.py").read_text()
    block = src.split('if args.command == "validate":', 1)[1].split("if args.command ==", 1)[0]
    assert "CommandRunner(dry_run=False)" in block
    # The runner must NOT be built from the flag (a comment may still mention it).
    assert "CommandRunner(dry_run=args.dry_run)" not in block


# R3 — flaky-list idempotency on the write side.
def _net_cfg() -> EnablementConfig:
    return EnablementConfig(
        profile="DEFAULT", region="eu-frankfurt-1", compartment_id="cmp",
        network=NetworkSelection(vcn_id="vcn", subnet_id="subnet"),
    )


def test_R3_list_first_miss_tolerates_create_conflict() -> None:
    """Defect: prepare-prereqs list-first guard trusted an empty list; a real
    'already exists' on create then crashed the run. Now it's an idempotent no-op."""
    oci = ReplayOci(create_conflict="The private endpoint name is already in use")

    PrerequisiteService(oci).prepare(_net_cfg())  # type: ignore[arg-type]  # must not raise

    assert oci.commands[0][:3] == ["database-management", "private-endpoint", "create"]
    assert oci.commands[1][:3] == ["opsi", "opsi-private-endpoint", "create"]


def test_R3_non_conflict_create_error_still_propagates() -> None:
    """Guardrail: tolerance must be scoped to name conflicts only."""
    oci = ReplayOci(create_conflict="InvalidParameter: subnet not found")

    with pytest.raises(RuntimeError, match="subnet not found"):
        PrerequisiteService(oci).prepare(_net_cfg())  # type: ignore[arg-type]
