"""Small stdio client for the local Codex chat demo."""
import asyncio
import json
import os
from pathlib import Path
import signal
import tempfile
import time
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, ValidationError

from app.config import settings
from app.github import GitHubClient
from app.services.chat_panel import proposal_panel, pr_panel


class PanelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["proposal", "pr", "clear"]
    candidate_path: str | None = Field(default=None, max_length=4096)
    manifest_path: str | None = Field(default=None, max_length=512)
    resource_keys: list[StrictStr] = Field(default_factory=list, max_length=20)
    crq: str | None = Field(default=None, max_length=67)
    pr_number: StrictInt | None = Field(default=None, gt=0, le=1000000)


PANEL_TOOL = {
    "type": "function", "name": "mccp_request_panel",
    "description": (
        "Update the web request summary. Use proposal only with an existing local candidate JSON, "
        "its scoped repository manifest path, explicit resource keys and CRQ. The server reads the file. "
        "Use pr with pr_number to independently read GitHub evidence. Use clear for a new request or "
        "when withdrawing a proposal. This tool is read-only and never authorizes publication."
    ),
    "inputSchema": PanelInput.model_json_schema(),
}


def skill_path() -> Path:
    if settings.chat_skill_path:
        return Path(settings.chat_skill_path).expanduser().resolve()
    return (Path(__file__).resolve().parents[4] / "codex-plugins/project-gitops/skills/project-gitops/SKILL.md")


