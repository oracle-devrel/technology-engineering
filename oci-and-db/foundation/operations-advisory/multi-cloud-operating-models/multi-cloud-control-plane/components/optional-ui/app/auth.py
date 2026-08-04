"""Authentication helpers and GitHub client factory."""
import secrets
import time
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import Response

from app.config import settings
from app.github import GitHubClient
from app.helpers import render_partial
from app.services.installation_service import InstallationError, load_mccp_installation

_OAUTH_SESSION_TTL_SECONDS = 8 * 60 * 60
_oauth_tokens_by_session_id: dict[str, tuple[str, float]] = {}


def store_oauth_token(access_token: str) -> str:
    """Store an OAuth token server-side and return its public session id."""
    session_id = secrets.token_urlsafe(32)
    _oauth_tokens_by_session_id[session_id] = (
        access_token,
        time.monotonic() + _OAUTH_SESSION_TTL_SECONDS,
    )
    return session_id


def clear_oauth_token(session_id: str | None) -> None:
    """Remove an OAuth token from the in-memory session store."""
    if session_id:
        _oauth_tokens_by_session_id.pop(session_id, None)


def get_oauth_token(session_id: str | None) -> str | None:
    """Return a non-expired OAuth token for a server-side session id."""
    if not session_id:
        return None
    token_record = _oauth_tokens_by_session_id.get(session_id)
    if not token_record:
        return None
    token, expires_at = token_record
    if expires_at <= time.monotonic():
        clear_oauth_token(session_id)
        return None
    return token


def get_current_user(request: Request) -> dict | None:
    """Return the session user if logged in."""
    return request.session.get("user")


def require_user(request: Request) -> dict:
    """Require a logged-in user for protected routes."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"HX-Redirect": "/login"},
        )
    return user


def get_github_client(request: Request) -> GitHubClient:
    """Return a GitHub client using the user's OAuth token."""
    user = require_user(request)
    token = get_oauth_token(user.get("session_id"))
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Missing OAuth token",
            headers={"HX-Redirect": "/login"},
        )
    return GitHubClient(token=token)


def require_github_client(request: Request) -> None:
    """Ensure an authenticated GitHub client is available on request.state."""
    request.state.github_client = get_github_client(request)


async def has_project_access(request: Request, project: str, require_write: bool = False) -> bool:
    """Check if the current OAuth user has access to the given project."""
    primary_client = request.state.github_client

    try:
        installation = load_mccp_installation(settings.mccp_installation_path)
    except InstallationError:
        return False
    if settings.github_org != installation.customer_org:
        return False
    try:
        installation.project_context(
            project,
            "prod" if (project or "").strip().startswith("prod-") else "dev",
        )
    except InstallationError:
        return False

    def _allowed(permissions: dict) -> bool:
        if not permissions:
            return False
        if require_write:
            return bool(permissions.get("push") or permissions.get("admin"))
        return bool(permissions.get("pull") or permissions.get("push") or permissions.get("admin"))

    if require_write:
        project_name = (project or "").strip()
        project_name_lc = project_name.lower()
        if (
            project_name_lc in {"gitops-templates", "platform-ci"}
            or project_name_lc.endswith("-template")
        ):
            return False

        repo = await primary_client.get_repo(project_name)
        if not repo or repo.get("is_template"):
            return False
        permissions = repo.get("permissions") or await primary_client.get_repo_permissions(project_name)
    else:
        permissions = await primary_client.get_repo_permissions(project)
    if _allowed(permissions):
        return True

    return False


async def user_can_access_configured_org(github_client: GitHubClient) -> bool:
    """Return whether the OAuth user can read at least one repo in the configured org."""
    org = (settings.github_org or "").strip().lower()
    if not org:
        return False

    try:
        org_repos = await github_client.list_org_repos(limit=1)
        if org_repos:
            return True
    except Exception:
        pass

    try:
        user_repos = await github_client.list_user_repos(limit=500)
    except Exception:
        user_repos = []

    for repo in user_repos or []:
        owner = repo.get("owner") or {}
        owner_login = str(owner.get("login") or "").lower()
        full_name = str(repo.get("full_name") or "").lower()
        if owner_login == org or full_name.startswith(f"{org}/"):
            return True
    return False


async def project_access_guard(
    request: Request,
    project: str | None,
    *,
    require_write: bool = False,
    require_selection: bool = False,
) -> Response | None:
    """Return a rendered partial response when access validation fails."""
    if require_selection and not project:
        return render_partial("partials/state-empty.html", request, message="Select a project")
    if project and not await has_project_access(request, project, require_write=require_write):
        return render_partial(
            "partials/state-error.html",
            request,
            title="Access denied",
            message="You don't have access to this project.",
        )
    return None


class GuardResponseException(Exception):
    """Raised by access dependencies to short-circuit with a rendered response."""

    def __init__(self, response: Response):
        self.response = response
        super().__init__("Guard blocked request")


def _raise_if_denied(response: Response | None) -> None:
    if response is not None:
        raise GuardResponseException(response)


async def require_project_optional_access(
    request: Request,
    project: str | None = Query(None),
) -> str | None:
    """Optional project query param with read-access guard when present."""
    _raise_if_denied(await project_access_guard(request, project))
    return project


async def require_project_selected_access(
    request: Request,
    project: str | None = Query(None),
) -> str:
    """Require selected project and read access."""
    _raise_if_denied(await project_access_guard(request, project, require_selection=True))
    return project or ""


async def require_project_read_access(
    request: Request,
    project: str = Query(...),
) -> str:
    """Require explicit project query param and read access."""
    _raise_if_denied(await project_access_guard(request, project))
    return project


async def ensure_project_write_access(request: Request, project: str) -> None:
    """Ensure write access for a project value from payload/path."""
    _raise_if_denied(await project_access_guard(request, project, require_write=True))


ProjectOptional = Annotated[str | None, Depends(require_project_optional_access)]
ProjectSelected = Annotated[str, Depends(require_project_selected_access)]
ProjectRead = Annotated[str, Depends(require_project_read_access)]
