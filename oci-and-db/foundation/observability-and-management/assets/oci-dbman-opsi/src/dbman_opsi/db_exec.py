"""Hybrid DB-side script execution: auto-run in non-prod, hand off in prod.

The toolkit generates DB-side SQL (monitoring user, grants, Performance Hub,
Data Safe) but does not run it by default. This module adds an opt-in executor
that *auto-runs* those scripts against the database in non-production tenancies
(e.g. the ``cap`` staging tenancy) while staying generate-and-handoff for
production (``emdemo``), where running SQL automatically is unsafe.

The actual SQL transport (Bastion port-forward -> ssh -> sqlplus) is injected as
a ``sql_runner`` callback so the gating/orchestration is testable without a live
database, and so the proven manual Bastion procedure can be plugged in for real
runs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.db_scripts import DB_SCRIPT_TARGETS

# Production tenancies where DB-side SQL must never be auto-executed; these always
# fall back to handoff. Keyed by OCI CLI profile name.
PROD_PROFILES = frozenset({"emdemo"})

# Runs a target's ordered SQL scripts and returns combined output. Raising is
# allowed and surfaces as a failed decision.
SqlRunner = Callable[[Target, "list[Path]"], str]


@dataclass(frozen=True)
class ExecDecision:
    target: str
    action: str  # executed | handoff | skipped | failed
    detail: str
    scripts: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"target": self.target, "action": self.action, "detail": self.detail, "scripts": list(self.scripts)}


def is_production_profile(profile: str) -> bool:
    return profile in PROD_PROFILES


def should_auto_execute(profile: str, force: bool = False) -> bool:
    """Auto-exec in non-prod; in prod only when explicitly forced."""

    if force:
        return True
    return not is_production_profile(profile)


# DB-side scripts in run order. 04 (validate) runs last so it confirms the grants.
SCRIPT_RUN_ORDER = (
    "01-create-monitoring-user.sql",
    "02-grant-basic-monitoring.sql",
    "03-grant-advanced-diagnostics.sql",
    "05-enable-performance-hub.sql",
    "06-enable-data-safe.sql",
    "04-validate-monitoring-user.sql",
)


def ordered_scripts(target_dir: Path) -> list[Path]:
    """Return the target's generated scripts in execution order (existing only)."""

    return [target_dir / name for name in SCRIPT_RUN_ORDER if (target_dir / name).exists()]


def _slug(name: str) -> str:
    return name.replace(" ", "-").lower()


class DbExecService:
    def __init__(self, sql_runner: SqlRunner | None = None) -> None:
        self.sql_runner = sql_runner

    def plan(self, config: EnablementConfig, force: bool = False) -> list[ExecDecision]:
        """Decide per target whether DB-side scripts auto-run or hand off."""

        auto = should_auto_execute(config.profile, force=force)
        decisions: list[ExecDecision] = []
        for target in config.targets:
            if target.kind not in DB_SCRIPT_TARGETS:
                decisions.append(ExecDecision(target.name, "skipped", f"kind {target.kind} has no DB-side scripts"))
                continue
            if auto:
                decisions.append(ExecDecision(
                    target.name, "executed",
                    f"non-production profile '{config.profile}': scripts will auto-run via Bastion",
                ))
            else:
                decisions.append(ExecDecision(
                    target.name, "handoff",
                    f"production profile '{config.profile}': generate-and-handoff (no auto-exec)",
                ))
        return decisions

    def execute(
        self,
        config: EnablementConfig,
        scripts_dir: str | Path,
        force: bool = False,
    ) -> list[ExecDecision]:
        """Auto-run DB-side scripts for non-prod targets via the injected runner.

        Production targets return a ``handoff`` decision and are left untouched.
        A runner that raises yields a ``failed`` decision so one bad target does
        not abort the others.
        """

        base = Path(scripts_dir)
        if should_auto_execute(config.profile, force=force) and self.sql_runner is None:
            raise ValueError("auto-execute requires a sql_runner; none provided")
        results: list[ExecDecision] = []
        for target in config.targets:
            if target.kind not in DB_SCRIPT_TARGETS:
                results.append(ExecDecision(target.name, "skipped", f"kind {target.kind} has no DB-side scripts"))
                continue
            if not should_auto_execute(config.profile, force=force):
                results.append(ExecDecision(
                    target.name, "handoff",
                    f"production profile '{config.profile}': run the handoff packet manually",
                ))
                continue
            target_dir = base / _slug(target.name)
            scripts = ordered_scripts(target_dir)
            if not scripts:
                results.append(ExecDecision(target.name, "skipped", f"no generated scripts in {target_dir}"))
                continue
            try:
                assert self.sql_runner is not None  # guarded above
                self.sql_runner(target, scripts)
            except Exception as exc:  # noqa: BLE001 - surface as a failed decision, keep going
                results.append(ExecDecision(target.name, "failed", str(exc), tuple(p.name for p in scripts)))
                continue
            results.append(ExecDecision(
                target.name, "executed", f"ran {len(scripts)} scripts via Bastion",
                tuple(p.name for p in scripts),
            ))
        return results
