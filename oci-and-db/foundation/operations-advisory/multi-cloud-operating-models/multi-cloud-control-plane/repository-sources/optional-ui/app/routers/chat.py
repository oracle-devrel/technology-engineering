"""Authenticated, opt-in project-scoped chat for the local demo."""
import asyncio
from contextlib import asynccontextmanager
import json
import time
from urllib.parse import urlsplit

import anyio

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from markdown_it import MarkdownIt

from app.auth import require_user, require_github_client, has_project_access, get_oauth_token
from app.config import settings
from app.helpers import render_partial
from app.services.chat_service import ChatSession
from app.services.chat_panel import pr_panel
from app.services.project_context import project_context, ProjectContextError

router = APIRouter()
sessions: dict[tuple[str, str], ChatSession] = {}
_chat_markdown = MarkdownIt("js-default").disable("image")


def _chat_link_open(tokens, index, options, env):
    try:
        url = urlsplit(tokens[index].attrGet("href") or "")
        web_link = url.scheme in {"https", "http"} and bool(url.netloc)
    except ValueError:
        web_link = False
    env["chat_web_link"] = web_link
    return _chat_markdown.renderer.renderToken(tokens, index, options, env) if web_link else ""


def _chat_link_close(tokens, index, options, env):
    return "</a>" if env.pop("chat_web_link", False) else ""


_chat_markdown.renderer.rules["link_open"] = _chat_link_open
_chat_markdown.renderer.rules["link_close"] = _chat_link_close


def render_chat_markdown(text: str) -> str:
    """Render chat Markdown with tables, without raw HTML or remote images."""
    return _chat_markdown.render(text)


def authorize_chat(request):
    if not settings.chat_enabled:
        raise HTTPException(404, "Chat demo is disabled")
    user = require_user(request)
    if not settings.chat_demo_login or user.get("login", "").lower() != settings.chat_demo_login.lower():
        raise HTTPException(403, "Chat is limited to the configured demo presenter")
    return user


async def close_session(key):
    # Logout closes every project; scoped reset and expiry close only one.
    keys = [key] if isinstance(key, tuple) else [item for item in sessions if item[0] == key]
    for item in keys:
        session = sessions.pop(item, None)
        if session:
            await session.close()


@asynccontextmanager
async def lifespan(app):
    async def reap():
        while True:
            await asyncio.sleep(60)
            for key, session in list(sessions.items()):
                if not session.busy and time.monotonic() - session.last_used > 1800:
                    await close_session(key)
    task = asyncio.create_task(reap())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        for key in list(sessions):
            await close_session(key)


async def check_project(request, project):
    authorize_chat(request)
    if settings.github_org != "multicloud-control-plane":
        raise HTTPException(503, "Chat requires the skill's configured multicloud-control-plane organization")
    try:
        context = project_context(project, "prod" if project.startswith("prod-") else "dev")
    except ProjectContextError:
        raise HTTPException(403, "Select a governed project repository")
    require_github_client(request)
    if not await has_project_access(request, project, require_write=True):
        raise HTTPException(403, "Project write access is required")
    return context


@router.get("/partials/chat")
async def chat_partial(request: Request, project: str | None = None):
    if not project:
        user = authorize_chat(request)
        if not get_oauth_token(user["session_id"]):
            raise HTTPException(401, "Sign in again")
        return render_partial("partials/ai-operations-home.html", request)
    context = await check_project(request, project)
    scopes = settings.chat_scopes
    return render_partial("partials/chat.html", request, project=project, environment=context.environment,
                          scopes=scopes, scope_label=" · ".join(f"{scope['cloud'].upper()} {scope['region']}" for scope in scopes))


class ChatMessage(BaseModel):
    project: str = Field(min_length=1, max_length=100)
    message: str = Field(min_length=1, max_length=12000)
    conversation_id: str | None = Field(default=None, max_length=64)


def check_origin(request):
    if request.headers.get("origin") != settings.app_url.rstrip("/"):
        raise HTTPException(403, "Invalid browser origin")


@router.get("/api/chat")
async def chat_state(request: Request, project: str):
    await check_project(request, project)
    user_key = require_user(request)["session_id"]
    if not get_oauth_token(user_key):
        raise HTTPException(401, "Sign in again")
    key = (user_key, project)
    session = sessions.get(key)
    if session and session.project != project:
        raise HTTPException(403, "Chat belongs to a different project")
    state = {"project": project, "exists": bool(session), "conversation_id": None,
             "messages": [], "panel": None, "busy": False, "needs_reset": False, "status": "Ready."}
    if session:
        state.update(conversation_id=session.conversation_id, panel=session.panel, busy=session.busy,
                     needs_reset=session.needs_reset, status=session.status_text,
                     messages=[{**item, **({"html": render_chat_markdown(item["text"])}
                                          if item["role"] == "Project GitOps" else {})}
                               for item in session.messages])
    return JSONResponse(state, headers={"Cache-Control": "no-store"})


