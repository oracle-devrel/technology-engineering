"""Connection-string helpers shared by discovery and the wizard.

A single canonical parser for the OCI ``connection-strings`` shape so the
PDB-grain service-name logic — the field that disambiguates a PDB's Data Safe
target from its CDB's — lives in exactly one place and cannot drift between the
read-only inventory (``discovery``) and the interactive planner (``wizard``).
"""

from __future__ import annotations

from typing import Any


def service_name_from_record(record: dict[str, Any]) -> str | None:
    """Return a DB's service name from its connection strings, or ``None``.

    Reads ``connection-strings`` in OCI's documented precedence
    (``pdb-default`` → ``cdb-default`` → ``all-connection-strings.cdbDefault``)
    and returns the portion after the last ``'/'``. Returns ``None`` when no
    connection string is present or the value carries no ``/service`` path, so
    callers can decide their own fallback.
    """

    strings = record.get("connection-strings")
    if not isinstance(strings, dict):
        return None
    all_strings = strings.get("all-connection-strings")
    value = (
        strings.get("pdb-default")
        or strings.get("cdb-default")
        or (all_strings.get("cdbDefault") if isinstance(all_strings, dict) else None)
    )
    if isinstance(value, str) and "/" in value:
        return value.rsplit("/", 1)[-1]
    return None
