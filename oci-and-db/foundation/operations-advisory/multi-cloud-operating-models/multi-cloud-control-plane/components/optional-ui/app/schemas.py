"""Shared Pydantic schemas for application service contracts."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class OperationParameter(BaseModel):
    """Form parameter definition for a Day-2 operation."""

    model_config = ConfigDict(extra="allow")

    label: str = ""
    type: str = "string"
    required: bool = True
    default: Any = None
    options: list[Any] = Field(default_factory=list)
    resource_type: str = ""
    resources: list[dict[str, Any]] = Field(default_factory=list)


class OperationCatalogEntry(BaseModel):
    """Validated operation catalog entry loaded from gitops-templates."""

    model_config = ConfigDict(extra="allow")

    id: str
    cloud: str
    operation_type: str = ""
    name: str = ""
    description: str = ""
    parameters: dict[str, OperationParameter] = Field(default_factory=dict)
    workflow: str = ""
    auto_approve: bool | None = None
    wait_for_completion: bool | None = None


class OperationsCatalog(BaseModel):
    """Typed response for operations catalog lookups."""

    operations: list[OperationCatalogEntry] = Field(default_factory=list)
