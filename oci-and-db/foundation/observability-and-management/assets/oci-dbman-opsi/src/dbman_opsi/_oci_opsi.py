"""Operations Insights: private endpoints and database insights.

The per-lifecycle-state union in ``list_opsi_database_insights_complete`` works
around an observed OPSI list control-plane flap on cap/eu-frankfurt-1 — see the
method docstrings for the root-cause notes (kept verbatim; they encode hard-won
operational knowledge).
"""

from __future__ import annotations

from typing import Any

from dbman_opsi._oci_base import _OciBase


class OpsiCommands(_OciBase):
    # OPSI database-insights list excludes FAILED/terminal states by default, so
    # the non-ACTIVE states are queried explicitly to surface broken insights
    # during validate.
    OPSI_INSIGHT_STATES = ("CREATING", "UPDATING", "ACTIVE", "FAILED", "NEEDS_ATTENTION")

    def list_opsi_private_endpoints(self, compartment_id: str) -> list[dict[str, Any]]:
        data = self.run_json(["opsi", "opsi-private-endpoint", "list", "--compartment-id", compartment_id, "--all"])
        return self._items(data)

    def get_opsi_private_endpoint(self, endpoint_id: str) -> dict[str, Any]:
        return self._data(self.run_json([
            "opsi",
            "opsi-private-endpoint",
            "get",
            "--opsi-private-endpoint-id",
            endpoint_id,
        ]))

    def list_opsi_database_insights(self, compartment_id: str) -> list[dict[str, Any]]:
        """List OPSI database insights across all relevant lifecycle states.

        Root-cause note (cap, eu-frankfurt-1): combining the full ``--lifecycle-state``
        set with ``--all`` in a *single* call makes the OPSI list control plane
        flap — it intermittently returns an empty or partial page for the same
        compartment (observed bouncing between 0, 2, and 7 items call-to-call).
        A single-lifecycle-state query is stable (ACTIVE-only returned the same
        full set 10/10 times). So query one state per call and union the results
        by insight OCID: reliable, and still surfaces FAILED/terminal insights
        that the default ACTIVE-only list hides.

        Per-state calls are individually fault-tolerant: a transient failure on
        one state is skipped so it cannot discard the insights already gathered
        from the other states. If every state call fails the result is empty,
        which callers treat as inconclusive rather than authoritative absence.

        Note: a skipped state means the union is *incomplete* — an insight that
        only exists in the failed state (e.g. ``FAILED``) is silently absent. A
        caller that needs to assert *absence* must use
        :meth:`list_opsi_database_insights_complete` and refuse to conclude
        "not found" from an incomplete read.
        """

        return self.list_opsi_database_insights_complete(compartment_id)[0]

    def list_opsi_database_insights_complete(
        self, compartment_id: str
    ) -> tuple[list[dict[str, Any]], bool]:
        """Per-state union plus a completeness flag.

        Returns ``(insights, complete)`` where ``complete`` is ``False`` if any
        per-lifecycle-state call failed (so the union may be missing insights
        that live in the failed state). Callers can trust a *positive* match
        regardless of ``complete``, but must treat a *negative* result from an
        incomplete read as inconclusive rather than authoritative absence.
        """

        merged: dict[str, dict[str, Any]] = {}
        complete = True
        for state in self.OPSI_INSIGHT_STATES:
            args = [
                "opsi",
                "database-insights",
                "list",
                "--compartment-id",
                compartment_id,
                "--compartment-id-in-subtree",
                "true",
                "--all",
                "--lifecycle-state",
                state,
            ]
            try:
                items = self._items(self.run_json(args))
            except RuntimeError:
                complete = False
                continue
            for item in items:
                key = str(item.get("id") or item.get("database-id"))
                merged[key] = item
        return list(merged.values()), complete

    def get_opsi_database_insight(self, insight_id: str) -> dict[str, Any]:
        """Get a single OPSI database insight by its OCID.

        Unlike the aggregated ``database-insights list`` (which flaps between
        empty/partial/full on the cap control plane), a single-resource GET by
        insight OCID is reliable — the authoritative way to read an insight's
        lifecycle/connection state once its OCID is known.
        """

        return self._data(self.run_json([
            "opsi",
            "database-insights",
            "get",
            "--database-insight-id",
            insight_id,
        ]))
