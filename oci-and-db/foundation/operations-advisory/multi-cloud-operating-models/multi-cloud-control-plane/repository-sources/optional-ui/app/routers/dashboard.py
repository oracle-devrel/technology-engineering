"""Dashboard HTMX partials."""
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.auth import ProjectSelected, require_github_client
from app.helpers import render_partial, render_repository_state_error
from app.services.dashboard_service import DashboardService
from app.services.git_service import GitService, RepositoryStateError
from app.services.project_service import ProjectService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_github_client)])


def _build_cloud_region_summary(inventory: dict) -> list[dict]:
    """Build a compact provider/region summary from inventory data."""
    resource_counts: dict[tuple[str, str], int] = {}
    for resource in inventory.get("resources", []):
        key = (resource.get("cloud", ""), resource.get("region", ""))
        resource_counts[key] = resource_counts.get(key, 0) + 1

    summary = []
    for cloud in sorted(inventory.get("clouds", []), key=lambda item: item.get("name", "")):
        cloud_name = cloud.get("name", "")
        regions = []
        for region in sorted(cloud.get("regions", []), key=lambda item: item.get("name", "")):
            region_name = region.get("name", "")
            regions.append(
                {
                    "name": region_name,
                    "resource_count": resource_counts.get((cloud_name, region_name), 0),
                }
            )
        summary.append(
            {
                "name": cloud_name,
                "regions": regions,
                "resource_count": sum(region["resource_count"] for region in regions),
            }
        )
    return summary


@router.get("/overview", response_class=HTMLResponse)
async def overview_partial(request: Request) -> HTMLResponse:
    """Global overview — all projects."""
    try:
        github_client = request.state.github_client
        projects = await ProjectService(github_client=github_client).list_projects()
    except Exception as e:
        logger.error(f"Error loading overview: {e}", exc_info=True)
        projects = []

    return render_partial("partials/overview.html", request, projects=projects)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_partial(
    request: Request,
    project: ProjectSelected,
) -> HTMLResponse:
    """Dashboard overview partial."""
    load_error = ""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        dashboard = DashboardService(git)
        stats = await dashboard.get_dashboard_stats(strict=True)
        pending_prs = await dashboard.get_pending_prs()
        deployments = await dashboard.get_recent_deployments()
    except RepositoryStateError as e:
        logger.error("Unable to verify dashboard state for %s: %s", project, e, exc_info=True)
        return render_repository_state_error(request)
    except Exception as e:
        logger.error(f"Error loading dashboard for {project}: {e}", exc_info=True)
        stats = {}
        pending_prs = []
        deployments = []
        load_error = "dashboard"

    return render_partial(
        "partials/dashboard.html",
        request,
        project=project,
        stats=stats,
        pending_prs=pending_prs,
        deployments=deployments,
        load_error=load_error,
    )


@router.get("/cloud-regions", response_class=HTMLResponse)
async def cloud_regions_partial(
    request: Request,
    project: ProjectSelected,
) -> HTMLResponse:
    """Cloud and region summary partial."""
    load_error = ""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        dashboard = DashboardService(git)
        inventory = await dashboard.get_resource_inventory(strict=True)
        cloud_regions = _build_cloud_region_summary(inventory)
    except RepositoryStateError as e:
        logger.error("Unable to verify cloud regions for %s: %s", project, e, exc_info=True)
        return render_repository_state_error(request)
    except Exception as e:
        logger.error(f"Error loading cloud regions for {project}: {e}", exc_info=True)
        cloud_regions = []
        load_error = "cloud and region summary"

    return render_partial(
        "partials/cloud-regions.html",
        request,
        project=project,
        cloud_regions=cloud_regions,
        load_error=load_error,
    )


@router.get("/tree", response_class=HTMLResponse)
async def tree_partial(
    request: Request,
    project: ProjectSelected,
) -> HTMLResponse:
    """Repository tree structure partial."""
    load_error = ""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        structure = await git.get_repository_structure(strict=True)
    except RepositoryStateError as e:
        logger.error("Unable to verify tree for %s: %s", project, e, exc_info=True)
        return render_repository_state_error(request)
    except Exception as e:
        logger.error(f"Error loading tree for {project}: {e}", exc_info=True)
        structure = {}
        load_error = "structure"

    return render_partial(
        "partials/tree.html",
        request,
        project=project,
        structure=structure,
        load_error=load_error,
    )
