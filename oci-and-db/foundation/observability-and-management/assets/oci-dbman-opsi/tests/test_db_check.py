import pytest

from dbman_opsi.db_check import parse_validation_output

PASSING_SPOOL = """
USERNAME                       ACCOUNT_STATUS
------------------------------ ------------------------------
DBSNMP                         OPEN

PRIVILEGE
----------------------------------------
CREATE SESSION
SELECT ANY DICTIONARY

GRANTED_ROLE
----------------------------------------
SELECT_CATALOG_ROLE
"""

MISSING_DICT_SPOOL = """
USERNAME      ACCOUNT_STATUS
DBSNMP        OPEN

PRIVILEGE
----------
CREATE SESSION
"""

LOCKED_SPOOL = """
USERNAME      ACCOUNT_STATUS
DBSNMP        LOCKED

PRIVILEGE
CREATE SESSION
SELECT ANY DICTIONARY
"""


def test_passing_spool_is_ok() -> None:
    result = parse_validation_output(PASSING_SPOOL)

    assert result.ok
    assert result.account_open
    assert "CREATE SESSION" in result.found


def test_missing_dictionary_grant_fails() -> None:
    result = parse_validation_output(MISSING_DICT_SPOOL)

    assert not result.ok
    assert any("SELECT ANY DICTIONARY" in item for item in result.missing)


def test_locked_account_fails_even_with_grants() -> None:
    result = parse_validation_output(LOCKED_SPOOL)

    assert not result.account_open
    assert not result.ok


def test_expiry_date_header_is_not_mistaken_for_expired() -> None:
    spool = "USERNAME ACCOUNT_STATUS LOCK_DATE EXPIRY_DATE\nDBSNMP OPEN\nCREATE SESSION\nSELECT_CATALOG_ROLE\n"
    result = parse_validation_output(spool)

    assert result.account_open
    assert result.ok


def test_garbage_spool_raises_clear_parse_error() -> None:
    with pytest.raises(ValueError, match="SQL\\*Plus validation spool"):
        parse_validation_output("not the validation query output")