@router.post("/api/chat")
async def send_message(request: Request, body: ChatMessage):
    check_origin(request)
    context = await check_project(request, body.project)
    scopes = settings.chat_scopes
    user = require_user(request)
    key = (user["session_id"], body.project)
    token = get_oauth_token(user["session_id"])
    if not token:
        raise HTTPException(401, "Sign in again")
    session = sessions.get(key)
    if ((session and body.conversation_id != session.conversation_id)
            or (not session and body.conversation_id is not None)):
        raise HTTPException(409, "The chat changed or expired. Reload to recover it, or select New chat.")
    if session and session.project != body.project:
        raise HTTPException(409, "Start a new chat for the selected project")
    if session and session.needs_reset:
        raise HTTPException(409, "The previous response was interrupted. Select New chat before continuing.")
    if session and session.busy:
        raise HTTPException(409, "Wait for the current response")
    if session and session.scopes != scopes:
        raise HTTPException(409, "The configured cloud regions changed. Select New chat before continuing.")
    if session is None:
        if len(sessions) >= 20:
            raise HTTPException(429, "Too many demo sessions; close an existing chat")
        session = ChatSession(body.project, context.environment, settings.default_region, token, scopes=scopes)
        sessions[key] = session
    session.busy = True
    answer_record = {"role": "Project GitOps", "text": ""}
    session.messages.extend([{"role": "You", "text": body.message}, answer_record])
    session.status_text = "Connecting to AI Operations…"

    async def stream():
        completed = False
        answer = ""
        try:
            yield json.dumps({"type": "session", "conversation_id": session.conversation_id}) + "\n"
            yield json.dumps({"type": "status", "text": session.status_text}) + "\n"
            async for event in session.turn(body.message):
                if event["type"] == "delta":
                    answer += event["text"]
                    answer_record["text"] = answer
                    event = {**event, "html": render_chat_markdown(answer)}
                elif event["type"] == "status":
                    session.status_text = event["text"]
                elif event["type"] == "panel":
                    session.panel = event["panel"]
                elif event["type"] == "done":
                    completed = event.get("status") == "completed"
                    session.status_text = "Ready." if completed else "Response interrupted. Select New chat to continue."
                yield json.dumps(event) + "\n"
        except Exception:
            yield json.dumps({"type": "error", "text": "Codex could not complete this turn. Check the local Codex login and skill configuration, then start a new chat."}) + "\n"
        finally:
            session.last_used = time.monotonic()
            if not completed and sessions.get(key) is session:
                # StreamingResponse cancels its task group on browser disconnect.
                # Retain the transcript, but never silently replace the lost thread.
                session.needs_reset = True
                session.status_text = "Response interrupted. Your messages are preserved. Select New chat to continue."
                with anyio.CancelScope(shield=True):
                    await session.close()
            session.busy = False

    return StreamingResponse(stream(), media_type="application/x-ndjson", headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"})


@router.delete("/api/chat")
async def reset_chat(request: Request, project: str):
    check_origin(request)
    user = authorize_chat(request)
    await check_project(request, project)
    await close_session((user["session_id"], project))
    return {"status": "closed"}


class PanelRefresh(BaseModel):
    project: str = Field(min_length=1, max_length=100)
    conversation_id: str | None = Field(default=None, max_length=64)


@router.post("/api/chat/panel")
async def refresh_panel(request: Request, body: PanelRefresh):
    check_origin(request)
    await check_project(request, body.project)
    user = require_user(request)
    if not get_oauth_token(user["session_id"]):
        raise HTTPException(401, "Sign in again")
    key = (user["session_id"], body.project)
    session = sessions.get(key)
    if not session or session.project != body.project:
        raise HTTPException(410, "Chat expired. Start a new chat.")
    if session.busy:
        raise HTTPException(409, "Wait for the current response")
    if session.needs_reset or (body.conversation_id is not None and body.conversation_id != session.conversation_id):
        raise HTTPException(409, "The chat changed. Reload to recover it, or select New chat.")
    if not session.panel or session.panel.get("kind") != "pr":
        raise HTTPException(400, "No PR is selected in this chat")
    selected_panel = session.panel
    conversation_id = session.conversation_id
    message_count = len(session.messages)
    result = await pr_panel(request.state.github_client, session.project, session.environment,
                            session.region, selected_panel["pr_number"], scopes=session.scopes)
    if (sessions.get(key) is not session or session.project != body.project
            or session.conversation_id != conversation_id or session.panel is not selected_panel
            or len(session.messages) != message_count or session.busy or session.needs_reset):
        raise HTTPException(409, "The chat or selected PR changed. Discard this evidence.")
    session.panel = result
    return {"panel": result}