class ChatSession:
    """One isolated workspace and Codex process per browser session/project."""

    def __init__(self, project, environment, region, token, *, command=None):
        self.project = project
        self.environment = environment
        self.region = region
        self.token = token
        self.command = command or [settings.chat_codex_binary, "app-server"]
        self.process = None
        self.workspace = None
        self.thread_id = None
        self.busy = False
        self.last_used = time.monotonic()
        self.sequence = 0
        self.pending = []
        self.panel = None
        self.conversation_id = uuid4().hex
        self.messages = []
        self.needs_reset = False
        self.status_text = "Ready."

    async def _panel_call(self, message):
        try:
            data = PanelInput.model_validate(message.get("params", {}).get("arguments"))
            if data.kind == "proposal":
                panel = proposal_panel(self.workspace.name, self.project, self.environment, self.region,
                                       data.candidate_path, data.manifest_path, data.resource_keys, data.crq)
            elif data.kind == "pr":
                if data.pr_number is None:
                    raise ValueError("A PR number is required.")
                panel = await pr_panel(GitHubClient(self.token), self.project, self.environment, self.region, data.pr_number)
            else:
                panel = None
            self.panel = panel
            result = {"success": True, "contentItems": [{"type": "inputText", "text": json.dumps({"panel": panel})}]}
        except (ValueError, ValidationError, TypeError):
            # Never echo model inputs or candidate contents in a validation error.
            result = {"success": False, "contentItems": [{"type": "inputText", "text": "Panel update rejected. Supply a scoped candidate JSON with runtime credential placeholders and unambiguous resource keys, or a valid PR number."}]}
            panel = self.panel = None
        await self._send({"id": message["id"], "result": result})
        return {"type": "panel", "panel": panel}

    async def _send(self, message):
        self.process.stdin.write((json.dumps(message) + "\n").encode())
        await self.process.stdin.drain()

    async def _read(self):
        line = await asyncio.wait_for(self.process.stdout.readline(), timeout=300)
        if not line:
            raise RuntimeError("Codex process stopped")
        return json.loads(line)

    async def _rpc(self, method, params):
        self.sequence += 1
        request_id = self.sequence
        await self._send({"id": request_id, "method": method, "params": params})
        while True:
            message = await self._read()
            if message.get("id") == request_id and "method" not in message:
                if "error" in message:
                    raise RuntimeError("Codex rejected the request")
                return message["result"]
            if message.get("method") == "item/tool/call" and message.get("params", {}).get("tool") == PANEL_TOOL["name"]:
                event = await self._panel_call(message)
                self.pending.append({"method": "mccp/panel", "params": event})
            else:
                self.pending.append(message)

    async def _start(self):
        path = skill_path()
        if not path.is_file():
            raise RuntimeError("Project GitOps skill is not installed")
        self.workspace = tempfile.TemporaryDirectory(prefix="mccp-chat-")
        env = os.environ.copy()
        # GitHub CLI and Git HTTPS use the web user's identity, not host credentials.
        env.update(GH_TOKEN=self.token, GITHUB_TOKEN=self.token)
        git_config = [
            ("credential.helper", ""),
            ("credential.helper", "!gh auth git-credential"),
            ("url.https://github.com/.insteadOf", "git@github.com:"),
            ("url.https://github.com/.insteadOf", "ssh://git@github.com/"),
        ]
        env["GIT_CONFIG_COUNT"] = str(len(git_config))
        for index, (key, value) in enumerate(git_config):
            env[f"GIT_CONFIG_KEY_{index}"] = key
            env[f"GIT_CONFIG_VALUE_{index}"] = value
        self.process = await asyncio.create_subprocess_exec(
            *self.command, cwd=self.workspace.name, env=env,
            stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL, limit=4 * 1024 * 1024,
            start_new_session=True,
        )
        await self._rpc("initialize", {"clientInfo": {"name": "mccp_web_demo", "version": "0.1.0"},
                                       "capabilities": {"experimentalApi": True}})
        await self._send({"method": "initialized", "params": {}})
        instructions = (
            "You are AI Operations, a governed cloud operations assistant using the shared project-gitops skill. "
            f"The only permitted target is multicloud-control-plane/{self.project}, "
            f"OCI {self.environment}, region {self.region}. Refuse changes outside this scope. "
            "Use the project-gitops skill and its references for every request. "
            "Its Consult, Request change, Operate and Investigate contracts are shared with Codex; follow them here. "
            "The browser messages are the user's instructions; require a standalone confirm after "
            "the semantic preview before any GitHub write, including issues, branches, commits or PRs. "
            "Confirmations apply only to the exact preview and current main. "
            "Never approve or merge PRs, dispatch workflows, run Terraform/Ansible or call cloud APIs. "
            "Use the temporary working directory for disposable clones and artifacts. "
            "Never read host credentials, environment secrets, .env files or Codex configuration. "
            "GitHub authentication is already configured; do not print tokens. "
            "If intent conflicts with the selected project, explain the selected project and environment boundary. "
            "Use mccp_request_panel after preparing or changing a resource or operation candidate JSON and semantic preview: "
            "pass the candidate's absolute path inside your working directory, target manifest_path, CRQ and only the changed resource keys or exact operation target names. "
            "For removal of a pending lifecycle request, use an empty local JSON candidate and no resource keys; this previews the removal, not a cloud action. "
            "Never put literal passwords in candidates. Call clear before starting a different request or withdrawing a proposal. "
            "After publishing a PR, or when asked about an existing PR, call it with kind pr and its number. "
            "The panel's GitHub evidence is independent of your prose. Never claim panel verification unless the tool succeeded. "
            "For read-only catalog/inventory questions with no active request, leave the panel empty."
        )
        params = {"cwd": self.workspace.name, "approvalPolicy": "never",
                  "sandbox": "workspace-write", "ephemeral": True,
                  "developerInstructions": instructions, "dynamicTools": [PANEL_TOOL]}
        if settings.chat_model:
            params["model"] = settings.chat_model
        result = await self._rpc("thread/start", params)
        self.thread_id = result["thread"]["id"]

    async def turn(self, text):
        self.last_used = time.monotonic()
        if self.process is None:
            await self._start()
        await self._rpc("turn/start", {
            "threadId": self.thread_id,
            "input": [{"type": "text", "text": text},
                      {"type": "skill", "name": "project-gitops", "path": str(skill_path())}],
            "sandboxPolicy": {"type": "workspaceWrite", "writableRoots": [self.workspace.name],
                              "networkAccess": True},
        })
        last_message_id = None
        while True:
            message = self.pending.pop(0) if self.pending else await self._read()
            method = message.get("method", "")
            params = message.get("params", {})
            if "id" in message and method:
                # No automatic shell permission grants or hidden approval prompts.
                if method == "item/tool/call" and params.get("tool") == PANEL_TOOL["name"]:
                    yield await self._panel_call(message)
                    continue
                elif method in ("item/commandExecution/requestApproval", "item/fileChange/requestApproval"):
                    await self._send({"id": message["id"], "result": {"decision": "decline"}})
                else:
                    await self._send({"id": message["id"], "error": {"code": -32601, "message": "Unsupported by web demo"}})
                yield {"type": "status", "text": "A runtime permission request was declined."}
            elif method == "mccp/panel":
                yield params
            elif method == "item/agentMessage/delta":
                item_id = params.get("itemId")
                if last_message_id is not None and item_id and item_id != last_message_id:
                    yield {"type": "delta", "text": "\n\n"}
                if item_id:
                    last_message_id = item_id
                yield {"type": "delta", "text": params["delta"]}
            elif method == "item/started" and params.get("item", {}).get("type") == "commandExecution":
                    yield {"type": "status", "text": "Working on your request…"}
            elif method == "error":
                if params.get("willRetry"):
                    yield {"type": "status", "text": "Codex is reconnecting. Waiting for the response…"}
                else:
                    raise RuntimeError("Codex reported an error")
            elif method == "turn/completed":
                if params["turn"]["status"] == "failed":
                    raise RuntimeError("Codex turn failed")
                self.last_used = time.monotonic()
                yield {"type": "done", "status": params["turn"]["status"]}
                return

    async def close(self):
        if self.process and self.process.returncode is None:
            try:
                os.killpg(self.process.pid, signal.SIGTERM)
                await asyncio.wait_for(self.process.wait(), timeout=3)
            except ProcessLookupError:
                pass
            except asyncio.TimeoutError:
                os.killpg(self.process.pid, signal.SIGKILL)
                await self.process.wait()
        if self.workspace:
            self.workspace.cleanup()
        self.token = ""
