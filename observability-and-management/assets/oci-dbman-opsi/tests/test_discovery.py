from dbman_opsi.discovery import DiscoveryService


class FakeOci:
    def list_vcns(self, compartment_id):
        return [{"id": "vcn-1"}]

    def list_service_gateways(self, compartment_id, vcn_id):
        return [{"lifecycle-state": "AVAILABLE"}] if vcn_id == "vcn-1" else []

    def list_subnets(self, compartment_id, vcn_id):
        return [{"id": "subnet-1", "display-name": "private", "prohibit-public-ip-on-vnic": True}]

    def list_vaults(self, compartment_id):
        return [{"id": "vault-1", "display-name": "v", "lifecycle-state": "ACTIVE", "management-endpoint": "https://kms"}]

    def list_keys(self, compartment_id, management_endpoint):
        return [{"id": "key-1", "display-name": "k"}]

    def list_db_systems(self, compartment_id):
        return [{"id": "dbsys-1"}]

    def list_databases(self, compartment_id, db_system_id):
        return [{"id": "cdb-1", "db-name": "DB0424", "lifecycle-state": "AVAILABLE",
                 "database-management-config": None}]

    def list_pluggable_databases(self, compartment_id):
        return [{"id": "pdb-1", "pdb-name": "test", "lifecycle-state": "AVAILABLE",
                 "pluggable-database-management-config": {"management-status": "ENABLED"}}]

    def list_autonomous_databases(self, compartment_id):
        return [{"id": "adb-1", "display-name": "adb", "lifecycle-state": "AVAILABLE",
                 "database-management-status": "NOT_ENABLED"}]

    def list_db_management_private_endpoints(self, compartment_id):
        return [{"name": "dbm-pe"}]

    def list_opsi_private_endpoints(self, compartment_id):
        return [{"display-name": "opsi-pe"}]

    def list_data_safe_private_endpoints(self, compartment_id):
        return [{"display-name": "ds-pe"}]

    def list_opsi_database_insights(self, compartment_id):
        # OPSI insight references the CDB by database-id, ACTIVE.
        return [{"id": "insight-1", "database-id": "cdb-1", "lifecycle-state": "ACTIVE"}]

    def list_data_safe_targets(self, compartment_id):
        # Data Safe target references the parent DB system, ACTIVE.
        return [{"id": "dstarget-1", "lifecycle-state": "ACTIVE",
                 "database-details": {"db-system-id": "dbsys-1"}}]

    def list_management_agents(self, compartment_id):
        return [{"display-name": "agent-1"}]

    def list_bastions(self, compartment_id):
        return [{"name": "bastion-1"}]


def test_discovery_builds_inventory() -> None:
    inventory = DiscoveryService(FakeOci()).discover([{"id": "cmpt-1", "name": "demo-database"}])  # type: ignore[arg-type]

    compartment = inventory.compartments[0]
    assert compartment.subnets[0].has_service_gateway is True
    assert compartment.subnets[0].private is True
    assert compartment.vaults[0].keys == (("key-1", "k"),)
    roles = {db.role for db in compartment.databases}
    assert roles == {"CDB", "PDB"}
    pdb = next(db for db in compartment.databases if db.role == "PDB")
    assert pdb.dbm_status == "ENABLED"
    cdb = next(db for db in compartment.databases if db.role == "CDB")
    assert cdb.dbm_status == "NOT_ENABLED"
    assert compartment.bastions == ("bastion-1",)
    assert compartment.data_safe_private_endpoints == ({"display-name": "ds-pe"},)


def test_discovery_detects_three_pillars_per_db() -> None:
    inventory = DiscoveryService(FakeOci()).discover([{"id": "cmpt-1", "name": "demo-database"}])  # type: ignore[arg-type]

    compartment = inventory.compartments[0]
    cdb = next(db for db in compartment.databases if db.role == "CDB")
    # CDB: OPSI insight matches by database-id, Data Safe matches by db-system-id.
    assert cdb.opsi_status == "ENABLED"
    assert cdb.data_safe_status == "ENABLED"
    assert set(cdb.enabled_services) == {"opsi", "datasafe"}
    assert "dbm" in cdb.missing_services
    pdb = next(db for db in compartment.databases if db.role == "PDB")
    # PDB: DBM enabled, but no OPSI insight / Data Safe target references it.
    assert pdb.enabled_services == ("dbm",)
    assert set(pdb.missing_services) == {"opsi", "datasafe"}
    # to_dict carries the new fields for reporting.
    assert cdb.to_dict()["data_safe_status"] == "ENABLED"


class _PdbGrainOci:
    """Minimal fake exercising service-name disambiguation of a Base DB target."""

    def list_db_systems(self, compartment_id):
        return [{"id": "sys-9"}]

    def list_databases(self, compartment_id, db_system_id):
        return [{"id": "cdb-9", "db-name": "PRODCDB", "lifecycle-state": "AVAILABLE",
                 "connection-strings": {"cdb-default": "h:1521/cdb9.svc"}}]

    def list_pluggable_databases(self, compartment_id):
        return [{"id": "pdb-9", "pdb-name": "APPPDB", "lifecycle-state": "AVAILABLE",
                 "connection-strings": {"pdb-default": "h:1521/apppdb.svc"},
                 "pluggable-database-management-config": {"management-status": "ENABLED"}}]

    def list_data_safe_targets(self, compartment_id):
        # Summary: database-details null; join key in associated-resource-ids.
        return [{"id": "dst-9", "lifecycle-state": "ACTIVE",
                 "associated-resource-ids": ["sys-9"], "database-details": None}]

    def get_data_safe_target(self, target_database_id):
        # GET enriches with database-details incl. the PDB service name.
        return {"id": "dst-9", "lifecycle-state": "ACTIVE",
                "associated-resource-ids": ["sys-9"],
                "database-details": {"db-system-id": "sys-9", "service-name": "apppdb.svc"}}


