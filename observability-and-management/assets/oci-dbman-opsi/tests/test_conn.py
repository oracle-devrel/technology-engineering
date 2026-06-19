from dbman_opsi.conn import service_name_from_record


def test_prefers_pdb_default_then_cdb_default() -> None:
    record = {"connection-strings": {"pdb-default": "host:1521/PDB1.sub.vcn", "cdb-default": "host:1521/CDB.sub.vcn"}}
    assert service_name_from_record(record) == "PDB1.sub.vcn"


def test_falls_back_to_cdb_default_when_no_pdb_default() -> None:
    record = {"connection-strings": {"cdb-default": "host:1521/CDB.sub.vcn"}}
    assert service_name_from_record(record) == "CDB.sub.vcn"


def test_reads_all_connection_strings_cdb_default() -> None:
    record = {"connection-strings": {"all-connection-strings": {"cdbDefault": "host:1521/ORCL.sub.vcn"}}}
    assert service_name_from_record(record) == "ORCL.sub.vcn"


def test_returns_none_when_no_connection_strings() -> None:
    assert service_name_from_record({}) is None
    assert service_name_from_record({"connection-strings": None}) is None


def test_returns_none_when_value_has_no_service_path() -> None:
    # A bare host:port with no '/service' must not be mis-parsed as a service name.
    assert service_name_from_record({"connection-strings": {"pdb-default": "host:1521"}}) is None


def test_ignores_non_dict_connection_strings() -> None:
    # OCI payloads occasionally return a string here; must not crash on .get().
    assert service_name_from_record({"connection-strings": "host:1521/PDB1"}) is None
