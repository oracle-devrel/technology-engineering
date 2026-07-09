"""Core types shared across the KQL→Logan QL subpackage.

Phase 6 introduces a tiered classification (D-16) for every converted stage
and a frozen-dataclass context (D-08) threaded through the pipeline so
operators stay pure functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class Tier(IntEnum):
    """Conversion fidelity classification for a KQL expression.

    IntEnum so severity aggregates via ``max(...)`` per D-16.

    - TIER_1 — lossless: KQL converts to semantically equivalent Logan QL.
    - TIER_2 — transform with documented rewrite (e.g. operator rename).
    - TIER_3 — unsupported in OCI Log Analytics; converter SKIPS with
      structured reason.
    """

    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


@dataclass(frozen=True)
class ConversionContext:
    """Immutable per-conversion state threaded between pipeline stages (D-08)."""

    mapping: dict
    allowed_aliases: frozenset[str] = field(default_factory=frozenset)
    dictionary_fields: frozenset[str] = field(default_factory=frozenset)
    log_source_tables: tuple[str, ...] = ()


@dataclass(frozen=True)
class StageResult:
    """Per-operator output (D-06).

    fragments    — Logan QL stage strings emitted by the operator.
    tier         — fidelity classification for this stage.
    skip_reasons — non-empty when the operator could not convert.
    new_aliases  — column aliases introduced for downstream stages.
    """

    fragments: tuple[str, ...] = ()
    tier: Tier = Tier.TIER_1
    skip_reasons: tuple[str, ...] = ()
    new_aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class KqlStage:
    """Parsed top-level KQL stage prior to operator dispatch."""

    kind: str
    body: str


@dataclass(frozen=True)
class KqlPredicate:
    """Parsed KQL predicate text. Phase 6 keeps the shape minimal per D-06."""

    text: str


__all__ = [
    "Tier",
    "ConversionContext",
    "StageResult",
    "KqlStage",
    "KqlPredicate",
]
