from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.validation import ValidationService


class FakeOci:
    def __init__(self, agents, insights=None, insight_failures=0, insight_sequence=None):
        self.agents = agents
        self.insights = insights or []
        self.insight_failures = insight_failures
        # insight_sequence: explicit per-call return values to model the flaky
        # OPSI list that flaps between full/partial/empty sets across calls.
        self.insight_sequence = insight_sequence
        self.insight_calls = 0

    def list_management_agents(self, compartment_id):
        return self.agents

    def list_opsi_database_insights(self, compartment_id):
        self.insight_calls += 1
        if self.insight_calls <= self.insight_failures:
            raise RuntimeError("NotAuthorizedOrNotFound")
        if self.insight_sequence is not None:
            idx = min(self.insight_calls - 1, len(self.insight_sequence) - 1)
            return self.insight_sequence[idx]
        return self.insights

    def get_autonomous_database(self, autonomous_database_id):
        return {"database-management-status": "ENABLED", "operations-insights-status": "ENABLED"}

    def get_database(self, database_id):
        return {"database-management-config": {"management-status": "ENABLED"}}

    def get_pluggable_database(self, pluggable_database_id):
        return {"pluggable-database-management-config": {"management-status": "ENABLED"}}


class RegionFakeOci(FakeOci):
    def __init__(self, region):
        super().__init__([])
        self.region = region
        self.database_reads = []

    def get_database(self, database_id):
        self.database_reads.append((self.region, database_id))
        return {"database-management-config": {"management-status": "ENABLED"}}


class FakeOciWithGet(FakeOci):
    def __init__(self, *args, insight_details=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.insight_details = insight_details or {}
        self.get_calls = []

    def get_opsi_database_insight(self, insight_id):
        self.get_calls.append(insight_id)
        return self.insight_details.get(insight_id, {})


class FakeOciWithComplete(FakeOci):
    """Exposes the completeness-aware list facade (a skipped lifecycle state)."""

    def __init__(self, *args, complete=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.complete = complete

    def list_opsi_database_insights_complete(self, compartment_id):
        return list(self.insights), self.complete


def test_validation_detects_registered_external_agent() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="external-db", name="salesdb", compartment_id="compartment-id"),),
    )
    service = ValidationService(FakeOci([{"display-name": "salesdb-agent"}]))  # type: ignore[arg-type]

    assert service.validate(config) == ["salesdb: Management Agent registered"]


def test_validation_reports_missing_agent_and_resource_id() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        targets=(
            Target(kind="external-db", name="external"),
            Target(kind="dbcs", name="cloud"),
        ),
    )
    service = ValidationService(FakeOci([]))  # type: ignore[arg-type]

    assert service.validate(config) == ["external: Management Agent not found yet", "cloud: missing resource OCID"]


def test_validation_reports_active_opsi_insight() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(
            Target(kind="autonomous", name="adb", resource_id="adb-id"),
            Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),
        ),
    )
    insights = [{"database-id": "db-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(FakeOci([], insights))  # type: ignore[arg-type]

    assert service.validate(config) == [
        "adb: Database Management ENABLED; Ops Insights ENABLED",
        "dbcs (CDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)",
    ]


def test_validation_surfaces_failed_opsi_insight() -> None:
    # A broken Ops Insights collection must be reported as FAILED, not hidden.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "db-id", "lifecycle-state": "FAILED", "status": "ENABLED"}]
    service = ValidationService(FakeOci([], insights))  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights FAILED (ENABLED)",
    ]


def test_validation_reports_not_found_when_other_insights_present() -> None:
    # A populated list that lacks our database is authoritative: the endpoint is
    # demonstrably healthy, so the insight is genuinely absent (NOT_FOUND).
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="pdb1", resource_id="pdb-id", database_role="PDB", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "some-other-db", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(FakeOci([], insights), sleeper=lambda _delay: None)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "pdb1 (PDB): Database Management ENABLED; Ops Insights NOT_FOUND (no Database Insight)",
    ]


def test_validation_empty_insight_list_degrades_to_unknown_not_false_not_found() -> None:
    # The flaky OPSI control plane returns exit-0 empty even when insights exist.
    # An all-empty result is inconclusive and must NOT masquerade as NOT_FOUND.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="pdb1", resource_id="pdb-id", database_role="PDB", compartment_id="compartment-id"),),
    )
    service = ValidationService(FakeOci([], []), sleeper=lambda _delay: None)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "pdb1 (PDB): Database Management ENABLED; Ops Insights UNKNOWN (insight query failed; verify in OCI Console)",
    ]


def test_validation_uses_reliable_get_when_insight_ocid_known() -> None:
    # When the insight OCID is in config, validate must read state with the
    # reliable single-resource GET and never touch the flapping list.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(
            Target(
                kind="dbcs",
                name="dbcs",
                resource_id="db-id",
                compartment_id="compartment-id",
                opsi_database_insight_id="ins-ocid",
            ),
        ),
    )
    oci = FakeOciWithGet(
        [], insights=[], insight_details={"ins-ocid": {"lifecycle-state": "ACTIVE", "status": "SUCCESS"}}
    )
    service = ValidationService(oci)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights ACTIVE (SUCCESS)",
    ]
    assert oci.get_calls == ["ins-ocid"]
    assert oci.insight_calls == 0  # never hit the flaky list


