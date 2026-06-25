"""KQL-side AST scaffolding.

Phase 6 keeps this minimal — only the nodes operator signatures need.
Logan-side AST is intentionally deferred (D-06): operators return string
fragments, not AST nodes.
"""

from __future__ import annotations

from .types import KqlPredicate, KqlStage

__all__ = ["KqlStage", "KqlPredicate"]
