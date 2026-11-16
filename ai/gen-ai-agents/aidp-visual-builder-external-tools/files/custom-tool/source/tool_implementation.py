"""AIDP custom tool that refreshes an ADB MCP token for every invocation."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import aidputils
from aidputils.agents.tools.custom_tools.base import CustomToolBase


TOOL_NAME = "SUPPLIER_FEEDBACK_SQL"
PROTOCOL_VERSION = "2025-03-26"
MAX_QUESTION_LENGTH = 4000


class SupplierFeedbackMCPError(RuntimeError):
    """Raised when the database authentication or MCP request fails."""


def _post_json(
    url: str,
    payload: dict[str, Any],
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 45,
) -> tuple[int, Any, str]:
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.headers, response.read().decode(
                "utf-8", errors="replace"
            )
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers, exc.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise SupplierFeedbackMCPError(
            f"Could not reach the database service: {exc.reason}"
        ) from exc


def _parse_mcp_response(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if not raw:
        return {}
    try:
        result = json.loads(raw)
        if isinstance(result, dict):
            return result
    except json.JSONDecodeError:
        pass

    # Streamable HTTP can return a JSON-RPC response as an SSE data event.
    for line in raw.splitlines():
        if line.startswith("data:"):
            data = line[5:].strip()
            if data and data != "[DONE]":
                result = json.loads(data)
                if isinstance(result, dict):
                    return result
    raise SupplierFeedbackMCPError("The database returned an unreadable MCP response.")


def _get_token(token_url: str, username: str, password: str, timeout: int) -> str:
    status, _, raw = _post_json(
        token_url,
        {
            "grant_type": "password",
            "username": username,
            "password": password,
        },
        headers={"Accept": "application/json"},
        timeout=timeout,
    )
    if status != 200:
        raise SupplierFeedbackMCPError(
            f"Database token request failed with HTTP {status}. Check the credential and database account."
        )
    try:
        token = json.loads(raw).get("access_token")
    except (json.JSONDecodeError, AttributeError) as exc:
        raise SupplierFeedbackMCPError(
            "Database token endpoint returned an invalid response."
        ) from exc
    if not token:
        raise SupplierFeedbackMCPError(
            "Database token endpoint did not return an access token."
        )
    return token


class _MCPConnection:
    """Minimal Streamable HTTP MCP client for this single known tool."""

    def __init__(self, mcp_url: str, token: str, timeout: int):
        self.mcp_url = mcp_url
        self.token = token
        self.timeout = timeout
        self.session_id: str | None = None
        self.protocol_version = PROTOCOL_VERSION
        self.request_id = 0

    def _send(self, message: dict[str, Any], *, notification: bool = False) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.token}"}
        if self.protocol_version:
            headers["MCP-Protocol-Version"] = self.protocol_version
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id

        status, response_headers, raw = _post_json(
            self.mcp_url, message, headers=headers, timeout=self.timeout
        )
        accepted = (200, 202, 204) if notification else (200, 202)
        if status not in accepted:
            # Do not include server bodies or authorization data in agent traces.
            raise SupplierFeedbackMCPError(f"Database MCP request failed with HTTP {status}.")
        self.session_id = response_headers.get("Mcp-Session-Id", self.session_id)
        if notification or not raw.strip():
            return {}
        response = _parse_mcp_response(raw)
        if "error" in response:
            error = response.get("error", {})
            message_text = error.get("message", "MCP request failed") if isinstance(error, dict) else "MCP request failed"
            raise SupplierFeedbackMCPError(f"Database MCP error: {message_text}")
        return response

    def call(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.request_id += 1
        return self._send(
            {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": method,
                "params": params,
            }
        )

    def query(self, question: str) -> dict[str, Any]:
        initialized = self.call(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "aidp-supplier-feedback-tool", "version": "1.0.0"},
            },
        )
        negotiated_version = initialized.get("result", {}).get("protocolVersion")
        if negotiated_version:
            self.protocol_version = negotiated_version

        self._send(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            notification=True,
        )
        response = self.call(
            "tools/call",
            {
                "name": TOOL_NAME,
                "arguments": {"ACTION": "runsql", "QUERY": question},
            },
        )
        result = response.get("result", {})
        if result.get("isError"):
            raise SupplierFeedbackMCPError("The supplier query failed in the database tool.")

        contents = result.get("content", [])
        text_parts = [
            item.get("text", "")
            for item in contents
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        text_result = "\n".join(part for part in text_parts if part).strip()
        if not text_result:
            return {"rows": [], "message": "The database tool returned no text results."}
        try:
            parsed = json.loads(text_result)
        except json.JSONDecodeError:
            return {"result": text_result}
        if isinstance(parsed, list):
            return {"rows": parsed}
        return {"result": parsed}


@CustomToolBase.register
class SupplierFeedbackQuery(CustomToolBase):
    """Query supplier feedback with Select AI using natural-language questions."""

    @classmethod
    def _validate_config(cls, conf, runtime_params, **context_vars):
        tool_conf = conf.get("conf", conf)
        if not tool_conf.get("credential_name"):
            raise ValueError("Set credential_name in the tool Configuration tab.")
        if not str(tool_conf.get("region", "")).strip():
            raise ValueError("Set the Autonomous Database region in the tool Configuration tab.")
        if not str(tool_conf.get("database_ocid", "")).strip().startswith("ocid1.autonomousdatabase."):
            raise ValueError("Set the Autonomous Database OCID in the tool Configuration tab.")
        if not runtime_params.get("question", "").strip():
            raise ValueError("Provide a natural-language question.")

    @classmethod
    def _execute_tool(cls, conf, runtime_params, **context_vars):
        tool_conf = conf.get("conf", conf)
        question = str(runtime_params.get("question", "")).strip()
        if not question:
            raise ValueError("Provide a natural-language question.")
        if len(question) > MAX_QUESTION_LENGTH:
            raise ValueError(f"Question is too long; limit is {MAX_QUESTION_LENGTH} characters.")

        credential_name = str(tool_conf.get("credential_name", "")).strip()
        region = str(tool_conf.get("region", "")).strip()
        database_ocid = str(tool_conf.get("database_ocid", "")).strip()
        username_key = str(tool_conf.get("username_key", "username"))
        password_key = str(tool_conf.get("password_key", "password"))
        timeout = int(tool_conf.get("timeout_seconds", 45))
        if timeout < 5 or timeout > 120:
            raise ValueError("timeout_seconds must be between 5 and 120.")

        username = aidputils.secrets.get(name=credential_name, key=username_key)
        password = aidputils.secrets.get(name=credential_name, key=password_key)
        if not username or not password:
            raise ValueError(
                "Could not read the configured database username/password from the AIDP Credential Store."
            )

        host = f"https://dataaccess.adb.{region}.oraclecloudapps.com"
        token_url = f"{host}/adb/auth/v1/databases/{database_ocid}/token"
        mcp_url = f"{host}/adb/mcp/v1/databases/{database_ocid}"
        token = _get_token(token_url, str(username), str(password), timeout)
        try:
            return _MCPConnection(mcp_url, token, timeout).query(question)
        finally:
            # Avoid retaining the short-lived access token beyond this invocation.
            token = ""
            password = ""
