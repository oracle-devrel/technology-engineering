"""Shared structured-logging adapter for the live-OCI scripts.

Goal: production runs of the live-OCI scripts (dashboard deploy, log-source
setup, ingestion, Sentinel conversion, parse/health validation) emit
correlatable, level-controlled, machine-parseable diagnostics on **stderr**
instead of bare ``print()`` — without disturbing the **stdout** contract that
tests and pipelines consume (JSON reports, summary tables, result lines).

Design constraints (deliberate):
  * Stdlib ``logging`` only — no third-party dependencies.
  * Logs always go to **stderr**. stdout is reserved for CLI output.
  * One short, stable ``run_id`` per process so multi-line runs correlate.
    Derived from ``OCI_RUN_ID`` (CI override) or ``os.getpid()`` — never from
    wall-clock/``random`` so repo hooks that forbid nondeterminism stay happy.
  * Level honored from ``OCI_LOG_LEVEL`` (default ``INFO``).
  * ``OCI_LOG_FORMAT=plain`` switches to a human-friendly format for local dev;
    the default is logfmt (``ts=... level=INFO run=ab12 msg="..." k=v``).
  * Idempotent: ``get_logger`` never double-adds handlers.

Usage::

    import obs_logging
    log = obs_logging.get_logger(__name__)
    log.info("Connecting to OCI", extra={"context": {"profile": profile}})
    blog = obs_logging.bind(log, profile=profile, compartment=cmpt)
    blog.warning("retrying")
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Mapping

# ─── run_id: one short, stable id per process ────────────────────────────────
# OCI_RUN_ID lets a CI job stamp every script in a pipeline with one correlation
# id. Otherwise we fall back to the (stable-within-process) PID in hex. We never
# use time/random so deterministic-output hooks don't flag this module.
RUN_ID: str = os.environ.get("OCI_RUN_ID") or f"{os.getpid():x}"

_DEFAULT_LEVEL = "INFO"
_CONFIGURED_LOGGERS: set[str] = set()

# Reserved LogRecord attributes — anything *not* in here that lands on a record
# is treated as a structured field and emitted as key=value.
_RESERVED_RECORD_KEYS = frozenset(
    vars(logging.makeLogRecord({})).keys()
) | {"message", "asctime", "context", "taskName"}


def _resolve_level() -> int:
    """Resolve the logging level from ``OCI_LOG_LEVEL`` (default INFO)."""
    name = (os.environ.get("OCI_LOG_LEVEL") or _DEFAULT_LEVEL).strip().upper()
    return logging.getLevelName(name) if isinstance(logging.getLevelName(name), int) else logging.INFO


def _logfmt_quote(value: Any) -> str:
    """Render a value for a logfmt key=value pair, quoting when needed."""
    text = str(value)
    if text == "" or any(ch in text for ch in (" ", "=", '"', "\n", "\t")):
        escaped = text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\t", " ")
        return f'"{escaped}"'
    return text


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    """Collect structured fields attached to a record via ``extra=``.

    Supports both ``extra={"k": v}`` (flat) and ``extra={"context": {...}}``
    (namespaced) so call sites can use whichever reads better.
    """
    fields: dict[str, Any] = {}
    context = getattr(record, "context", None)
    if isinstance(context, Mapping):
        fields.update(context)
    for key, value in record.__dict__.items():
        if key in _RESERVED_RECORD_KEYS:
            continue
        if key.startswith("_"):
            continue
        fields[key] = value
    return fields


class LogfmtFormatter(logging.Formatter):
    """Emit one logfmt line: ``ts=... level=INFO run=ab12 logger=x msg="..." k=v``."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat()
        parts = [
            f"ts={ts}",
            f"level={record.levelname}",
            f"run={RUN_ID}",
            f"logger={record.name}",
            f"msg={_logfmt_quote(record.getMessage())}",
        ]
        for key, value in _extra_fields(record).items():
            parts.append(f"{key}={_logfmt_quote(value)}")
        if record.exc_info:
            parts.append(f"exc={_logfmt_quote(self.formatException(record.exc_info))}")
        return " ".join(parts)


class PlainFormatter(logging.Formatter):
    """Human-friendly format for local dev (``OCI_LOG_FORMAT=plain``)."""

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime("%H:%M:%S")
        base = f"{ts} {record.levelname:<7} [{record.name}] {record.getMessage()}"
        fields = _extra_fields(record)
        if fields:
            base += " " + " ".join(f"{k}={v}" for k, v in fields.items())
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base


def _build_formatter() -> logging.Formatter:
    if (os.environ.get("OCI_LOG_FORMAT") or "").strip().lower() == "plain":
        return PlainFormatter()
    return LogfmtFormatter()


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger that writes structured lines to **stderr**.

    Idempotent: calling twice for the same name does not double-add handlers.
    Honors ``OCI_LOG_LEVEL`` (default INFO) and ``OCI_LOG_FORMAT`` (logfmt|plain).
    """
    logger = logging.getLogger(name)
    level = _resolve_level()
    logger.setLevel(level)
    # Do not let records bubble to the root logger (which may have its own
    # stdout/stderr handlers) — that would both duplicate lines and risk
    # leaking diagnostics onto stdout.
    logger.propagate = False

    if name in _CONFIGURED_LOGGERS and logger.handlers:
        # Already configured by us — only refresh the level (env may differ
        # across calls in tests) and the formatter, never add a second handler.
        for handler in logger.handlers:
            if getattr(handler, "_obs_logging", False):
                handler.setLevel(level)
                handler.setFormatter(_build_formatter())
        return logger

    handler = logging.StreamHandler()  # defaults to sys.stderr
    handler._obs_logging = True  # type: ignore[attr-defined]
    handler.setLevel(level)
    handler.setFormatter(_build_formatter())
    logger.addHandler(handler)
    _CONFIGURED_LOGGERS.add(name)
    return logger


def bind(logger: logging.Logger | logging.LoggerAdapter, **fields: Any) -> logging.LoggerAdapter:
    """Return a ``LoggerAdapter`` that injects ``fields`` as structured kv pairs.

    Example::

        blog = bind(log, profile="cap", compartment=cmpt)
        blog.info("validating")   # -> ... msg="validating" profile=cap compartment=...
    """
    base_fields: dict[str, Any] = {}
    if isinstance(logger, logging.LoggerAdapter):
        existing = logger.extra.get("context") if isinstance(logger.extra, Mapping) else None
        if isinstance(existing, Mapping):
            base_fields.update(existing)
        logger = logger.logger
    base_fields.update(fields)
    return logging.LoggerAdapter(logger, {"context": base_fields})
