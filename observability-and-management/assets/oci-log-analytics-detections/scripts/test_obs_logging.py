"""Unit tests for the shared structured-logging adapter (scripts/obs_logging.py)."""
from __future__ import annotations

import importlib
import logging
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

import obs_logging  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_logging_state():
    """Isolate each test: clear our handler registry and any loggers we made."""
    obs_logging._CONFIGURED_LOGGERS.clear()
    yield
    for name in list(logging.Logger.manager.loggerDict):
        if name.startswith("obs_test"):
            log = logging.getLogger(name)
            for handler in list(log.handlers):
                log.removeHandler(handler)
    obs_logging._CONFIGURED_LOGGERS.clear()


def _reload_with_env(monkeypatch, **env):
    """Reload the module under a given environment (run_id/level are module-level)."""
    for key in ("OCI_RUN_ID", "OCI_LOG_LEVEL", "OCI_LOG_FORMAT"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return importlib.reload(obs_logging)


def test_get_logger_is_idempotent_no_duplicate_handlers():
    log_a = obs_logging.get_logger("obs_test.idem")
    count_after_first = len(log_a.handlers)
    log_b = obs_logging.get_logger("obs_test.idem")
    assert log_a is log_b
    assert len(log_b.handlers) == count_after_first == 1


def test_run_id_is_stable_within_process():
    first = obs_logging.RUN_ID
    second = obs_logging.RUN_ID
    assert first == second
    assert first  # non-empty


def test_oci_run_id_override(monkeypatch):
    mod = _reload_with_env(monkeypatch, OCI_RUN_ID="ci-correlation-42")
    try:
        assert mod.RUN_ID == "ci-correlation-42"
    finally:
        importlib.reload(_reload_with_env(monkeypatch))  # restore clean module


def test_run_id_defaults_to_pid_hex(monkeypatch):
    mod = _reload_with_env(monkeypatch)  # no OCI_RUN_ID
    try:
        assert mod.RUN_ID == f"{os.getpid():x}"
    finally:
        importlib.reload(mod)


def test_level_honored_from_env(monkeypatch):
    mod = _reload_with_env(monkeypatch, OCI_LOG_LEVEL="WARNING")
    try:
        log = mod.get_logger("obs_test.level")
        assert log.level == logging.WARNING
    finally:
        importlib.reload(mod)


def test_default_level_is_info(monkeypatch):
    mod = _reload_with_env(monkeypatch)
    try:
        log = mod.get_logger("obs_test.default_level")
        assert log.level == logging.INFO
    finally:
        importlib.reload(mod)


def test_logs_go_to_stderr_not_stdout(capsys):
    log = obs_logging.get_logger("obs_test.stream")
    log.warning("to-stderr-marker")
    captured = capsys.readouterr()
    assert "to-stderr-marker" not in captured.out
    assert "to-stderr-marker" in captured.err


def test_logfmt_fields_present(capsys):
    log = obs_logging.get_logger("obs_test.fmt")
    log.info("hello world")
    err = capsys.readouterr().err
    assert "ts=" in err
    assert "level=INFO" in err
    assert f"run={obs_logging.RUN_ID}" in err
    assert "logger=obs_test.fmt" in err
    assert 'msg="hello world"' in err  # message with spaces is quoted


def test_bind_injects_structured_fields(capsys):
    log = obs_logging.get_logger("obs_test.bind")
    blog = obs_logging.bind(log, profile="cap", compartment="cmpt-x")
    blog.info("validating")
    err = capsys.readouterr().err
    assert "profile=cap" in err
    assert "compartment=cmpt-x" in err
    assert 'msg=validating' in err


def test_bind_merges_nested_binds(capsys):
    log = obs_logging.get_logger("obs_test.bind2")
    blog = obs_logging.bind(obs_logging.bind(log, a="1"), b="2")
    blog.info("merged")
    err = capsys.readouterr().err
    assert "a=1" in err
    assert "b=2" in err


def test_extra_context_namespace_emitted(capsys):
    log = obs_logging.get_logger("obs_test.ctx")
    log.info("with-ctx", extra={"context": {"widget": "w1"}})
    err = capsys.readouterr().err
    assert "widget=w1" in err


def test_plain_format_is_human_friendly(monkeypatch, capsys):
    mod = _reload_with_env(monkeypatch, OCI_LOG_FORMAT="plain")
    try:
        log = mod.get_logger("obs_test.plain")
        log.info("plain-msg")
        err = capsys.readouterr().err
        assert "plain-msg" in err
        assert "ts=" not in err  # logfmt prefix absent
    finally:
        importlib.reload(mod)


def test_importable_without_calling_logging():
    """Importing the module must not configure root or emit anything."""
    root = logging.getLogger()
    before = len(root.handlers)
    importlib.reload(obs_logging)
    assert len(logging.getLogger().handlers) == before