def test_discovery_attributes_data_safe_to_pdb_by_service() -> None:
    inventory = DiscoveryService(_PdbGrainOci()).discover([{"id": "c", "name": "prod"}])  # type: ignore[arg-type]
    compartment = inventory.compartments[0]
    pdb = next(db for db in compartment.databases if db.role == "PDB")
    cdb = next(db for db in compartment.databases if db.role == "CDB")
    # The target's service-name matches the PDB, not the CDB root.
    assert pdb.data_safe_status == "ENABLED"
    assert cdb.data_safe_status == "NOT_ENABLED"


def test_discovery_to_dict_skips_empty() -> None:
    class Empty(FakeOci):
        def list_vcns(self, compartment_id):
            return []

        def list_vaults(self, compartment_id):
            return []

        def list_db_systems(self, compartment_id):
            return []

        def list_pluggable_databases(self, compartment_id):
            return []

        def list_autonomous_databases(self, compartment_id):
            return []

        def list_db_management_private_endpoints(self, compartment_id):
            return []

        def list_opsi_private_endpoints(self, compartment_id):
            return []

        def list_data_safe_private_endpoints(self, compartment_id):
            return []

        def list_management_agents(self, compartment_id):
            return []

        def list_bastions(self, compartment_id):
            return []

    inventory = DiscoveryService(Empty()).discover([{"id": "c", "name": "empty"}])  # type: ignore[arg-type]
    assert inventory.to_dict() == {"compartments": []}


def test_parallel_map_preserves_order_and_runs_concurrently() -> None:
    # Order must match the input; concurrency is proven deterministically with a
    # Barrier that only releases once all workers arrive together (a serial map
    # would deadlock and raise BrokenBarrierError on timeout).
    import threading

    from dbman_opsi.discovery import _parallel_map

    barrier = threading.Barrier(3, timeout=5)

    def doubled(value: int) -> int:
        barrier.wait()
        return value * 2

    assert _parallel_map(doubled, [1, 2, 3], max_workers=3) == [2, 4, 6]


def test_parallel_map_falls_back_to_serial_for_trivial_inputs() -> None:
    from dbman_opsi.discovery import _parallel_map

    assert _parallel_map(lambda x: x + 1, [10], max_workers=8) == [11]   # single item
    assert _parallel_map(lambda x: x + 1, [10, 20], max_workers=1) == [11, 21]  # max_workers=1
    assert _parallel_map(lambda x: x + 1, [], max_workers=8) == []        # empty


def test_discover_parallel_matches_serial_across_compartments() -> None:
    compartments = [{"id": f"cmpt-{n}", "name": f"c{n}"} for n in range(4)]
    serial = DiscoveryService(FakeOci(), max_workers=1).discover(compartments)        # type: ignore[arg-type]
    parallel = DiscoveryService(FakeOci(), max_workers=8).discover(compartments)      # type: ignore[arg-type]

    # Same results, same order — parallelism must not reorder or drop compartments.
    assert parallel.to_dict() == serial.to_dict()
    assert tuple(c.id for c in parallel.compartments) == ("cmpt-0", "cmpt-1", "cmpt-2", "cmpt-3")


class _OrderedDataSafeOci:
    def list_data_safe_targets(self, compartment_id):
        return [
            {"id": "dst-1", "database-details": None},
            {"id": "dst-2", "database-details": None},
            {"id": "dst-3", "database-details": None},
        ]

    def get_data_safe_target(self, target_database_id):
        return {
            "id": target_database_id,
            "database-details": {"service-name": f"{target_database_id}.svc"},
        }


def test_data_safe_enrichment_parallel_matches_serial_order() -> None:
    serial_service = DiscoveryService(_OrderedDataSafeOci(), max_workers=1)  # type: ignore[arg-type]
    parallel_service = DiscoveryService(_OrderedDataSafeOci(), max_workers=4)  # type: ignore[arg-type]
    serial = serial_service._data_safe_targets_enriched("c")
    parallel = parallel_service._data_safe_targets_enriched("c")

    assert parallel == serial
    assert [target["id"] for target in parallel] == ["dst-1", "dst-2", "dst-3"]
    assert [target["database-details"]["service-name"] for target in parallel] == [
        "dst-1.svc",
        "dst-2.svc",
        "dst-3.svc",
    ]


def test_data_safe_gets_run_concurrently() -> None:
    import threading

    class ConcurrentDataSafeOci(_OrderedDataSafeOci):
        def __init__(self) -> None:
            self.barrier = threading.Barrier(3, timeout=0.5)

        def get_data_safe_target(self, target_database_id):
            self.barrier.wait()
            return super().get_data_safe_target(target_database_id)

    service = DiscoveryService(ConcurrentDataSafeOci(), max_workers=3)  # type: ignore[arg-type]
    targets = service._data_safe_targets_enriched("c")

    assert [target["id"] for target in targets] == ["dst-1", "dst-2", "dst-3"]
    assert all(target.get("database-details") for target in targets)
