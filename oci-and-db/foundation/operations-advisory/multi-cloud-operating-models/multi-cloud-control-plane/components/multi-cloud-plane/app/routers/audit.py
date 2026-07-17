import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse

from app.auth import ProjectRead, ProjectSelected, require_github_client
from app.config import settings
from app.helpers import render_partial
from app.services.git_service import GitService

logger = logging.getLogger(__name__)
router = APIRouter(dependencies=[Depends(require_github_client)])


async def _build_gitops_audit(github_client, project: str, limit: int = 60) -> list[dict[str, Any]]:
    raw_commits = await github_client.get_commits(project, limit=limit)
    workflows = await github_client.get_workflow_runs(project, limit=50)
    workflows_by_sha = {r.get("head_sha"): r for r in workflows if r.get("head_sha")}
    prefixes = tuple(settings.audit_infra_prefixes)

    async def _build_event(commit: dict[str, Any]) -> dict[str, Any] | None:
        sha = commit.get("sha", "")
        if not sha:
            return None

        commit_details = await github_client.get_commit_details(project, sha)
        changed_files = [
            f.get("filename", "")
            for f in commit_details.get("files", [])
            if isinstance(f, dict)
        ]
        if prefixes and not any(path.startswith(prefixes) for path in changed_files):
            return None

        pr = await github_client.get_commit_pr(project, sha)
        pr_number = (pr or {}).get("number")
        approvers: list[str] = []
        pr_details: dict[str, Any] = {}
        if pr_number:
            approvers_task = github_client.get_pr_approvers(project, pr_number)
            pr_details_task = github_client.get_pull_request(project, pr_number)
            approvers, pr_details = await asyncio.gather(approvers_task, pr_details_task)

        run = workflows_by_sha.get(sha, {})
        ci_raw = run.get("conclusion") or run.get("status") or ""
        ci_status = ci_raw.replace("_", " ").title() if ci_raw else ""
        merged_by = (pr_details.get("merged_by") or {}).get("login", "")

        event_date = (
            pr_details.get("merged_at")
            or commit.get("commit", {}).get("author", {}).get("date", "")
        )
        event_date = event_date[:16].replace("T", " ") if event_date else ""

        return {
            "sha": sha,
            "message": (pr or {}).get("title") or commit.get("commit", {}).get("message", ""),
            "author": (
                merged_by
                or (pr or {}).get("user", {}).get("login")
                or commit.get("commit", {}).get("author", {}).get("name", "")
            ),
            "date": event_date,
            "pr_number": pr_number,
            "pr_url": (pr or {}).get("html_url"),
            "approvers": approvers or [],
            "ci_status": ci_status,
            "ci_state": ci_raw,
        }

    built = await asyncio.gather(*[_build_event(c) for c in raw_commits], return_exceptions=True)
    events = []
    for item in built:
        if isinstance(item, dict):
            events.append(item)
        elif isinstance(item, Exception):
            logger.warning("Skipping one audit event due to enrichment error: %s", item)
    return events[:50]


@router.get("/audit", response_class=HTMLResponse)
async def audit_partial(
    request: Request,
    project: ProjectSelected,
) -> HTMLResponse:
    """Show audit log with recent commits or GitOps-filtered events."""
    audit_mode = "gitops"
    load_error = ""
    try:
        github_client = request.state.github_client
        commits = await _build_gitops_audit(github_client, project)
    except Exception as e:
        logger.error(f"Error loading audit log for {project}: {e}", exc_info=True)
        commits = []
        load_error = "audit log"

    return render_partial(
        "partials/audit.html",
        request,
        project=project,
        commits=commits,
        audit_mode=audit_mode,
        load_error=load_error,
        github_org=settings.github_org,
    )


@router.get("/pr-plan", response_class=HTMLResponse)
async def pr_plan_partial(
    request: Request,
    project: ProjectRead,
    pr_number: int = Query(...),
    kind: str = Query("", pattern="^(|terraform|operation|ansible)$"),
) -> HTMLResponse:
    """HTMX partial for PR CI preview."""
    try:
        github_client = request.state.github_client
        git = GitService(project, github_client=github_client)
        plan_data = await git.get_pr_ci_preview(pr_number, expected_kind=kind)

        pr_status = plan_data.get("pr_status", {})
        pr_state = pr_status.get("state", "unknown")
        pr_merged = pr_status.get("merged", False)

        return render_partial(
            "partials/pr-plan.html",
            request,
            pr_number=pr_number,
            project=project,
            pr_state=pr_state,
            pr_merged=pr_merged,
            check_runs=plan_data.get("check_runs", []),
            preview_kind=plan_data.get("preview_kind", "checks"),
            preview_title=plan_data.get("title", "PR Check Preview"),
            unavailable_title=plan_data.get("unavailable_title", "Preview Not Available"),
            output_label=plan_data.get("output_label", "Plan Output"),
            action_hint=plan_data.get("action_hint", "Review the CI checks above, then decide:"),
            plan_found=plan_data.get("found", False),
            execution_status=plan_data.get("execution_status", "unknown"),
            execution_conclusion=plan_data.get("execution_conclusion", ""),
            execution_message=plan_data.get("execution_message", ""),
            execution_runs=plan_data.get("execution_runs", []),
            execution_url=plan_data.get("execution_url", ""),
            merge_commit_sha=plan_data.get("merge_commit_sha", ""),
            format_status=plan_data.get("format_status", "unknown"),
            validate_status=plan_data.get("validate_status", "unknown"),
            plan_output=plan_data.get("plan_output", ""),
            message=plan_data.get("message", ""),
            show_actions=pr_state == "open" and not pr_merged,
            github_pr_url=f"https://github.com/{settings.github_org}/{project}/pull/{pr_number}",
        )

    except Exception as e:
        logger.error(f"Error loading PR checks for {project} PR#{pr_number}: {e}", exc_info=True)
        return render_partial(
            "partials/state-error.html",
            request,
            title="Error loading PR checks",
            message=str(e),
            retry_url=f"/partials/pr-plan?pr_number={pr_number}&project={project}",
            retry_target="#main",
        )
