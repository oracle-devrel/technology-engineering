"""Shared operations logic for matching and dynamic form parameters."""
from __future__ import annotations

from typing import Any

from rapidfuzz import fuzz, process, utils

from app.helpers import fill_template_with_missing, find_placeholders, find_raw_placeholders
from app.schemas import OperationCatalogEntry, OperationParameter, OperationsCatalog

_OPERATION_METADATA_KEYS = {
    "name",
    "description",
    "parameters",
    "workflow",
    "auto_approve",
    "cloud",
    "id",
    "wait_for_completion",
}


class OperationsService:
    """Reusable operation matching and parameter-enrichment helpers."""

    @staticmethod
    def _template_payload(operation_def: OperationCatalogEntry) -> dict[str, Any]:
        return operation_def.model_dump(exclude_none=True)

    @staticmethod
    def match_operations(
        resource_type: str,
        cloud: str,
        operations: list[OperationCatalogEntry],
    ) -> list[OperationCatalogEntry]:
        """Return relevant Day-2 operations for a resource."""
        query = (resource_type or "").strip()
        if not query:
            return []

        cloud_ops = [op for op in operations if op.cloud.lower() == (cloud or "").lower()]
        if not cloud_ops:
            return []

        choices = {
            idx: " ".join(
                [
                    op.id,
                    op.name,
                    op.operation_type,
                    op.description,
                ]
            )
            for idx, op in enumerate(cloud_ops)
        }
        matches = process.extract(
            query,
            choices,
            scorer=fuzz.WRatio,
            processor=utils.default_process,
            score_cutoff=45.0,
            limit=4,
        )
        return [cloud_ops[idx] for _, _, idx in matches]

    @classmethod
    def attach_matches(
        cls,
        resources: list[dict[str, Any]],
        operations: list[OperationCatalogEntry],
    ) -> list[dict[str, Any]]:
        """Annotate each resource with matched operations in-place and return it."""
        for resource in resources:
            resource["ops"] = cls.match_operations(
                resource.get("type", ""),
                resource.get("cloud", ""),
                operations,
            )
        return resources

    @staticmethod
    def find_operation(catalog: OperationsCatalog, operation_id: str) -> OperationCatalogEntry | None:
        """Find operation by id from a loaded catalog payload."""
        return next(
            (item for item in catalog.operations if item.id == operation_id),
            None,
        )

    @classmethod
    def build_parameters(cls, operation_def: OperationCatalogEntry) -> dict[str, OperationParameter]:
        """Build operation parameters, autodiscovering placeholders when needed."""
        existing = operation_def.parameters
        parameters = dict(existing)

        for placeholder in find_placeholders(cls._template_payload(operation_def)):
            if placeholder in parameters:
                continue
            param_config = OperationParameter(
                label=placeholder.replace("_", " ").title(),
                type="string",
                required=True,
            )
            if any(key in placeholder for key in ("adb", "database", "db")):
                param_config = OperationParameter(
                    label=param_config.label,
                    type="resource",
                    resource_type="database",
                    required=True,
                )
            elif "start_or_stop" in placeholder:
                param_config = OperationParameter(
                    label="Action",
                    type="choice",
                    options=["start", "stop"],
                    required=True,
                )
            parameters[placeholder] = param_config

        return parameters

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value is None or value == ""

    @staticmethod
    def _to_bool(value: Any, param_key: str) -> bool:
        if isinstance(value, bool):
            return value
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
        raise ValueError(f"Invalid boolean value for {param_key}")

    @staticmethod
    def _resource_matches(
        resource: dict[str, Any],
        resource_type: str,
        cloud: str | None,
        environment: str | None,
        region: str | None,
    ) -> bool:
        return (
            (not cloud or resource.get("cloud", "").lower() == cloud.lower())
            and (not environment or resource.get("environment") == environment)
            and (not region or resource.get("region") == region)
            and resource_type.lower() in resource.get("type", "").lower()
        )

    @classmethod
    def validate_execution_payload(
        cls,
        operation_def: OperationCatalogEntry,
        payload: dict[str, Any],
        *,
        inventory_resources: list[dict[str, Any]] | None = None,
        cloud: str | None = None,
        environment: str | None = None,
        region: str | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        """Validate catalog parameters and resource targets for an execution."""
        normalized = dict(payload or {})
        missing: list[str] = []

        for param_key, param_def in cls.build_parameters(operation_def).items():
            value = normalized.get(param_key)
            if param_def.type == "boolean":
                if cls._is_empty(value):
                    if param_def.required:
                        missing.append(param_key)
                    else:
                        normalized[param_key] = False
                else:
                    normalized[param_key] = cls._to_bool(value, param_key)
                continue

            if cls._is_empty(value):
                if param_def.required:
                    missing.append(param_key)
                elif param_def.default is not None:
                    normalized[param_key] = param_def.default
                continue

            if param_def.type == "choice" and value not in param_def.options:
                raise ValueError(f"Invalid value for {param_key}")

            if param_def.type == "resource":
                candidates = inventory_resources or []
                if not any(
                    resource.get("name") == value
                    and cls._resource_matches(
                        resource,
                        param_def.resource_type,
                        cloud,
                        environment,
                        region,
                    )
                    for resource in candidates
                ):
                    raise ValueError(f"Invalid resource for {param_key}")

        return normalized, sorted(set(missing))

    @classmethod
    def build_execution_manifest(
        cls,
        operation_def: OperationCatalogEntry,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Build manifest content for execute-operation payloads."""
        template_payload = cls._template_payload(operation_def)
        placeholders = find_raw_placeholders(template_payload)
        manifest, missing = fill_template_with_missing(template_payload, payload, placeholders)
        if missing:
            raise ValueError(f"Missing values: {', '.join(sorted(missing))}")
        if isinstance(manifest, dict):
            final_manifest = {k: v for k, v in manifest.items() if k not in _OPERATION_METADATA_KEYS}
            if final_manifest:
                unresolved = sorted(find_raw_placeholders(final_manifest))
                if unresolved:
                    raise ValueError(f"Unresolved placeholders: {', '.join(unresolved)}")
                return final_manifest
        return {
            k: v
            for k, v in payload.items()
            if k not in {"project", "operation", "cloud", "region"}
        }

    @staticmethod
    def needs_inventory(parameters: dict[str, OperationParameter]) -> bool:
        """Return whether parameters include resource selectors."""
        return any(param.type == "resource" for param in parameters.values())

    @staticmethod
    def attach_inventory(
        parameters: dict[str, OperationParameter],
        inventory_resources: list[dict[str, Any]],
        *,
        cloud: str | None = None,
        environment: str | None = None,
        region: str | None = None,
    ) -> dict[str, OperationParameter]:
        """Attach inventory options to resource-type parameters."""
        for param_def in parameters.values():
            if param_def.type != "resource":
                continue
            resource_type = param_def.resource_type
            param_def.resources = [
                resource
                for resource in inventory_resources
                if OperationsService._resource_matches(
                    resource,
                    resource_type,
                    cloud,
                    environment,
                    region,
                )
            ]
        return parameters

    @staticmethod
    def available_regions(
        parameters: dict[str, OperationParameter],
        inventory_resources: list[dict[str, Any]],
        *,
        cloud: str | None = None,
        environment: str | None = None,
    ) -> list[str]:
        """Return regions satisfying every required resource selector."""
        resource_parameters = [param for param in parameters.values() if param.type == "resource"]
        required_parameters = [param for param in resource_parameters if param.required]
        active_parameters = required_parameters or resource_parameters
        if not active_parameters:
            return []

        region_sets = []
        for param_def in active_parameters:
            region_sets.append(
                {
                    resource.get("region")
                    for resource in inventory_resources
                    if resource.get("region")
                    and OperationsService._resource_matches(
                        resource,
                        param_def.resource_type,
                        cloud,
                        environment,
                        None,
                    )
                }
            )

        available = set.intersection(*region_sets) if region_sets else set()
        return sorted(available)
