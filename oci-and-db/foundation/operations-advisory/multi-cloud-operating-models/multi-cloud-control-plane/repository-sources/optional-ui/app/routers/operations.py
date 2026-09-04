"""Operations HTMX partials - Day-2 operations management."""
import logging
from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from app.auth import (
    GuardResponseException,
    ProjectOptional,
    ProjectSelected,
    ensure_project_write_access,
    require_github_client,
)
from app.config import settings
from app.forms import (
    htmx_error_context,
    request_form_payload,
    validation_messages,
)
from app.helpers import render_partial, render_repository_state_error
from app.path_validation import validate_path_segment
from app.services.dashboard_service import DashboardService
from app.services.installation_service import load_mccp_installation
from app.services.git_service import GitService, RepositoryStateError
from app.services.operations_service import OperationsService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_github_client)])

_CLOUD_ORDER = {"oci": 0, "azure": 1, "gcp": 2}


def _cloud_sort_key(cloud: str) -> tuple[int, str]:
    return (_CLOUD_ORDER.get(cloud, 99), cloud)


def _validate_operation_scope(cloud: str, environment: str) -> None:
    """Keep the MVP Day 2 surface to OCI across supported environments."""
    if cloud != "oci" or environment not in {"dev", "test", "uat", "prod"}:
        raise ValueError("Day 2 operations are not available for this cloud or environment")


def _environment_options(project: str) -> list[str]:
    """Return the V2 environments permitted by the selected project layout."""
    installation = load_mccp_installation(settings.mccp_installation_path)
    if project.startswith("prod-"):
        return [installation.project_context(project, "prod").environment]
    return sorted(installation.nonprod_environments)

RequiredText = Annotated[str, StringConstraints(min_length=1)]
OptionalText = str


class ExecuteOperationForm(BaseModel):
    """Validated base fields for execute-operation submissions."""
    model_config = ConfigDict(str_strip_whitespace=True)

    project: RequiredText
    operation: RequiredText
    cloud: RequiredText = settings.default_cloud
    environment: RequiredText = "dev"
    region: RequiredText = settings.default_region
    change_reference: OptionalText = ""


_REQUIRED_LABELS = {"project": "Project", "operation": "Operation"}


@router.get("/operations", response_class=HTMLResponse)
async def operations_partial(
    request: Request,
    project: ProjectOptional,
    environment: str = Query("dev"),
) -> HTMLResponse:
    """List available operations from catalog."""
    load_error = ""
    try:
        if project:
            environment_options = _environment_options(project)
            if environment not in environment_options:
                environment = environment_options[0]

        github_client = request.state.github_client
        git = GitService(project or "platform-ci", github_client=github_client)
        catalog = await git.get_operations_catalog()
        operations_by_cloud = {}
        for operation in catalog.operations:
            if operation.cloud != "oci":
                continue
            operations_by_cloud.setdefault(operation.cloud, []).append(operation)
        operations_by_cloud = {
            cloud: sorted(operations, key=lambda item: item.name or item.operation_type or item.id)
            for cloud, operations in sorted(
                operations_by_cloud.items(),
                key=lambda item: _cloud_sort_key(item[0]),
            )
        }
    except Exception as exc:
        logger.error("Error loading operations catalog: %s", exc, exc_info=True)
        operations_by_cloud = {}
        load_error = "operations"

    return render_partial(
        "partials/operations.html",
        request,
        project=project,
        environment=environment,
        environment_options=_environment_options(project) if project else ["dev", "test", "uat"],
        operations_by_cloud=operations_by_cloud,
        load_error=load_error,
    )


