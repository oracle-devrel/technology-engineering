"""Capability evals — does the toolkit report correct state from good fixtures?

These pin the *intended* behaviour (the "capability eval" half of the eval-first
loop). If a refactor breaks how state is read or reported, these fail.
"""

from __future__ import annotations

import pytest

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.validation import ValidationService
from fakes import ReplayOci

pytestmark = pytest.mark.eval

_CDB = "ocid1.database.oc1..cdb"
_ENABLED_DB = {"lifecycle-state": "AVAILABLE", "database-management-config": {"management-status": "ENABLED"}}


def _cfg(target: Target) -> EnablementConfig:
    return EnablementConfig(
        profile="DEFAULT", region="eu-frankfurt-1", compartment_id="cmp", targets=(target,)
    )


def test_validate_reports_active_via_reliable_get_when_ocid_known() -> None:
    target = Target(
        kind="dbcs", name="cdb", resource_id=_CDB, compartment_id="cmp",
        opsi_database_insight_id="ins-1",
    )
    oci = ReplayOci(
        databases={_CDB: _ENABLED_DB},
        insight_get={"ins-1": {"lifecycle-state": "ACTIVE", "status": "ENABLED"}},
        # LIST flaps to empty — must be irrelevant because the OCID is known.
        insight_list_sequence=[([], True)],
    )

    findings = ValidationService(oci).validate(_cfg(target))  # type: ignore[arg-type]

    assert findings == ["cdb (CDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)"]
    assert oci.get_insight_calls == ["ins-1"]  # never leaned on the flaky LIST


def test_validate_reports_dbm_enabled_from_resource_get() -> None:
    target = Target(kind="dbcs", name="cdb", resource_id=_CDB, compartment_id="cmp",
                    opsi_database_insight_id="ins-1")
    oci = ReplayOci(databases={_CDB: _ENABLED_DB},
                    insight_get={"ins-1": {"lifecycle-state": "ACTIVE", "status": "SUCCESS"}})

    findings = ValidationService(oci).validate(_cfg(target))  # type: ignore[arg-type]

    assert "Database Management ENABLED" in findings[0]
    assert "Ops Insights ACTIVE (SUCCESS)" in findings[0]


def test_validate_authoritative_not_found_only_from_complete_stable_absence() -> None:
    # No OCID configured; LIST is COMPLETE + non-empty + stable and reproducibly
    # lacks our database -> the one case NOT_FOUND is authoritative.
    target = Target(kind="dbcs", name="cdb", resource_id=_CDB, compartment_id="cmp")
    others = [{"id": "ins-x", "database-id": "ocid1.database.oc1..other", "lifecycle-state": "ACTIVE"}]
    oci = ReplayOci(
        databases={_CDB: _ENABLED_DB},
        insight_list_sequence=[(others, True), (others, True), (others, True)],
    )

    findings = ValidationService(oci, sleeper=lambda _d: None).validate(_cfg(target))  # type: ignore[arg-type]

    assert findings == ["cdb (CDB): Database Management ENABLED; Ops Insights NOT_FOUND (no Database Insight)"]
