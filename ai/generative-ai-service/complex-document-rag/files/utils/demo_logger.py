"""
Presentation-grade logging, on by default.

The pipeline already branches on DEMO_MODE in several places to downgrade noisy
internals — but DEMO_MODE is set by whether this module imports, and it never
existed, so those branches have always been dead. Creating it activates them.

What this changes for a viewer looking at the terminal:

* Third-party chatter is silenced — chromadb posthog errors, httpx request lines,
  transformers/HF advisories, matplotlib font debug. None of it is about the work
  being done, and "ERROR: Failed to send telemetry event" reads as a broken system.
* Pre-repair JSON parse failures stop shouting. They are logged before the repair
  pass runs and the repair almost always succeeds, so an ERROR line there is
  actively misleading. A genuine unrecoverable failure still surfaces.
* The moments that tell the story get formatted: the planner's decomposition,
  section start/finish with timings, chart renders, final assembly.

Set VERBOSE=1 (or RAG_VERBOSE=1) for full standard logging when debugging.
"""

from __future__ import annotations

import logging
import os
import sys
import warnings
from typing import Any, Dict, Iterable, Optional

# Loggers that produce noise rather than signal during a demo.
_NOISY_LOGGERS = (
    "chromadb",
    "chromadb.telemetry",
    "chromadb.telemetry.product.posthog",
    "chromadb.segment",
    "httpx",
    "httpcore",
    "urllib3",
    "transformers",
    "sentence_transformers",
    "matplotlib",
    "matplotlib.font_manager",
    "PIL",
    "oci",
    "circuitbreaker",
    "asyncio",
    "langchain",
    "langchain_core",
    "openai",
    "filelock",
    "fsspec",
    "numexpr",
)

# Substrings that mark a line as internal plumbing rather than pipeline progress.
_SUPPRESSED_SUBSTRINGS = (
    "Failed to send telemetry",
    "capture() takes",
    "Telemetry disabled",
    "None of PyTorch, TensorFlow",
    "🔧 JSON parsing failed",
    "🔧 Error position",
    "🔧 Error context",
    "🔧 Attempting ultimate fallback",
    "🔧 Cleaned JSON",
    "🔧 Starting universal JSON cleanup",
    "🔧 JSON parsing successful",
    "Delete of nonexisting embedding ID",
    "Tokenizer initialized",
    "No tokenizer provided",
    # Internal wiring and startup — true, but not the story being told.
    "Ultimate fallback repair successful",
    "RAGSystem init",
    "self.llm assigned",
    "Agents initialized",
    "known_tags loaded",
    "Processing query with",
    "Starting report generation",
    "Using provided entities",
    "[Planner] Using provided entities",
    "[Planner] Extracted",
    "Processing section ",
    "Processing 3 retrieval",
    "retrieval sections in parallel",
    "Loading ",
    "token count:",
)

# Long single-line messages (retrieval steps carry the full criteria list verbatim)
# are truncated rather than dropped — the line is informative, its tail is not.
_MAX_LINE = 150


def _verbose_requested() -> bool:
    return os.environ.get("VERBOSE", "").lower() in ("1", "true", "yes") or \
        os.environ.get("RAG_VERBOSE", "").lower() in ("1", "true", "yes")