@router.get("/operation-form", response_class=HTMLResponse)
async def operation_form_partial(
    request: Request,
    op: str,
    project: ProjectSelected,
    cloud: str = Query(None),
    environment: str = Query("dev"),
    region: str = Query(None),
) -> HTMLResponse:
    """Show form for a specific operation."""
    try:
        if environment not in _environment_options(project):
            raise ValueError("Selected environment is not allowed for this project repository")
        github_client = request.state.github_client
        git_service = GitService(project, github_client=github_client)
        catalog = await git_service.get_operations_catalog(cloud_filter=cloud)

        operation_def = OperationsService.find_operation(catalog, op)
        if not operation_def:
            return render_partial(
                "partials/state-error.html",
                request,
                title="Operation not found",
                message=f"Operation '{op}' was not found in the catalog.",
            )

        parameters = OperationsService.build_parameters(operation_def)
        operation_cloud = operation_def.cloud or cloud or settings.default_cloud
        _validate_operation_scope(operation_cloud, environment)
        selected_region = region or settings.default_region_for_cloud(operation_cloud)
        region_options = settings.region_options_for_cloud(operation_cloud)
        can_execute = True
        if OperationsService.needs_inventory(parameters):
            dashboard = DashboardService(git_service)
            inventory = await dashboard.get_resource_inventory(strict=True)
            inventory_resources = inventory.get("resources", [])
            region_options = OperationsService.available_regions(
                parameters,
                inventory_resources,
                cloud=operation_cloud,
                environment=environment,
            )
            if selected_region not in region_options:
                selected_region = region_options[0] if region_options else selected_region
            parameters = OperationsService.attach_inventory(
                parameters,
                inventory_resources,
                cloud=operation_cloud,
                environment=environment,
                region=selected_region,
            )
            required_resources = [
                param
                for param in parameters.values()
                if param.type == "resource" and param.required
            ]
            can_execute = bool(region_options) and all(
                param.resources for param in required_resources
            )
        elif selected_region not in region_options:
            region_options = [selected_region, *region_options]

        return render_partial(
            "partials/operation-form.html",
            request,
            operation=operation_def,
            parameters=parameters,
            project=project,
            cloud=operation_cloud,
            environment=environment,
            region=selected_region,
            region_options=region_options,
            can_execute=can_execute,
        )

    except RepositoryStateError as exc:
        logger.error("Unable to verify operation inventory for %s: %s", op, exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error building form for %s: %s", op, exc, exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading operation form",
            message=str(exc),
        )


@router.post("/execute-operation", response_class=HTMLResponse)
async def execute_operation_htmx(
    request: Request,
) -> HTMLResponse:
    """Execute Day-2 operation - creates PR via GitOps."""
    payload = await request_form_payload(
        request,
        defaults={
            "cloud": settings.default_cloud,
            "environment": "dev",
            "region": settings.default_region,
        },
    )

    try:
        form = ExecuteOperationForm.model_validate(payload)
    except ValidationError as exc:
        error = "; ".join(validation_messages(exc, required_labels=_REQUIRED_LABELS))
        return render_partial(
            "partials/operation-result.html",
            request,
            **htmx_error_context(escape(error), project=""),
        )

    try:
        await ensure_project_write_access(request, form.project)
        if form.environment not in _environment_options(form.project):
            raise ValueError("Selected environment is not allowed for this project repository")
        validate_path_segment(form.cloud, "cloud")
        validate_path_segment(form.environment, "environment")
        validate_path_segment(form.region, "region")
        validate_path_segment(form.operation, "operation")
        _validate_operation_scope(form.cloud, form.environment)

        github_client = request.state.github_client
        git_service = GitService(form.project, github_client=github_client)
        catalog = await git_service.get_operations_catalog(cloud_filter=form.cloud)

        operation_def = OperationsService.find_operation(catalog, form.operation)
        if not operation_def:
            raise ValueError(f"Operation {form.operation} not found")

        parameters = OperationsService.build_parameters(operation_def)
        inventory_resources = None
        if OperationsService.needs_inventory(parameters):
            inventory = await DashboardService(git_service).get_resource_inventory(strict=True)
            inventory_resources = inventory.get("resources", [])

        payload, missing_parameters = OperationsService.validate_execution_payload(
            operation_def,
            payload,
            inventory_resources=inventory_resources,
            cloud=form.cloud,
            environment=form.environment,
            region=form.region,
        )
        if missing_parameters:
            missing = ", ".join(missing_parameters)
            return render_partial(
                "partials/operation-result.html",
                request,
                **htmx_error_context(escape(f"Missing values: {missing}"), project=form.project),
            )

        final_manifest = OperationsService.build_execution_manifest(operation_def, payload)

        action = payload.get("action") or payload.get("start_or_stop") or "execute"
        target_name = next(
            (value for key, value in payload.items() if "name" in key or "target" in key),
            "target",
        )
        base_msg = f"Operation: {form.operation} - {action} on {target_name}"
        commit_message = f"[{form.change_reference}] {base_msg}" if form.change_reference else base_msg

        result = await git_service.write_manifest(
            cloud=form.cloud,
            environment=form.environment,
            region=form.region,
            resource_path=f"lifecycle_operations/{form.operation}.json",
            data=final_manifest,
            commit_message=commit_message,
        )

        return render_partial(
            "partials/operation-result.html",
            request,
            success=True,
            pr_number=result.get("pr_number", "N/A"),
            pr_url=result.get("pr_url", "#"),
            operation=form.operation,
            project=form.project,
        )

    except GuardResponseException:
        raise
    except RepositoryStateError as exc:
        logger.error("Unable to verify operation target state: %s", exc, exc_info=True)
        return render_repository_state_error(request)
    except Exception as exc:
        logger.error("Error executing operation: %s", exc, exc_info=True)
        return render_partial(
            "partials/operation-result.html",
            request,
            **htmx_error_context(escape(str(exc)), project=form.project),
        )