def test_validation_positive_list_hit_reads_state_via_reliable_get() -> None:
    # Discovered via the list, the OCID is then GET for the authoritative state:
    # the list may report a stale ACTIVE while GET shows the true NEEDS_ATTENTION.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    oci = FakeOciWithGet(
        [],
        insights=[{"id": "ins-1", "database-id": "db-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
        insight_details={"ins-1": {"lifecycle-state": "NEEDS_ATTENTION", "status": "SUCCESS"}},
    )
    service = ValidationService(oci)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights NEEDS_ATTENTION (SUCCESS)",
    ]
    assert oci.get_calls == ["ins-1"]


def test_validation_varying_partial_lists_degrade_to_unknown_not_false_not_found() -> None:
    # The cap OPSI list flaps between different non-empty sets call to call. Our
    # database is absent from each *partial* response only because the endpoint
    # is dropping entries — that must read UNKNOWN, never a false NOT_FOUND.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    sequence = [
        [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
        [],
        [
            {"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"},
            {"database-id": "other-b", "lifecycle-state": "ACTIVE", "status": "ENABLED"},
        ],
    ]
    service = ValidationService(
        FakeOci([], insight_sequence=sequence), sleeper=lambda _delay: None
    )  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights UNKNOWN (insight query failed; verify in OCI Console)",
    ]


def test_validation_empty_attempt_within_window_blocks_not_found() -> None:
    # Codex review: a window of [other], [], [other] must NOT yield NOT_FOUND —
    # the empty read means the endpoint may have dropped our insight that round.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    sequence = [
        [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
        [],
        [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
    ]
    service = ValidationService(
        FakeOci([], insight_sequence=sequence), sleeper=lambda _delay: None
    )  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights UNKNOWN (insight query failed; verify in OCI Console)",
    ]


def test_validation_incomplete_union_never_concludes_not_found() -> None:
    # Codex review: if a lifecycle-state call failed (incomplete union), the
    # insight could live in the skipped state — a stable non-empty list that
    # lacks our database must read UNKNOWN, not NOT_FOUND.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(
        FakeOciWithComplete([], insights=insights, complete=False), sleeper=lambda _delay: None
    )  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights UNKNOWN (insight query failed; verify in OCI Console)",
    ]


def test_validation_complete_stable_list_concludes_not_found() -> None:
    # Counterpart: a complete, stable, non-empty list reproducibly lacking our
    # database is the one case where NOT_FOUND is authoritative.
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(
        FakeOciWithComplete([], insights=insights, complete=True), sleeper=lambda _delay: None
    )  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights NOT_FOUND (no Database Insight)",
    ]


def test_validation_positive_match_on_a_later_flaky_attempt_is_authoritative() -> None:
    # Even if early reads drop our database, a single attempt that surfaces it is
    # trusted (an id cannot appear unless the insight exists).
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    sequence = [
        [],
        [{"database-id": "other-a", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
        [{"database-id": "db-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}],
    ]
    service = ValidationService(
        FakeOci([], insight_sequence=sequence), sleeper=lambda _delay: None
    )  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)",
    ]


def test_validation_retries_then_reads_insight_after_transient_404() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "db-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(FakeOci([], insights, insight_failures=1), sleeper=lambda _delay: None)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)",
    ]


def test_validation_degrades_to_unknown_when_insight_query_keeps_failing() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="dbcs", resource_id="db-id", compartment_id="compartment-id"),),
    )
    service = ValidationService(FakeOci([], insight_failures=5), sleeper=lambda _delay: None)  # type: ignore[arg-type]

    assert service.validate(config) == [
        "dbcs (CDB): Database Management ENABLED; Ops Insights UNKNOWN (insight query failed; verify in OCI Console)",
    ]


def test_validation_reads_pdb_nested_status() -> None:
    config = EnablementConfig(
        profile="DEFAULT",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(Target(kind="dbcs", name="pdb1", resource_id="pdb-id", database_role="PDB", compartment_id="compartment-id"),),
    )
    insights = [{"database-id": "pdb-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(FakeOci([], insights))  # type: ignore[arg-type]

    assert service.validate(config) == [
        "pdb1 (PDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)",
    ]


def test_validation_routes_target_reads_to_target_region() -> None:
    config = EnablementConfig(
        profile="cap",
        region="eu-frankfurt-1",
        compartment_id="compartment-id",
        targets=(
            Target(
                kind="dbcs",
                name="chicago-cdb",
                region="us-chicago-1",
                resource_id="db-id",
                service_name="cdb.example",
                compartment_id="compartment-id",
            ),
        ),
    )
    clients = {
        "eu-frankfurt-1": RegionFakeOci("eu-frankfurt-1"),
        "us-chicago-1": RegionFakeOci("us-chicago-1"),
    }
    clients["us-chicago-1"].insights = [{"database-id": "db-id", "lifecycle-state": "ACTIVE", "status": "ENABLED"}]
    service = ValidationService(
        clients["eu-frankfurt-1"],  # type: ignore[arg-type]
        oci_for_region=lambda region: clients[region],  # type: ignore[arg-type]
    )

    assert service.validate(config) == [
        "chicago-cdb [us-chicago-1] (CDB): Database Management ENABLED; Ops Insights ACTIVE (ENABLED)",
    ]
    assert clients["eu-frankfurt-1"].database_reads == []
    assert clients["us-chicago-1"].database_reads == [("us-chicago-1", "db-id")]
