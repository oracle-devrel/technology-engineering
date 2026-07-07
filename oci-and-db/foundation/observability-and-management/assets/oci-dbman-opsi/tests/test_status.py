from dbman_opsi.status import (
    data_safe_status,
    dbm_status,
    is_enabled,
    opsi_insight_status,
)


def test_opsi_insight_status_matches_by_database_id() -> None:
    insights = [{"database-id": "db-1", "lifecycle-state": "ACTIVE"}]
    assert opsi_insight_status(insights, "db-1") == "ENABLED"
    assert opsi_insight_status(insights, "db-2") == "NOT_ENABLED"


def test_opsi_insight_status_creating_counts_as_enabled() -> None:
    insights = [{"database-id": "db-1", "lifecycle-state": "CREATING"}]
    assert opsi_insight_status(insights, "db-1") == "ENABLED"


def test_opsi_insight_status_failed_surfaces_lifecycle() -> None:
    insights = [{"database-id": "db-1", "lifecycle-state": "FAILED"}]
    assert opsi_insight_status(insights, "db-1") == "FAILED"


def test_data_safe_status_matches_by_database_id() -> None:
    targets = [{"lifecycle-state": "ACTIVE", "database-details": {"database-id": "db-1"}}]
    assert data_safe_status(targets, "db-1") == "ENABLED"
    assert data_safe_status(targets, "other") == "NOT_ENABLED"


def test_data_safe_status_matches_by_db_system_for_base_db() -> None:
    targets = [{"lifecycle-state": "ACTIVE", "database-details": {"db-system-id": "sys-1"}}]
    # Base DB target registers against the DB system; match the DB via its system.
    assert data_safe_status(targets, "db-1", db_system_id="sys-1") == "ENABLED"
    assert data_safe_status(targets, "db-1", db_system_id="sys-2") == "NOT_ENABLED"


def test_data_safe_status_matches_autonomous() -> None:
    targets = [{"lifecycle-state": "ACTIVE", "database-details": {"autonomous-database-id": "adb-1"}}]
    assert data_safe_status(targets, "adb-1") == "ENABLED"


def test_data_safe_status_matches_by_associated_resource_ids() -> None:
    # The target-database LIST summary has database-details=null and carries the
    # registered DB OCID under associated-resource-ids instead.
    targets = [{
        "id": "ocid1.datasafetargetdatabase.oc1..t1",
        "lifecycle-state": "ACTIVE",
        "database-details": None,
        "associated-resource-ids": ["adb-1"],
    }]
    assert data_safe_status(targets, "adb-1") == "ENABLED"
    assert data_safe_status(targets, "adb-2") == "NOT_ENABLED"


def test_data_safe_status_does_not_match_on_target_own_id() -> None:
    # A target's own OCID must never be treated as the DB it points at.
    targets = [{"id": "shared-ocid", "lifecycle-state": "ACTIVE", "database-details": None}]
    assert data_safe_status(targets, "shared-ocid") == "NOT_ENABLED"


def test_data_safe_status_empty_is_not_enabled() -> None:
    assert data_safe_status([], "db-1") == "NOT_ENABLED"


def test_data_safe_status_matches_pdb_by_service_name() -> None:
    # A Base DB target registered with a PDB service name: the target's
    # database-details.service-name disambiguates which PDB it covers.
    targets = [{
        "id": "t1", "lifecycle-state": "ACTIVE",
        "associated-resource-ids": ["sys-1"],
        "database-details": {"db-system-id": "sys-1", "service-name": "pdb1.octodemo.cloud"},
    }]
    # PDB whose service matches -> ENABLED.
    assert data_safe_status(targets, "pdb-ocid", db_system_id="sys-1",
                            service_name="pdb1.octodemo.cloud") == "ENABLED"
    # A different PDB in the same DB system but different service -> NOT_ENABLED
    # (must NOT over-match via the shared db-system OCID).
    assert data_safe_status(targets, "pdb-other", db_system_id="sys-1",
                            service_name="pdb2.octodemo.cloud") == "NOT_ENABLED"


def test_data_safe_status_cdb_not_enabled_when_only_pdb_registered() -> None:
    # Only the PDB service is registered; the CDB (different service) must read
    # NOT_ENABLED even though it shares the DB system OCID with the target.
    targets = [{
        "id": "t1", "lifecycle-state": "ACTIVE",
        "associated-resource-ids": ["sys-1"],
        "database-details": {"db-system-id": "sys-1", "service-name": "pdb1.octodemo.cloud"},
    }]
    assert data_safe_status(targets, "cdb-ocid", db_system_id="sys-1",
                            service_name="CDBROOT_x.octodemo.cloud") == "NOT_ENABLED"


def test_data_safe_status_service_name_match_is_case_insensitive() -> None:
    # Oracle service names are case-insensitive: the listener may register
    # 'PDB1.x' while the Data Safe target stored 'pdb1.x'.
    targets = [{
        "id": "t1", "lifecycle-state": "ACTIVE", "associated-resource-ids": ["sys-1"],
        "database-details": {"db-system-id": "sys-1", "service-name": "pdb1.octodemo.cloud"},
    }]
    assert data_safe_status(targets, "pdb-ocid", db_system_id="sys-1",
                            service_name="PDB1.octodemo.cloud") == "ENABLED"


def test_data_safe_status_coarse_db_system_fallback_when_no_service_info() -> None:
    # When the target has no service-name (e.g. summary not enriched), fall back
    # to the coarse DB-system match so a CDB still reads ENABLED.
    targets = [{
        "id": "t1", "lifecycle-state": "ACTIVE",
        "associated-resource-ids": ["sys-1"], "database-details": None,
    }]
    assert data_safe_status(targets, "cdb-ocid", db_system_id="sys-1",
                            service_name="anything") == "ENABLED"


def test_is_enabled_and_dbm_status_round_out_coverage() -> None:
    assert is_enabled("ENABLED") is True
    assert is_enabled(None) is False
    adb = {"database-management-status": "ENABLED"}
    assert dbm_status(adb, "autonomous") == "ENABLED"
