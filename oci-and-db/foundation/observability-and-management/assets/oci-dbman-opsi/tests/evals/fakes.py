"""Fixture-driven OCI fake for the eval harness.

`ReplayOci` models the two behaviours that matter for the defect signatures:

* the **flaky aggregated LIST** — `list_opsi_database_insights[_complete]` replays
  a caller-supplied sequence of `(items, complete)` tuples, one per call, so an
  eval can reproduce the full/partial/empty flap seen on the live control plane;
* the **reliable single-resource GET** — `get_opsi_database_insight` and the
  database GETs return fixed fixtures, mirroring production where GET-by-OCID is
  trustworthy where the LIST is not.

It also supports the prerequisites write path (`run` / `run_tolerating`) with an
optional create-conflict to reproduce the list-first-miss idempotency case.
"""

from __future__ import annotations

from typing import Any


class ReplayOci:
    def __init__(
        self,
        *,
        databases: dict[str, dict[str, Any]] | None = None,
        pluggables: dict[str, dict[str, Any]] | None = None,
        autonomous: dict[str, dict[str, Any]] | None = None,
        insight_get: dict[str, dict[str, Any]] | None = None,
        insight_list_sequence: list[tuple[list[dict[str, Any]], bool]] | None = None,
        create_conflict: str | None = None,
        existing_dbm_pes: list[dict[str, Any]] | None = None,
        existing_opsi_pes: list[dict[str, Any]] | None = None,
    ) -> None:
        self.databases = databases or {}
        self.pluggables = pluggables or {}
        self.autonomous = autonomous or {}
        self.insight_get = insight_get or {}
        # Each call to the OPSI list returns the next (items, complete) tuple; the
        # last entry repeats once exhausted.
        self.insight_list_sequence = insight_list_sequence or [([], True)]
        self.create_conflict = create_conflict
        self.existing_dbm_pes = existing_dbm_pes or []
        self.existing_opsi_pes = existing_opsi_pes or []
        self.commands: list[list[str]] = []
        self._list_calls = 0
        self.get_insight_calls: list[str] = []

    # --- resource GETs (reliable) -------------------------------------
    def get_database(self, resource_id: str) -> dict[str, Any]:
        return self.databases.get(resource_id, {})

    def get_pluggable_database(self, resource_id: str) -> dict[str, Any]:
        return self.pluggables.get(resource_id, {})

    def get_autonomous_database(self, resource_id: str) -> dict[str, Any]:
        return self.autonomous.get(resource_id, {})

    def get_opsi_database_insight(self, insight_id: str) -> dict[str, Any]:
        self.get_insight_calls.append(insight_id)
        return self.insight_get.get(insight_id, {})

    def list_management_agents(self, compartment_id: str) -> list[dict[str, Any]]:
        return []

    # --- OPSI insight LIST (flaky) ------------------------------------
    def list_opsi_database_insights_complete(self, compartment_id: str) -> tuple[list[dict[str, Any]], bool]:
        idx = min(self._list_calls, len(self.insight_list_sequence) - 1)
        self._list_calls += 1
        items, complete = self.insight_list_sequence[idx]
        return list(items), complete

    def list_opsi_database_insights(self, compartment_id: str) -> list[dict[str, Any]]:
        return self.list_opsi_database_insights_complete(compartment_id)[0]

    # --- prerequisites write path -------------------------------------
    def list_db_management_private_endpoints(self, compartment_id: str) -> list[dict[str, Any]]:
        return self.existing_dbm_pes

    def list_opsi_private_endpoints(self, compartment_id: str) -> list[dict[str, Any]]:
        return self.existing_opsi_pes

    def run(self, args: list[str]) -> None:
        self.commands.append(args)
        if self.create_conflict is not None:
            raise RuntimeError(self.create_conflict)

    def run_tolerating(self, args: list[str], tolerated: tuple[str, ...]) -> bool:
        try:
            self.run(args)
            return True
        except RuntimeError as exc:
            if any(marker in str(exc) for marker in tolerated):
                return False
            raise
