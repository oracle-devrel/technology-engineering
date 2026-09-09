"""Pydantic models for the compliance audit output."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Finding(BaseModel):
    timestamp: str
    sop_clause: str
    status: Literal["compliant", "violation", "partial"]
    severity: Optional[Literal["critical", "major", "minor"]] = None
    description: str
    evidence: str


class AuditReport(BaseModel):
    overall_compliance: Literal["pass", "fail", "conditional"]
    summary: str
    findings: list[Finding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)