"""Configure orchestrator: detect -> branch by location -> gate -> act."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from dbman_opsi.checks import PreflightReport, TargetReport
from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.datasafe import DataSafeDecision, DataSafeService
from dbman_opsi.enablement import EnablementService
from dbman_opsi.handoff import generate_handoff
from dbman_opsi.oci_cli import OciCli
from dbman_opsi.preflight import PreflightService
from dbman_opsi.status import dbm_status, is_enabled

Mode = Literal["plan", "apply", "db-side-only"]
Action = Literal["skip-enabled", "blocked", "handoff", "ready", "enabled", "stopped-not-found"]


@dataclass(frozen=True)
class TargetDecision:
    name: str
    kind: str
    location: str
    action: Action
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "location": self.location,
            "action": self.action,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ConfigureReport:
    mode: Mode
    preflight: PreflightReport
    decisions: tuple[TargetDecision, ...]
    handoff_paths: tuple[Path, ...] = ()
    data_safe: tuple[DataSafeDecision, ...] = ()

    @property
    def ok(self) -> bool:
        return all(decision.action != "blocked" for decision in self.decisions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "ok": self.ok,
            "preflight": self.preflight.to_dict(),
            "decisions": [decision.to_dict() for decision in self.decisions],
            "handoff_paths": [str(path) for path in self.handoff_paths],
            "data_safe": [decision.to_dict() for decision in self.data_safe],
        }


class ConfigureService:
    def __init__(
        self,
        oci: OciCli,
        enablement: EnablementService | None = None,
        datasafe: DataSafeService | None = None,
    ) -> None:
        self.oci = oci
        self.preflight = PreflightService(oci)
        self.enablement = enablement or EnablementService(oci)
        self.datasafe = datasafe

    def configure(
        self,
        config: EnablementConfig,
        mode: Mode = "plan",
        handoff_dir: str | Path = "generated/handoff",
        force: bool = False,
    ) -> ConfigureReport:
        report = self.preflight.run(config)
        targets_by_name = {target.name: target for target in config.targets}
        # Enable container databases before pluggable databases: PDB Database
        # Management depends on the parent CDB already being enabled.
        ordered = sorted(
            report.targets,
            key=lambda target_report: targets_by_name[target_report.name].database_role == "PDB",
        )
        decisions: list[TargetDecision] = []
        enabled_parent_ids: set[str] = set()
        for target_report in ordered:
            target = targets_by_name[target_report.name]
            decision = self._decide(
                target,
                target_report,
                report,
                mode,
                force,
                enabled_parent_ids,
            )
            decisions.append(decision)
            if decision.action in {"enabled", "skip-enabled"} and target.database_role != "PDB" and target.resource_id:
                enabled_parent_ids.add(target.resource_id)
        handoff_paths: tuple[Path, ...] = ()
        if any(decision.action == "handoff" for decision in decisions):
            handoff_paths = tuple(generate_handoff(config, handoff_dir))
        # Third pillar: when a Data Safe service is wired and we are applying,
        # register Data Safe targets for the targets that opted into 'datasafe'.
        # Additive — a blocked Data Safe registration does not fail the DBM/OPSI
        # flow (it surfaces as a data_safe decision the operator can act on).
        data_safe: tuple[DataSafeDecision, ...] = ()
        if mode == "apply" and self.datasafe is not None:
            data_safe = tuple(self.datasafe.enable_all(config))
        return ConfigureReport(
            mode=mode,
            preflight=report,
            decisions=tuple(decisions),
            handoff_paths=handoff_paths,
            data_safe=data_safe,
        )

    def _decide(
        self,
        target: Target,
        target_report: TargetReport,
        report: PreflightReport,
        mode: Mode,
        force: bool,
        enabled_parent_ids: set[str],
    ) -> TargetDecision:
        base = {"name": target.name, "kind": target.kind, "location": target_report.location}

        # 1. DETECT + STATE: skip if already enabled.
        if self._already_enabled(target):
            if self._opsi_ready(target):
                if mode == "apply":
                    self.enablement.enable_opsi(target)
                    return TargetDecision(
                        **base,
                        action="enabled",
                        reason="Database Management already enabled; Ops Insights command executed",
                    )
                return TargetDecision(
                    **base,
                    action="ready",
                    reason="Database Management already enabled; rerun with --apply to ensure Ops Insights",
                )
            return TargetDecision(**base, action="skip-enabled", reason="Database Management already enabled")

        # 2. DB-side work is independent of OCI prerequisites: always hand off so the
        #    DBA can create the monitoring user in parallel with fixing OCI-side gaps.
        if mode == "db-side-only":
            return TargetDecision(**base, action="handoff", reason="Generated DB-side handoff packet")

        # 3. GATE: shared (IAM, and network for native) + per-target blocking checks.
        blockers = self._blockers(target, target_report, report, force, enabled_parent_ids)
        if blockers:
            return TargetDecision(**base, action="blocked", reason="; ".join(blockers))

        # 4. ACT by mode.
        if mode == "apply":
            self.enablement.enable_target(target)
            return TargetDecision(**base, action="enabled", reason="Enablement command executed")
        return TargetDecision(**base, action="ready", reason="Prerequisites satisfied; rerun with --apply")

    def _blockers(
        self,
        target: Target,
        target_report: TargetReport,
        report: PreflightReport,
        force: bool,
        enabled_parent_ids: set[str],
    ) -> list[str]:
        if force:
            return []
        blockers = [f"iam: {check.detail}" for check in report.tenancy_checks if check.blocking]
        if target_report.location == "oci-native":
            blockers += [f"network: {check.detail}" for check in report.network_checks if check.blocking]
        parent_enabled_in_run = (
            target.database_role == "PDB"
            and target.parent_cdb_id is not None
            and target.parent_cdb_id in enabled_parent_ids
        )
        blockers += [
            f"{check.name}: {check.detail}"
            for check in target_report.blocking_failures
            if not (parent_enabled_in_run and check.name == "target.parent_cdb")
        ]
        return blockers

    def _already_enabled(self, target: Target) -> bool:
        if not target.resource_id:
            return False
        try:
            if target.kind == "autonomous":
                details = self.oci.get_autonomous_database(target.resource_id)
            elif target.database_role == "PDB":
                details = self.oci.get_pluggable_database(target.resource_id)
            elif target.kind in {"dbcs", "exadata"}:
                details = self.oci.get_database(target.resource_id)
            else:
                return False
        except Exception:  # noqa: BLE001 - treat unreadable state as not-enabled
            return False
        return is_enabled(dbm_status(details, target.kind, target.database_role))

    @staticmethod
    def _opsi_ready(target: Target) -> bool:
        if target.kind not in {"dbcs", "exadata"}:
            return False
        return all(
            (
                target.compartment_id,
                target.resource_id,
                target.service_name,
                target.private_endpoint_id,
                target.opsi_private_endpoint_id,
                target.opsi_credential_details_file,
            )
        )
