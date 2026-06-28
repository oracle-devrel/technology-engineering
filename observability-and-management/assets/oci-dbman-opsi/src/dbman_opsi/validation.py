"""Validation checks for configured enablement."""

from __future__ import annotations

import time
from typing import Callable

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.status import dbm_status, opsi_status


class ValidationService:
    def __init__(
        self,
        oci: OciCli,
        *,
        oci_for_region: Callable[[str], OciCli] | None = None,
        insight_attempts: int = 5,
        insight_delay: float = 2.0,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        self.oci = oci
        self.oci_for_region = oci_for_region or (lambda _region: self.oci)
        self.insight_attempts = max(1, insight_attempts)
        self.insight_delay = insight_delay
        self.sleeper = sleeper

    def validate(self, config: EnablementConfig) -> list[str]:
        findings: list[str] = []
        for target in config.targets:
            region = target.region or config.region
            oci = self.oci_for_region(region)
            region_suffix = f" [{region}]" if region != config.region else ""
            if target.kind in {"external-db", "external-exadata"}:
                agents = oci.list_management_agents(target.compartment_id or config.compartment_id or "")
                matched = [agent for agent in agents if target.name.lower() in str(agent.get("display-name", "")).lower()]
                if not matched:
                    findings.append(f"{target.name}{region_suffix}: Management Agent not found yet")
                    continue
                findings.append(f"{target.name}{region_suffix}: Management Agent registered")
            elif not target.resource_id:
                findings.append(f"{target.name}{region_suffix}: missing resource OCID")
            elif target.kind == "autonomous":
                details = oci.get_autonomous_database(target.resource_id)
                dbmgmt = dbm_status(details, target.kind) or "NOT_ENABLED"
                opsi = opsi_status(details, target.kind) or "NOT_ENABLED"
                findings.append(f"{target.name}{region_suffix}: Database Management {dbmgmt}; Ops Insights {opsi}")
            elif target.kind in {"dbcs", "exadata"}:
                if target.database_role == "PDB":
                    details = oci.get_pluggable_database(target.resource_id)
                else:
                    details = oci.get_database(target.resource_id)
                dbmgmt = dbm_status(details, target.kind, target.database_role) or "NOT_ENABLED"
                opsi = self._opsi_insight_state(target, config, oci)
                findings.append(
                    f"{target.name}{region_suffix} ({target.database_role}): Database Management {dbmgmt}; "
                    f"Ops Insights {opsi}"
                )
            else:
                findings.append(
                    f"{target.name}{region_suffix}: validate Database Management and Ops Insights status in OCI Console/API"
                )
        return findings

    def _opsi_insight_state(self, target: "Target", config: EnablementConfig, oci: OciCli) -> str:
        """Resolve the real OPSI Database Insight lifecycle for a DBCS/Exadata target.

        Returns e.g. ``ACTIVE (ENABLED)``, ``FAILED (ENABLED)``,
        ``NOT_FOUND (no Database Insight)`` or
        ``UNKNOWN (insight query failed; verify in OCI Console)`` so a broken
        Ops Insights collection is surfaced instead of hidden behind a generic
        "needs validation" message.

        The cap OPSI ``database-insights list`` control plane is *unreliable*: it
        flaps between the full set, a partial set, and an exit-0 empty list (and
        sometimes ``NotAuthorizedOrNotFound``) for the same compartment, call to
        call (see KB / runbook "Known cap quirk"). A single-resource
        ``database-insights get`` by insight OCID, by contrast, is reliable
        (10/10 in cap). So:

        1. If the insight OCID is known (``target.opsi_database_insight_id`` in
           config, or discovered from a positive list hit), read state with the
           reliable GET. This is the authoritative path.
        2. Otherwise fall back to the flapping list with a verdict model that
           never emits a *false* NOT_FOUND:

           * **Positive is authoritative** — a ``database-id`` can't appear
             unless the insight exists; resolve its OCID and GET it.
           * **Negative needs stability** — only ``NOT_FOUND`` when the list
             returns the *same* non-empty id-set on ≥2 attempts without our
             database (endpoint behaving, insight genuinely gone).
           * **Everything else is ``UNKNOWN``** — empty/erroring reads or a
             varying id-set mean the endpoint is dropping entries.
        """

        compartment = target.compartment_id or config.compartment_id or ""
        if not compartment:
            return "UNKNOWN (no compartment in config)"

        # 1. Authoritative path: GET by known insight OCID.
        if target.opsi_database_insight_id:
            state = self._insight_state_by_id(oci, target.opsi_database_insight_id)
            if state is not None:
                return state

        # 2. Fall back to the flapping list to discover the insight / decide absence.
        #    A negative verdict (NOT_FOUND) is only safe from a *clean* window:
        #    every attempt answered, every answer was a complete per-state union
        #    (no skipped lifecycle state), non-empty, and the same id-set — and our
        #    database was reproducibly absent. Any empty / erroring / incomplete /
        #    varying read makes the window inconclusive (UNKNOWN), never a false
        #    NOT_FOUND. A positive id match is always authoritative.
        answered_id_sets: list[frozenset[str]] = []
        clean_window = True
        for attempt in range(self.insight_attempts):
            insights, complete = self._list_insights(oci, compartment)
            for insight in insights or []:
                if insight.get("database-id") == target.resource_id:
                    # Positive hit: prefer the reliable GET for the real state.
                    insight_id = insight.get("id")
                    if insight_id:
                        state = self._insight_state_by_id(oci, str(insight_id))
                        if state is not None:
                            return state
                    state = insight.get("lifecycle-state") or "UNKNOWN"
                    status = insight.get("status") or "UNKNOWN"
                    return f"{state} ({status})"
            if insights and complete:
                answered_id_sets.append(frozenset(str(i.get("database-id")) for i in insights))
            else:
                # Empty, erroring, or incomplete (a lifecycle state was skipped, so
                # an insight could be hiding in it) — cannot prove absence.
                clean_window = False
            if attempt < self.insight_attempts - 1:
                self.sleeper(self.insight_delay)

        if (
            clean_window
            and len(answered_id_sets) >= 2
            and all(s == answered_id_sets[0] for s in answered_id_sets)
        ):
            return "NOT_FOUND (no Database Insight)"
        return "UNKNOWN (insight query failed; verify in OCI Console)"

    def _list_insights(self, oci: OciCli, compartment: str) -> tuple[list[dict[str, object]], bool]:
        """Return ``(insights, complete)`` from the OPSI list facade.

        Uses :meth:`OciCli.list_opsi_database_insights_complete` when available so
        an incomplete per-state union (a skipped lifecycle state) is flagged and
        never trusted for a negative verdict; otherwise degrades to the plain list
        (treated as complete, with a RuntimeError counted as an erroring read).
        """

        complete_getter = getattr(oci, "list_opsi_database_insights_complete", None)
        if complete_getter is not None:
            try:
                insights, complete = complete_getter(compartment)
            except RuntimeError:
                return [], False
            return list(insights or []), bool(complete)
        try:
            return list(oci.list_opsi_database_insights(compartment) or []), True
        except RuntimeError:
            return [], False

    def _insight_state_by_id(self, oci: OciCli, insight_id: str) -> str | None:
        """Read an insight's state via the reliable single-resource GET.

        Returns ``"<lifecycle> (<status>)"`` or ``None`` when the GET could not
        be read (so the caller can fall back to the list path).
        """

        getter = getattr(oci, "get_opsi_database_insight", None)
        if getter is None:
            return None
        for _ in range(2):
            try:
                detail = getter(insight_id)
            except RuntimeError:
                detail = {}
            if detail:
                state = detail.get("lifecycle-state") or "UNKNOWN"
                status = detail.get("status") or "UNKNOWN"
                return f"{state} ({status})"
        return None
