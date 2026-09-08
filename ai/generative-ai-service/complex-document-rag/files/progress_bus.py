"""
Thread-safe progress bus for long-running pipeline work.

The report pipeline runs for minutes inside a single blocking call, so the UI had
nothing to show but a bar that jumped to 70% and froze. Rather than thread a callback
through every agent signature, the pipeline publishes coarse milestones here and the
UI polls them from its own thread.

Publishing is best-effort and must never break a run: a UI concern should not be able
to fail report generation. All publish helpers swallow their own errors.

    from progress_bus import progress_bus

    progress_bus.start(total_steps=12)
    progress_bus.publish("Planning report sections", step=1)
    progress_bus.publish_chart("/path/to/chart.png")
    snapshot = progress_bus.snapshot()   # from the UI thread
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ProgressSnapshot:
    """Immutable view of the bus, safe to read off-thread."""

    running: bool = False
    message: str = ""
    step: int = 0
    total_steps: int = 0
    elapsed: float = 0.0
    events: List[str] = field(default_factory=list)
    charts: List[str] = field(default_factory=list)

    @property
    def fraction(self) -> float:
        """Completion in [0, 1). Never returns 1.0 — the caller owns 'done'."""
        if self.total_steps <= 0:
            return 0.0
        return min(self.step / self.total_steps, 0.99)


class ProgressBus:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._message = ""
        self._step = 0
        self._total_steps = 0
        self._started_at = 0.0
        self._events: List[str] = []
        self._charts: List[str] = []

    def start(self, total_steps: int = 0, message: str = "Starting…") -> None:
        with self._lock:
            self._running = True
            self._message = message
            self._step = 0
            self._total_steps = total_steps
            self._started_at = time.time()
            self._events = [message] if message else []
            self._charts = []

    def set_total(self, total_steps: int) -> None:
        """Set the denominator once the planner reveals how many sections there are."""
        with self._lock:
            self._total_steps = total_steps

    def publish(self, message: str, step: Optional[int] = None, advance: bool = False) -> None:
        try:
            with self._lock:
                if not self._running:
                    return
                if step is not None:
                    self._step = step
                elif advance:
                    self._step += 1
                self._message = message
                self._events.append(message)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug(f"progress_bus.publish failed (ignored): {e}")

    def publish_chart(self, path: str) -> None:
        try:
            with self._lock:
                if self._running and path and path not in self._charts:
                    self._charts.append(path)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug(f"progress_bus.publish_chart failed (ignored): {e}")

    def finish(self, message: str = "Complete") -> None:
        with self._lock:
            self._running = False
            self._message = message
            if self._total_steps:
                self._step = self._total_steps

    def snapshot(self) -> ProgressSnapshot:
        with self._lock:
            return ProgressSnapshot(
                running=self._running,
                message=self._message,
                step=self._step,
                total_steps=self._total_steps,
                elapsed=time.time() - self._started_at if self._started_at else 0.0,
                events=list(self._events),
                charts=list(self._charts),
            )


progress_bus = ProgressBus()
