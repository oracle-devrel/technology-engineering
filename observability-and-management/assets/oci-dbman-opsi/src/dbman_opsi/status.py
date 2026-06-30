"""Accessors for Database Management / Ops Insights status across resource shapes.

OCI exposes enablement status differently per resource:

- Autonomous Database: top-level ``database-management-status`` /
  ``operations-insights-status``.
- Container/non-CDB database (``db database get``): nested under
  ``database-management-config.management-status``.
- Pluggable database (``db pluggable-database get``): nested under
  ``pluggable-database-management-config.management-status``.
"""

from __future__ import annotations

from typing import Any

_ENABLED_STATES = {"ENABLED", "ENABLING"}


def dbm_status(details: dict[str, Any], kind: str, role: str = "CDB") -> str | None:
    """Return the Database Management status for any supported resource shape."""

    if kind == "autonomous":
        return details.get("database-management-status")
    if role == "PDB":
        config = details.get("pluggable-database-management-config") or {}
    else:
        config = details.get("database-management-config") or {}
    return config.get("management-status") or config.get("database-management-status")


def opsi_status(details: dict[str, Any], kind: str) -> str | None:
    """Ops Insights status (only carried on the Autonomous Database resource)."""

    if kind == "autonomous":
        return details.get("operations-insights-status")
    return None


def is_enabled(status: str | None) -> bool:
    return str(status or "").upper() in _ENABLED_STATES


# Lifecycle states that count as an OPSI insight or Data Safe target being "on".
_RESOURCE_ENABLED_STATES = {"ACTIVE", "CREATING", "UPDATING"}


def _candidate_ids(record: dict[str, Any]) -> set[str]:
    """Collect every OCID a separate resource might use to reference a DB.

    Important: do NOT include the record's own ``id`` — that is the insight/target
    OCID, not the database it points at, and including it would never help a match
    while risking false positives. The Data Safe ``target-database list`` summary
    carries the join key in ``associated-resource-ids`` (the registered DB's OCID),
    while the full GET carries it under ``database-details``; OPSI insights carry
    it as ``database-id``. Read all of these.
    """

    details = record.get("database-details") or {}
    ids: set[Any] = {
        record.get("database-id"),
        details.get("database-id"),
        details.get("db-system-id"),
        details.get("autonomous-database-id"),
        details.get("vm-cluster-id"),
        details.get("infrastructure-id"),
    }
    associated = record.get("associated-resource-ids")
    if isinstance(associated, list):
        ids.update(associated)
    return {str(value) for value in ids if value}


def opsi_insight_status(insights: list[dict[str, Any]], db_id: str) -> str:
    """ENABLED if an OPSI insight references ``db_id`` and is in an active state."""

    for insight in insights:
        if db_id in _candidate_ids(insight):
            if str(insight.get("lifecycle-state", "")).upper() in _RESOURCE_ENABLED_STATES:
                return "ENABLED"
            return str(insight.get("lifecycle-state") or "NOT_ENABLED")
    return "NOT_ENABLED"


def _target_state(target: dict[str, Any]) -> str:
    if str(target.get("lifecycle-state", "")).upper() in _RESOURCE_ENABLED_STATES:
        return "ENABLED"
    return str(target.get("lifecycle-state") or "NOT_ENABLED")


def data_safe_status(
    targets: list[dict[str, Any]],
    db_id: str,
    db_system_id: str | None = None,
    service_name: str | None = None,
) -> str:
    """ENABLED if a Data Safe target-database references this specific DB.

    Data Safe registration is a standalone ``target-database`` resource. Match in
    order of precision so a Base Database CDB and its PDBs are attributed
    correctly even though they share a DB system OCID:

    1. **Exact OCID** — the target's database details / associations contain this
       DB's OCID (autonomous: ``autonomous-database-id``; or a target keyed by the
       DB OCID directly).
    2. **Service name** — the target's ``database-details.service-name`` equals
       this DB's service. This disambiguates which PDB (or the CDB root) a
       ``DATABASE_CLOUD_SERVICE`` target covers; targets must be GET-enriched for
       ``database-details`` to be present (the LIST summary has it null).
    3. **Coarse DB-system fallback** — only for targets that carry *no*
       service-name to disambiguate with; keeps a CDB ENABLED when the target
       summary could not be enriched.
    """

    coarse_state: str | None = None
    for target in targets:
        candidate_ids = _candidate_ids(target)
        details = target.get("database-details") or {}
        target_service = details.get("service-name")
        # 1 + 2: precise matches.
        if db_id in candidate_ids:
            return _target_state(target)
        # Oracle service names are case-insensitive (the listener may register
        # 'PDB1.x' while the target stored 'pdb1.x').
        if service_name and target_service and target_service.lower() == service_name.lower():
            return _target_state(target)
        # 3: remember a coarse DB-system match, but only when this target cannot
        # be disambiguated by service name (else it would over-match siblings).
        if db_system_id and not target_service and str(db_system_id) in candidate_ids:
            coarse_state = _target_state(target)
    return coarse_state or "NOT_ENABLED"
