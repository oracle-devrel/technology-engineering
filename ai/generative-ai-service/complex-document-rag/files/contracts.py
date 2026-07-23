"""
Strict Pydantic contracts for inter-agent communication.

All agent-to-agent data must flow through these models.
Legacy dict conversion helpers are provided at the boundary.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

EntityId = str
CollectionName = Literal["xlsx", "pdf", "multi"]


# ---------------------------------------------------------------------------
# Chunk — unit of retrieved context
# ---------------------------------------------------------------------------

class Chunk(BaseModel):
    """A single retrieved text chunk with metadata."""

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    search_entity: Optional[str] = None
    score: Optional[float] = None

    # -- conversion helpers --------------------------------------------------

    @classmethod
    def from_legacy_dict(cls, d: dict) -> "Chunk":
        """Convert a legacy chunk dict (from vector store / ResearchAgent) into a Chunk."""
        return cls(
            content=d.get("content", ""),
            metadata=d.get("metadata", {}),
            search_entity=d.get("_search_entity"),
            score=d.get("_entity_score"),
        )

    def to_legacy_dict(self) -> dict:
        """Convert back to a legacy dict for backward-compatible code paths."""
        d: dict = {
            "content": self.content,
            "metadata": self.metadata,
        }
        if self.search_entity is not None:
            d["_search_entity"] = self.search_entity
        if self.score is not None:
            d["_entity_score"] = self.score
        return d

    def content_hash(self) -> str:
        """Deterministic hash of the content for deduplication."""
        return hashlib.sha256(self.content.strip().encode()).hexdigest()


# ---------------------------------------------------------------------------
# PlanSection — one topic in the report plan
# ---------------------------------------------------------------------------

class PlanSection(BaseModel):
    """A single section in the report plan."""

    topic: str
    entity_steps: Dict[EntityId, str] = Field(
        default_factory=dict,
        description="Mapping entity -> retrieval instruction",
    )
    order: int = 0
    role: str = Field(
        default="compare",
        description=(
            "How this section is written. 'compare' retrieves source data and builds a "
            "metrics comparison. 'synthesize' and 'recommend' read the already-written "
            "compare sections instead, so they must run after them."
        ),
    )

    # -- conversion helpers --------------------------------------------------

    @classmethod
    def from_legacy_dict(cls, d: dict, order: int = 0, entities: Optional[List[str]] = None) -> "PlanSection":
        """Convert a legacy plan dict {'topic': ..., 'steps': [...]} into a PlanSection."""
        topic = d.get("topic", "Untitled")
        steps = d.get("steps", [])

        entity_steps: Dict[EntityId, str] = {}
        if entities and len(steps) == len(entities):
            for ent, step in zip(entities, steps):
                entity_steps[ent] = step
        elif entities and len(steps) == 1:
            entity_steps[entities[0]] = steps[0]
        else:
            # Fallback: number the steps
            for i, step in enumerate(steps):
                key = entities[i] if entities and i < len(entities) else f"entity_{i}"
                entity_steps[key] = step

        role = str(d.get("role", "compare")).strip().lower()
        if role not in ("compare", "synthesize", "recommend"):
            role = "compare"

        return cls(topic=topic, entity_steps=entity_steps, order=order, role=role)

    def to_legacy_dict(self) -> dict:
        """Convert back to the legacy {'topic': ..., 'steps': [...]} format."""
        return {
            "topic": self.topic,
            "steps": list(self.entity_steps.values()),
        }


# ---------------------------------------------------------------------------
# Plan — output of the planner
# ---------------------------------------------------------------------------

class Plan(BaseModel):
    """Full report plan produced by the PlannerAgent."""

    sections: List[PlanSection]
    entities: List[EntityId]
    is_comparison: bool = False
    raw_topics: Optional[List[str]] = None  # debug: topics before step construction

    # -- conversion helpers --------------------------------------------------

    @classmethod
    def from_legacy_tuple(
        cls,
        plan_list: List[dict],
        entities: List[str],
        is_comparison: bool,
    ) -> "Plan":
        """Convert the legacy (list[dict], list[str], bool) planner output."""
        sections = [
            PlanSection.from_legacy_dict(d, order=i, entities=entities)
            for i, d in enumerate(plan_list)
        ]
        return cls(
            sections=sections,
            entities=entities,
            is_comparison=is_comparison,
        )

    def to_legacy_tuple(self) -> tuple:
        """Return (list[dict], list[str], bool) for backward-compatible callers."""
        plan_list = [s.to_legacy_dict() for s in self.sections]
        return plan_list, list(self.entities), self.is_comparison


# ---------------------------------------------------------------------------
# SectionDraft — output of section writer
# ---------------------------------------------------------------------------

class SectionDraft(BaseModel):
    """A written section ready for report assembly."""

    topic: str
    markdown: str = ""
    table: List[Dict[str, Any]] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    chart_data: Dict[str, Any] = Field(default_factory=dict)
    entities: List[EntityId] = Field(default_factory=list)
    is_comparison: bool = False
    chunks_used: int = 0
    sources: List[Dict[str, Any]] = Field(default_factory=list)

    # -- conversion helpers --------------------------------------------------

    @classmethod
    def from_legacy_dict(cls, d: dict) -> "SectionDraft":
        """Convert a legacy section dict from SectionWriterAgent."""
        table = d.get("table", [])
        if isinstance(table, dict):
            table = [table]
        elif not isinstance(table, list):
            table = []

        chart_data = d.get("chart_data", {})
        if not isinstance(chart_data, dict):
            chart_data = {}

        findings = d.get("findings", [])
        if isinstance(findings, str):
            findings = [findings]
        elif not isinstance(findings, list):
            findings = []
        findings = [str(f).strip() for f in findings if str(f).strip()]

        sources = d.get("sources", [])
        if not isinstance(sources, list):
            sources = []

        return cls(
            topic=d.get("heading", d.get("topic", "Untitled")),
            markdown=d.get("text", ""),
            table=table,
            findings=findings,
            chart_data=chart_data,
            entities=d.get("entities", []),
            is_comparison=d.get("is_comparison", False),
            chunks_used=d.get("chunks_used", 0),
            sources=sources,
        )

    def to_legacy_dict(self) -> dict:
        """Convert back to the legacy section dict format."""
        return {
            "heading": self.topic,
            "text": self.markdown,
            "table": self.table,
            "findings": self.findings,
            "chart_data": self.chart_data,
            "entities": self.entities,
            "is_comparison": self.is_comparison,
            "chunks_used": self.chunks_used,
            "sources": self.sources,
        }


# ---------------------------------------------------------------------------
# ReportResult — output of report writer
# ---------------------------------------------------------------------------

class ReportResult(BaseModel):
    """Final output of the ReportWriterAgent."""

    report_path: str
    sections: List[SectionDraft] = Field(default_factory=list)
    total_chunks_used: int = 0
    sources: Dict[str, Any] = Field(default_factory=dict)
