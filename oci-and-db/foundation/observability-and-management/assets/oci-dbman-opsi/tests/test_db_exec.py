from pathlib import Path

import pytest

from dbman_opsi.config import EnablementConfig, Target
from dbman_opsi.db_exec import (
    DbExecService,
    ExecDecision,
    is_production_profile,
    ordered_scripts,
    should_auto_execute,
)


def test_production_profile_gate() -> None:
    assert is_production_profile("emdemo") is True
    assert is_production_profile("cap") is False
    assert should_auto_execute("cap") is True
    assert should_auto_execute("emdemo") is False
    # Force overrides the prod gate (explicit operator override).
    assert should_auto_execute("emdemo", force=True) is True


def test_ordered_scripts_returns_existing_in_run_order(tmp_path: Path) -> None:
    for name in ["02-grant-basic-monitoring.sql", "01-create-monitoring-user.sql",
                 "04-validate-monitoring-user.sql", "06-enable-data-safe.sql"]:
        (tmp_path / name).write_text("-- sql")
    names = [p.name for p in ordered_scripts(tmp_path)]
    # 01 first, 04 (validate) last, 06 before 04.
    assert names == [
        "01-create-monitoring-user.sql",
        "02-grant-basic-monitoring.sql",
        "06-enable-data-safe.sql",
        "04-validate-monitoring-user.sql",
    ]


def _config(profile: str) -> EnablementConfig:
    return EnablementConfig(
        profile=profile, region="eu-frankfurt-1",
        targets=(Target(kind="dbcs", name="dbmopsi"), Target(kind="autonomous", name="adb")),
    )


def test_plan_auto_execs_non_prod_and_skips_non_db_kinds() -> None:
    decisions = {d.target: d for d in DbExecService().plan(_config("cap"))}
    assert decisions["dbmopsi"].action == "executed"
    assert decisions["adb"].action == "skipped"  # autonomous has no DB-side scripts


def test_plan_hands_off_in_production() -> None:
    decisions = {d.target: d for d in DbExecService().plan(_config("emdemo"))}
    assert decisions["dbmopsi"].action == "handoff"


def test_execute_runs_scripts_via_injected_runner(tmp_path: Path) -> None:
    target_dir = tmp_path / "dbmopsi"
    target_dir.mkdir()
    (target_dir / "01-create-monitoring-user.sql").write_text("-- sql")
    (target_dir / "04-validate-monitoring-user.sql").write_text("-- sql")
    ran: list[tuple[str, list[str]]] = []

    def runner(target: Target, scripts: list[Path]) -> str:
        ran.append((target.name, [p.name for p in scripts]))
        return "ok"

    decisions = DbExecService(runner).execute(_config("cap"), tmp_path)
    by_target = {d.target: d for d in decisions}
    assert by_target["dbmopsi"].action == "executed"
    assert ran == [("dbmopsi", ["01-create-monitoring-user.sql", "04-validate-monitoring-user.sql"])]


def test_execute_in_production_hands_off_without_running(tmp_path: Path) -> None:
    target_dir = tmp_path / "dbmopsi"
    target_dir.mkdir()
    (target_dir / "01-create-monitoring-user.sql").write_text("-- sql")
    called = False

    def runner(target: Target, scripts: list[Path]) -> str:
        nonlocal called
        called = True
        return "ok"

    decisions = {d.target: d for d in DbExecService(runner).execute(_config("emdemo"), tmp_path)}
    assert decisions["dbmopsi"].action == "handoff"
    assert called is False


def test_execute_marks_failed_runner_without_aborting(tmp_path: Path) -> None:
    target_dir = tmp_path / "dbmopsi"
    target_dir.mkdir()
    (target_dir / "01-create-monitoring-user.sql").write_text("-- sql")

    def runner(target: Target, scripts: list[Path]) -> str:
        raise RuntimeError("ORA-12514")

    decisions = {d.target: d for d in DbExecService(runner).execute(_config("cap"), tmp_path)}
    assert decisions["dbmopsi"].action == "failed"
    assert "ORA-12514" in decisions["dbmopsi"].detail


def test_execute_auto_without_runner_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        DbExecService().execute(_config("cap"), tmp_path)


def test_exec_decision_to_dict() -> None:
    d = ExecDecision("t", "executed", "ok", ("01.sql",))
    assert d.to_dict() == {"target": "t", "action": "executed", "detail": "ok", "scripts": ["01.sql"]}
