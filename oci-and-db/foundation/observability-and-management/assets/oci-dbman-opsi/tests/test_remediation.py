from dbman_opsi.remediation import format_remediation, remediation_for


def test_remediation_matches_known_signatures() -> None:
    assert remediation_for("ORA-12514: TNS:listener does not currently know").signature == "ORA-12514"
    assert remediation_for("ORA-01017: invalid username/password").signature == "ORA-01017"
    assert remediation_for("Error: DbcsEntityChangeWorkflowFailed").signature == "DbcsEntityChangeWorkflowFailed"


def test_remediation_orders_account_lock_before_generic() -> None:
    # ORA-28000 must win over a co-occurring generic signature.
    text = "ORA-28000 - The account is locked. NotAuthorizedOrNotFound"
    assert remediation_for(text).signature == "ORA-28000"


def test_remediation_returns_none_for_unknown() -> None:
    assert remediation_for("totally unrelated error text") is None


def test_format_remediation_includes_solution_and_manual_step() -> None:
    out = format_remediation(remediation_for("ORA-28000 account locked"))
    assert "Solution:" in out
    assert "Manual step:" in out
    assert "C##DBSNMP_MON" in out
