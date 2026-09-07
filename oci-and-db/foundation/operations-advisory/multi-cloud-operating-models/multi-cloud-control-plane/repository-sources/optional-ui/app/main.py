"""FastAPI application - Multi-Cloud-Plane GitOps UI."""
import logging
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.helpers import oauth, templates  # Imported from helpers
from app.auth import (
    GuardResponseException,
    clear_oauth_token,
    get_current_user,
    get_github_client,
    store_oauth_token,
)
from app.routers import dashboard, operations, resources, audit
from app.services.project_service import ProjectService

# Logging — only configure if no handlers are set, so uvicorn/pytest config wins.
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# App
app = FastAPI(title="Multi Cloud Control Plane", version="2.1.0")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
app.add_middleware(CORSMiddleware, allow_origins=[settings.app_url], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Include routers
app.include_router(dashboard.router, prefix="/partials")
app.include_router(operations.router, prefix="/partials")
app.include_router(resources.router, prefix="/partials")
app.include_router(audit.router, prefix="/partials")


@app.exception_handler(GuardResponseException)
async def guard_response_exception_handler(_: Request, exc: GuardResponseException):
    """Return pre-rendered guard responses from dependency checks."""
    return exc.response

# Static files
static_path = Path(__file__).parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# ============ Routes ============

@app.get("/login")
async def login(request: Request):
    """Redirect to GitHub OAuth."""
    error = request.query_params.get("error")
    if not settings.github_client_id or not settings.github_client_secret:
        return RedirectResponse(url="/static/login.html?error=oauth_not_configured")
    if error:
        return RedirectResponse(url=f"/static/login.html?error={error}")
    # Build callback URL from the incoming request host/port to avoid OAuth/session
    # mismatches when users access the app via IP/localhost/proxy.
    callback_url = str(request.url_for("callback"))
    return await oauth.github.authorize_redirect(request, callback_url)


@app.get("/callback")
async def callback(request: Request):
    """GitHub OAuth callback."""
    try:
        token = await oauth.github.authorize_access_token(request)
        resp = await oauth.github.get('user', token=token)
        user_data = resp.json()
        session_id = store_oauth_token(token.get('access_token') or "")
        request.session['user'] = {
            'login': user_data.get('login'),
            'name': user_data.get('name') or user_data.get('login'),
            'avatar_url': user_data.get('avatar_url'),
            'session_id': session_id,
        }
        logger.info(f"User {user_data.get('login')} logged in")
        return RedirectResponse(url="/")
    except Exception as e:
        logger.error(f"OAuth error: {e}")
        return RedirectResponse(url="/login?error=oauth_failed")


@app.get("/logout")
async def logout(request: Request):
    """Clear session."""
    user = get_current_user(request) or {}
    clear_oauth_token(user.get("session_id"))
    request.session.clear()
    return RedirectResponse(url="/static/login.html")


@app.get("/")
async def root(request: Request):
    """Main UI."""
    user = get_current_user(request)
    if settings.github_client_id and not user:
        return RedirectResponse(url="/login")

    github = None
    if user:
        try:
            github = get_github_client(request)
        except HTTPException:
            return RedirectResponse(url="/login")

    try:
        projects = await ProjectService(github_client=github).list_projects() if github else []
    except Exception as e:
        logger.warning(f"Could not load projects: {e}")
        projects = []

    return templates.TemplateResponse(request, "pages/home.html", {
        "request": request, "projects": projects, "user": user
    })


@app.get("/health")
def health():
    """Health check."""
    return {"status": "healthy", "version": "2.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.app_host, port=settings.app_port, reload=True)