class _DemoFilter(logging.Filter):
    """Drop plumbing lines. Never drops anything at ERROR that is genuinely fatal."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:
            return True

        for needle in _SUPPRESSED_SUBSTRINGS:
            if needle in message:
                return False
        return True


class _DemoFormatter(logging.Formatter):
    """Terse, aligned output. No logger names, no module paths, no date."""

    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()

        # Pre-formatted presentation lines pass through untouched.
        if getattr(record, "demo_raw", False):
            return message

        if len(message) > _MAX_LINE:
            message = message[:_MAX_LINE].rstrip() + "…"

        if record.levelno >= logging.ERROR:
            prefix = "  ✖ "
        elif record.levelno >= logging.WARNING:
            prefix = "  ! "
        else:
            prefix = "    "
        return f"{prefix}{message}"


class DemoLogger(logging.Logger):
    """Logger with presentation helpers used by the ingest and report pipelines."""

    def _raw(self, text: str) -> None:
        self.info(text, extra={"demo_raw": True})

    def stage_header(self, title: str, subtitle: str = "") -> None:
        """A major pipeline stage — the visual anchor points in a live demo."""
        self._raw("")
        self._raw(f"┌─ {title.upper()}")
        if subtitle:
            self._raw(f"│  {subtitle}")
        self._raw("└" + "─" * (len(title) + 3))

    def plan(self, sections: Iterable[Dict[str, Any]], entities: Optional[Iterable[str]] = None) -> None:
        """
        Render the planner's decomposition.

        This is the single most demo-relevant output in the pipeline — it is the
        visible proof that the task was decomposed rather than answered in one shot —
        and it was previously not printed at all.
        """
        sections = list(sections)
        self._raw("")
        self._raw("┌─ TASK DECOMPOSITION")
        if entities:
            self._raw(f"│  entities: {', '.join(entities)}")
        self._raw(f"│  {len(sections)} sections planned")
        self._raw("│")
        for i, section in enumerate(sections, start=1):
            topic = section.get("topic", "?")
            role = section.get("role", "?")
            self._raw(f"│  {i}. {topic}  [{role}]")
            criteria = (section.get("criteria") or "").strip()
            if criteria:
                shown = criteria if len(criteria) <= 88 else criteria[:85] + "…"
                self._raw(f"│       criteria: {shown}")
        self._raw("└" + "─" * 20)

    def section_done(self, topic: str, chunks: int, findings: int, seconds: float | None = None) -> None:
        timing = f"  ({seconds:.1f}s)" if seconds is not None else ""
        self._raw(f"    ✓ {topic}  ·  {chunks} chunks  ·  {findings} findings{timing}")

    def chunk_comparison(self, original: str, rewritten: str, metadata: Dict[str, Any] | None = None) -> None:
        """Before/after for a rewritten chunk. Verbose-only: too long for a demo."""
        if not _verbose_requested():
            return
        sheet = (metadata or {}).get("sheet", "?")
        self._raw(f"    ── chunk [{sheet}]")
        self._raw(f"       before: {original[:160].strip()}…")
        self._raw(f"       after:  {rewritten[:160].strip()}…")


def setup_demo_logging(force_verbose: bool | None = None) -> DemoLogger:
    """
    Install demo logging and return the shared logger.

    Idempotent: repeated calls (each module does this at import) reconfigure rather
    than stacking handlers, which would otherwise duplicate every line.
    """
    verbose = _verbose_requested() if force_verbose is None else force_verbose

    logging.setLoggerClass(DemoLogger)
    logger = logging.getLogger("rag.demo")

    # Replace handlers rather than appending — avoids duplicate output.
    for existing in list(logger.handlers):
        logger.removeHandler(existing)

    handler = logging.StreamHandler(sys.stdout)
    if verbose:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
        )
    else:
        handler.setFormatter(_DemoFormatter())
        handler.addFilter(_DemoFilter())

    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    logger.propagate = False

    # Startup chatter from our own modules — embedding-model registration, collection
    # discovery, agent wiring. Useful when debugging, meaningless to an audience, and
    # it runs to ~40 lines before any actual work begins.
    if not verbose:
        warnings.filterwarnings("ignore", category=UserWarning)
        warnings.filterwarnings("ignore", category=DeprecationWarning)

    # The root logger also reaches the console via basicConfig elsewhere; quiet it
    # down so third-party libraries do not bypass the filtering above.
    root = logging.getLogger()
    for existing in list(root.handlers):
        root.removeHandler(existing)
    root_handler = logging.StreamHandler(sys.stdout)
    if verbose:
        root_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s", datefmt="%H:%M:%S")
        )
    else:
        root_handler.setFormatter(_DemoFormatter())
        root_handler.addFilter(_DemoFilter())
    root.addHandler(root_handler)
    # WARNING, not INFO: every module that does logging.getLogger(__name__) reaches
    # the console through root. At INFO that is ~40 lines of embedding-model
    # registration and collection discovery before any work starts. Narrative output
    # goes through the 'rag.demo' logger above, which stays at INFO.
    root.setLevel(logging.DEBUG if verbose else logging.WARNING)

    if not verbose:
        for name in _NOISY_LOGGERS:
            noisy = logging.getLogger(name)
            noisy.setLevel(logging.CRITICAL)
            noisy.propagate = False
            # A NullHandler is required, not optional: with propagate=False and no
            # handler at all, logging falls back to its lastResort handler and the
            # record still reaches stderr — which is how the chromadb telemetry
            # errors kept appearing despite being silenced.
            if not any(isinstance(h, logging.NullHandler) for h in noisy.handlers):
                noisy.addHandler(logging.NullHandler())

    return logger  # type: ignore[return-value]


# Module-level logger, imported directly by the pipeline.
demo_logger: DemoLogger = setup_demo_logging()
