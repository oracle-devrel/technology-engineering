"""Logan QL fragment emitter helpers."""

from __future__ import annotations

from typing import Iterable


def format_stage(fragments: Iterable[str]) -> str:
    """Join stage fragments with the canonical Logan QL pipe separator."""

    return " | ".join(f for f in fragments if f)


__all__ = ["format_stage"]
