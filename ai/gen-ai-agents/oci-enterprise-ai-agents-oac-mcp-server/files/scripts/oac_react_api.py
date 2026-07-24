# Copyright (c) 2026 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

"""JSON bridge for the React Oracle Analytics MCP demo.

The script reads one JSON object from stdin and writes one JSON object to stdout.
Tokens stay in stdin payloads, not CLI arguments.
"""

from __future__ import annotations

import json
import os
import base64
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from openai import OpenAI


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (PROJECT_ROOT / ".env", PROJECT_ROOT / ".env.local")


def _is_placeholder(value: str) -> bool:
    value = value.strip()
    return value.startswith("<") and value.endswith(">")


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_local_env() -> None:
    """Load .env files if present. Shell-exported values still win."""
    for path in ENV_FILES:
        if path.exists():
            for key, value in _read_env_file(path).items():
                current = os.environ.get(key, "").strip()
                if not current or _is_placeholder(current):
                    os.environ[key] = value


DEFAULT_REGION = "eu-frankfurt-1"
DEFAULT_MODEL = "openai.gpt-oss-120b"
# Set OAC_MCP_SERVER_URL in .env (or paste the URL in the UI). The refresh URL
# is derived from the MCP URL when OAC_TOKEN_REFRESH_URL is not set explicitly.
DEFAULT_OAC_MCP_URL = ""
DEFAULT_OAC_TOKEN_REFRESH_URL = ""
DEFAULT_TOKENS_FILE = PROJECT_ROOT / "tokens.json"
MCP_PROTOCOL_VERSION = "2025-11-25"
OAC_ALLOWED_TOOLS = ["discover_data", "describe_data", "execute_logical_sql"]

OAC_ANALYST_INSTRUCTIONS = """
You are a senior Oracle Analytics Cloud analyst working through an OAC MCP
server. Use tools deliberately and keep context compact.

Workflow:
1. If the target subject area or dataset is unclear, call discover_data first.
   discover_data returns BOTH governed SubjectAreas and uploaded Datasets
   (model = "custom"). Match the user's topic to any of them by displayName
   (e.g. a request about "crimes" maps to the "LA Crime Data" dataset).
2. Call describe_data only for the relevant subject area or dataset.
3. Build read-only Logical SQL using the exact names from describe_data.
4. Execute Logical SQL only for analytical SELECT-style questions.
5. Summarize the result in business language and include the Logical SQL used.

Logical SQL syntax:
- Governed subject area: SELECT "Subject Area"."Folder"."Column" ...
  FROM "Subject Area".
- Uploaded dataset (model = "custom"): reference it in the FROM clause as
  FROM XSA('<owner>'.'<Dataset Name>') using the dataset's "name" value from
  discover_data, and select columns by their exact describe_data names in
  double quotes, e.g.
  SELECT "Area Name", COUNT(*) AS "Crimes"
  FROM XSA('federico.venturin@oracle.com'.'LA Crime Data')
  GROUP BY "Area Name".
  A plain FROM "Dataset Name" without the XSA(...) wrapper will fail.
- Map vague user terms to the closest described column (e.g. "department" ->
  "Area Name"). If no column is a reasonable match, say so instead of guessing.

Guardrails:
- Do not claim dashboard, workbook, or catalog browsing unless the MCP server
  exposes those capabilities. This OAC server is expected to expose data tools:
  discover_data, describe_data, and execute_logical_sql.
- Prefer aggregated results and sensible limits over wide raw extracts.
- Avoid listing every column. Mention only the dimensions and measures needed.
- If multiple subject areas match, ask one concise clarification question.
- Never attempt write operations, data changes, admin actions, or credential work.
- If a tool returns large metadata, retain only the useful fields in your answer.

Final answer:
- Direct answer first.
- Then Logical SQL when a query was executed.
- Then short caveats or next analytical questions when useful.
- Output only the final answer. Never include scratchpad, internal planning,
  tool-call narration, or phrases like "we need to call", "now call", or
  "let's attempt".
""".strip()


OAC_LOGICAL_SQL_RULES = (
    "Logical SQL rules. Build the query only from the exact column names returned "
    "by describe_data; do not invent physical tables, joins, foreign keys, or "
    "database syntax. For a governed subject area use FROM \"Subject Area\" and "
    "\"Subject Area\".\"Folder\".\"Column\". For an uploaded dataset (a discover_data "
    "Datasets entry, model=custom) the FROM clause MUST be "
    "FROM XSA('<owner>'.'<Dataset Name>') using the dataset's exact 'name' value "
    "from discover_data, with columns selected by their exact describe_data names "
    "in double quotes, e.g. SELECT \"Area Name\", COUNT(*) AS \"Crimes\" "
    "FROM XSA('owner@example.com'.'LA Crime Data') GROUP BY \"Area Name\". "
    "A plain FROM \"Dataset Name\" without the XSA(...) wrapper will fail. "
    "Map vague user terms to the closest described column. When grouping, prefer "
    "a descriptive categorical column (e.g. an area, region, type, or status "
    "name) and avoid unique-identifier columns whose names contain 'number', "
    "'id', 'code', or 'record', since grouping by those yields one row each."
)


def main() -> None:
    """Run one JSON request."""
    os.chdir(PROJECT_ROOT)
    load_local_env()
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        result = dispatch(payload)
        emit_json({"ok": True, **result})
    except Exception as exc:  # pylint: disable=broad-exception-caught
        emit_json(
            {
                "ok": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                },
            }
        )
        raise SystemExit(1) from exc


def emit_json(value: dict[str, Any]) -> None:
    """Write one JSON object."""
    sys.stdout.buffer.write(
        (json.dumps(value, ensure_ascii=True, default=str) + "\n").encode("utf-8")
    )
    sys.stdout.buffer.flush()


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    """Dispatch one bridge action."""
    action = str(payload.get("action") or "chat")
    if action == "config":
        return {"config": config_payload()}
    if action == "initialize":
        return initialize_oac_mcp(payload)
    if action == "chat":
        return run_chat_turn(payload)
    raise ValueError(f"Unknown action: {action}")


def config_payload() -> dict[str, Any]:
    """Return non-secret default config for the React UI."""
    region = os.getenv("OCI_REGION", DEFAULT_REGION)
    return {
        "region": region,
        "model": os.getenv("OAC_DEMO_MODEL")
        or os.getenv("OCI_RESPONSES_MODEL")
        or DEFAULT_MODEL,
        "baseUrl": os.getenv(
            "GENAI_BASE_URL",
            f"https://inference.generativeai.{region}.oci.oraclecloud.com/openai/v1",
        ),
        "projectId": os.getenv("GENAI_PROJECT_ID", ""),
        "oacMcpUrl": normalize_oac_mcp_url(os.getenv("OAC_MCP_SERVER_URL", DEFAULT_OAC_MCP_URL)),
        "hasGenAiApiKey": bool(os.getenv("GENAI_API_KEY", "").strip()),
        "allowedTools": OAC_ALLOWED_TOOLS,
        "defaultPrompt": (
            "Discover available Oracle Analytics subject areas and datasets. "
            "Summarize what is available, then recommend one useful read-only "
            "analysis I can run next. Do not execute Logical SQL yet."
        ),
    }


def initialize_oac_mcp(payload: dict[str, Any]) -> dict[str, Any]:
    """Call OAC MCP initialize directly."""
    oac_url = normalize_oac_mcp_url(required_value(payload, "oacMcpUrl", "OAC_MCP_SERVER_URL"))
    token = resolve_oac_token(payload)
    response = initialize_oac_mcp_with_token(
        oac_url=oac_url,
        token=token,
        timeout_seconds=float(payload.get("timeoutSeconds") or 60),
    )
    tools = []
    tools_error = ""
    if response.status_code < 400:
        try:
            direct_session = DirectOacMcpSession(
                oac_url=oac_url,
                token=token,
                timeout_seconds=float(payload.get("timeoutSeconds") or 60),
            )
            direct_session.initialize()
            tools = [
                {
                    "name": tool.get("name"),
                    "description": str(tool.get("description") or "")[:300],
                }
                for tool in direct_session.list_tools()
            ]
        except Exception as exc:  # pylint: disable=broad-exception-caught
            tools_error = f"{type(exc).__name__}: {exc}"
    return {
        "httpStatus": response.status_code,
        "body": parse_response_body(response),
        "diagnostic": (
            diagnostic_for_oac_status(response.status_code)
            if response.status_code < 400
            else f"{diagnostic_for_oac_status(response.status_code)} {token_failure_detail(payload, token)}"
        ),
        "tokenDiagnostics": token_diagnostics(payload, token),
        "tools": tools,
        "toolsError": tools_error,
    }

def initialize_oac_mcp_with_token(
    *, oac_url: str, token: str, timeout_seconds: float
) -> requests.Response:
    """Call OAC MCP initialize directly using an already-resolved token."""
    response = requests.post(
        oac_url,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "react-oac-demo", "version": "1.0"},
            },
        },
        timeout=timeout_seconds,
        allow_redirects=False,
    )
    return response


def run_chat_turn(payload: dict[str, Any]) -> dict[str, Any]:
    """Run one OAC MCP chat turn through the Responses API."""
    prompt = str(payload.get("prompt") or "").strip()
    if not prompt:
        raise ValueError("Prompt is required.")

    if is_demo_chart_prompt(prompt):
        return demo_chart_response(prompt)
    if is_chart_followup_prompt(prompt) and valid_chart_payload(payload.get("previousChart")):
        return previous_chart_response(payload)

    client = build_openai_client(payload)
    model = str(payload.get("model") or os.getenv("OAC_DEMO_MODEL") or DEFAULT_MODEL)
    oac_url = normalize_oac_mcp_url(required_value(payload, "oacMcpUrl", "OAC_MCP_SERVER_URL"))
    token = resolve_oac_token(payload)
    preflight = initialize_oac_mcp_with_token(
        oac_url=oac_url,
        token=token,
        timeout_seconds=float(payload.get("timeoutSeconds") or 60),
    )
    if preflight.status_code in {401, 403}:
        raise ValueError(
            f"OAC MCP initialize returned HTTP {preflight.status_code}. "
            f"{diagnostic_for_oac_status(preflight.status_code)} "
            f"{token_failure_detail(payload, token)}"
        )
    if preflight.status_code >= 400:
        raise ValueError(
            f"OAC MCP initialize returned HTTP {preflight.status_code}: "
            f"{str(parse_response_body(preflight))[:1000]}"
        )

    return run_direct_oac_tool_loop(
        payload=payload,
        client=client,
        model=model,
        oac_url=oac_url,
        token=token,
        prompt=prompt,
    )


def run_direct_oac_tool_loop(
    *,
    payload: dict[str, Any],
    client: OpenAI,
    model: str,
    oac_url: str,
    token: str,
    prompt: str,
) -> dict[str, Any]:
    """Use OCI Responses with app-managed OAC MCP tool execution."""
    timeout_seconds = float(payload.get("timeoutSeconds") or 90)
    mcp_session = DirectOacMcpSession(
        oac_url=oac_url,
        token=token,
        timeout_seconds=timeout_seconds,
    )
    mcp_session.initialize()
    oac_tools = mcp_session.list_tools()
    function_tools, tool_name_map = build_function_tools_from_oac_tools(oac_tools)
    if not tool_name_map:
        returned_names = [
            str(tool.get("name") or "<unnamed>")
            for tool in oac_tools
            if isinstance(tool, dict)
        ]
        detail = ", ".join(returned_names) if returned_names else "none"
        raise RuntimeError(
            "OAC MCP returned no allowed callable tools in direct mode. "
            f"Returned tools: {detail}"
        )

    if not bool(payload.get("useHeuristicToolLoop", False)):
        try:
            return run_direct_oac_function_loop(
                payload=payload,
                client=client,
                model=model,
                mcp_session=mcp_session,
                function_tools=function_tools,
                tool_name_map=tool_name_map,
                prompt=prompt,
            )
        except Exception:
            pass

    return run_direct_oac_heuristic_loop(
        payload=payload,
        client=client,
        model=model,
        mcp_session=mcp_session,
        oac_tools=oac_tools,
        tool_name_map=tool_name_map,
        prompt=prompt,
    )


def run_direct_oac_function_loop(
    *,
    payload: dict[str, Any],
    client: OpenAI,
    model: str,
    mcp_session: "DirectOacMcpSession",
    function_tools: list[dict[str, Any]],
    tool_name_map: dict[str, str],
    prompt: str,
) -> dict[str, Any]:
    """Let the model choose OAC tools, execute them locally, and chain outputs."""
    tool_timeline: list[dict[str, Any]] = []
    context = build_input(prompt, payload)
    response = client.responses.create(
        model=model,
        input=context,
        instructions=OAC_ANALYST_INSTRUCTIONS,
        tools=function_tools,
        store=True,
    )

    for _ in range(8):
        calls = pending_function_calls(response, tool_name_map)
        if not calls:
            break

        tool_outputs = []
        for call in calls:
            model_tool_name = str(call.get("name") or "")
            mcp_name = tool_name_map[model_tool_name]
            arguments = parse_function_arguments(call.get("arguments"))
            call_id = str(call.get("call_id") or call.get("id") or "")
            call_response = mcp_session.call_tool(name=mcp_name, arguments=arguments)
            status = "failed" if oac_response_is_error(call_response) else "completed"
            timeline_item = {
                "type": "direct_oac_call",
                "name": model_tool_name,
                "mcpName": mcp_name,
                "status": status,
                "server": "oracle_analytics_direct",
                "arguments": truncate_value(arguments, limit=1600),
                "output": truncate_value(call_response, limit=3200),
                "modelOutput": compact_oac_tool_result_for_model(
                    tool_name=model_tool_name,
                    value=call_response,
                    prompt=prompt,
                ),
            }
            rows = extract_rows_from_oac_value(call_response)
            if (
                rows
                and model_tool_name == "execute_logical_sql"
                and not oac_response_is_error(call_response)
            ):
                timeline_item["rowsPreview"] = rows[:50]
            tool_timeline.append(timeline_item)
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": compact_tool_output_for_model(call_response),
                }
            )

        response = client.responses.create(
            model=model,
            input=tool_outputs,
            previous_response_id=response.id,
            instructions=OAC_ANALYST_INSTRUCTIONS,
            tools=function_tools,
            store=True,
        )

    answer = str(getattr(response, "output_text", "") or "")
    if tool_timeline:
        summary_response = summarize_direct_oac_results(
            client=client,
            model=model,
            prompt=prompt,
            tool_timeline=tool_timeline,
            oac_tools=[],
        )
        response = summary_response
        answer = str(getattr(summary_response, "output_text", "") or "")
    if not answer:
        answer = "The OAC analysis completed, but the model returned no final text."
    answer = sanitize_final_answer(answer)

    chart = build_chart_payload(tool_timeline)
    public_calls = public_tool_timeline(tool_timeline)
    return {
        "mode": "responses-app-managed-mcp",
        "responseId": getattr(response, "id", None),
        "answer": answer,
        "logicalSql": extract_logical_sql(answer, public_calls),
        "toolCalls": public_calls,
        "chart": chart,
        "outputSummary": summarize_response(response),
        "sessionNotes": build_session_notes(answer, public_calls),
    }


def run_direct_oac_heuristic_loop(
    *,
    payload: dict[str, Any],
    client: OpenAI,
    model: str,
    mcp_session: "DirectOacMcpSession",
    oac_tools: list[dict[str, Any]],
    tool_name_map: dict[str, str],
    prompt: str,
) -> dict[str, Any]:
    """Fallback direct flow for providers that cannot chain function calls."""
    tool_timeline: list[dict[str, Any]] = []
    context = build_input(prompt, payload)

    discover_output = execute_direct_oac_step(
        client=client,
        model=model,
        mcp_session=mcp_session,
        oac_tools=oac_tools,
        tool_name_map=tool_name_map,
        model_tool_name="discover_data",
        prompt=prompt,
        context=context,
        prior_outputs=[],
    )
    tool_timeline.append(discover_output)
    prior_outputs = [discover_output]

    if should_describe_data(prompt):
        describe_output = execute_direct_oac_step(
            client=client,
            model=model,
            mcp_session=mcp_session,
            oac_tools=oac_tools,
            tool_name_map=tool_name_map,
            model_tool_name="describe_data",
            prompt=prompt,
            context=context,
            prior_outputs=prior_outputs,
        )
        tool_timeline.append(describe_output)
        prior_outputs.append(describe_output)

    if should_execute_logical_sql(prompt):
        execute_output = execute_direct_oac_step(
            client=client,
            model=model,
            mcp_session=mcp_session,
            oac_tools=oac_tools,
            tool_name_map=tool_name_map,
            model_tool_name="execute_logical_sql",
            prompt=prompt,
            context=context,
            prior_outputs=prior_outputs,
        )
        tool_timeline.append(execute_output)
        prior_outputs.append(execute_output)

    response = summarize_direct_oac_results(
        client=client,
        model=model,
        prompt=prompt,
        tool_timeline=tool_timeline,
        oac_tools=oac_tools,
    )
    answer = str(getattr(response, "output_text", "") or "")
    if not answer:
        answer = "The direct OAC analysis completed, but the model returned no final text."
    answer = sanitize_final_answer(answer)
    chart = build_chart_payload(tool_timeline)
    public_calls = public_tool_timeline(tool_timeline)
    return {
        "mode": "app-managed-mcp",
        "responseId": getattr(response, "id", None),
        "answer": answer,
        "logicalSql": extract_logical_sql(answer, public_calls),
        "toolCalls": public_calls,
        "chart": chart,
        "outputSummary": summarize_response(response),
        "sessionNotes": build_session_notes(answer, public_calls),
    }


def is_demo_chart_prompt(prompt: str) -> bool:
    """Return whether the user requested the local graph rendering demo."""
    lowered = prompt.lower()
    return "demo graph" in lowered or "demo chart" in lowered or "graph demo" in lowered


def is_chart_followup_prompt(prompt: str) -> bool:
    """Return whether the user is asking to visualize the previous result."""
    lowered = prompt.lower()
    return any(
        phrase in lowered
        for phrase in (
            "plot that",
            "plot this",
            "bar chart",
            "make a chart",
            "show a chart",
            "graph it",
            "plot it",
            "visualize it",
            "visualise it",
        )
    )


def valid_chart_payload(value: Any) -> bool:
    """Return whether a previous chart payload can be reused."""
    if not isinstance(value, dict):
        return False
    data = value.get("data")
    value_keys = value.get("valueKeys")
    category_key = value.get("categoryKey")
    return (
        isinstance(category_key, str)
        and bool(category_key)
        and isinstance(value_keys, list)
        and bool(value_keys)
        and isinstance(data, list)
        and bool(data)
    )


def previous_chart_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Return the previous chart payload for chart-only follow-up prompts."""
    chart = payload["previousChart"]
    return {
        "mode": "chart-followup",
        "responseId": None,
        "answer": "Rendered the previous result as a bar chart.",
        "logicalSql": [],
        "toolCalls": [],
        "chart": chart,
        "outputSummary": {"chartRows": len(chart.get("data", []))},
        "sessionNotes": str(payload.get("sessionNotes") or ""),
    }


def demo_chart_response(prompt: str) -> dict[str, Any]:
    """Return deterministic sample rows to verify the React chart path."""
    rows = [
        {"Product Type": "Audio", "Revenue": 184250},
        {"Product Type": "Cameras", "Revenue": 158900},
        {"Product Type": "Computers", "Revenue": 143600},
        {"Product Type": "Mobile Phones", "Revenue": 126450},
        {"Product Type": "Accessories", "Revenue": 98200},
    ]
    return {
        "mode": "demo-chart",
        "responseId": None,
        "answer": (
            "Demo chart rendered from local sample rows. This verifies the React/Recharts graph path only; "
            "no OAC MCP tool or Logical SQL query was executed."
        ),
        "logicalSql": [],
        "toolCalls": [
            {
                "type": "demo",
                "name": "demo_chart",
                "status": "completed",
                "arguments": {"prompt": prompt},
            }
        ],
        "chart": {
            "type": "bar",
            "categoryKey": "Product Type",
            "valueKeys": ["Revenue"],
            "data": rows,
        },
        "outputSummary": {"demoRows": rows},
        "sessionNotes": ["Demo chart only. No Oracle Analytics data was queried."],
    }


def build_openai_client(payload: dict[str, Any]) -> OpenAI:
    """Build an OpenAI-compatible OCI Responses client."""
    base_url = str(payload.get("baseUrl") or os.getenv("GENAI_BASE_URL", "")).strip()
    api_key = str(payload.get("genAiApiKey") or os.getenv("GENAI_API_KEY", "")).strip()
    project_id = str(payload.get("projectId") or os.getenv("GENAI_PROJECT_ID", "")).strip()
    missing = [
        name
        for name, value in (
            ("GENAI_BASE_URL", base_url),
            ("GENAI_API_KEY", api_key),
            ("GENAI_PROJECT_ID", project_id),
        )
        if not value
    ]
    if missing:
        raise ValueError("Missing " + ", ".join(missing))
    return OpenAI(base_url=base_url, api_key=api_key, project=project_id, timeout=180)


def execute_direct_oac_step(
    *,
    client: OpenAI,
    model: str,
    mcp_session: "DirectOacMcpSession",
    oac_tools: list[dict[str, Any]],
    tool_name_map: dict[str, str],
    model_tool_name: str,
    prompt: str,
    context: str,
    prior_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Plan and execute one direct OAC MCP tool call."""
    mcp_name = tool_name_map[model_tool_name]
    tool = find_oac_tool(oac_tools, mcp_name)
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    arguments = default_oac_tool_arguments(
        tool_name=model_tool_name,
        prompt=prompt,
        context=context,
        prior_outputs=prior_outputs,
    )
    allow_repair = arguments is None
    if arguments is None:
        arguments = plan_oac_tool_arguments(
            client=client,
            model=model,
            tool_name=model_tool_name,
            mcp_name=mcp_name,
            schema=schema if isinstance(schema, dict) else {},
            prompt=prompt,
            context=context,
            prior_outputs=prior_outputs,
        )
    try:
        call_response = mcp_session.call_tool(name=mcp_name, arguments=arguments)
    except RuntimeError as exc:
        repaired = repair_oac_tool_arguments(
            client=client,
            model=model,
            tool_name=model_tool_name,
            mcp_name=mcp_name,
            schema=schema if isinstance(schema, dict) else {},
            prompt=prompt,
            context=context,
            prior_outputs=prior_outputs,
            failed_arguments=arguments,
            error=str(exc),
        )
        if repaired != arguments:
            arguments = repaired
            call_response = mcp_session.call_tool(name=mcp_name, arguments=arguments)
        else:
            raise
    if (
        oac_response_is_error(call_response)
        and allow_repair
        and not non_repairable_oac_error(call_response)
    ):
        repaired = repair_oac_tool_arguments(
            client=client,
            model=model,
            tool_name=model_tool_name,
            mcp_name=mcp_name,
            schema=schema if isinstance(schema, dict) else {},
            prompt=prompt,
            context=context,
            prior_outputs=prior_outputs,
            failed_arguments=arguments,
            error=oac_error_text(call_response),
        )
        if repaired != arguments:
            arguments = repaired
            call_response = mcp_session.call_tool(name=mcp_name, arguments=arguments)
    status = "failed" if oac_response_is_error(call_response) else "completed"
    timeline_item = {
        "type": "direct_oac_call",
        "name": model_tool_name,
        "mcpName": mcp_name,
        "status": status,
        "server": "oracle_analytics_direct",
        "arguments": truncate_value(arguments, limit=1600),
        "output": truncate_value(call_response, limit=2600),
        "modelOutput": compact_oac_tool_result_for_model(
            tool_name=model_tool_name,
            value=call_response,
            prompt=prompt,
        ),
    }
    rows = extract_rows_from_oac_value(call_response)
    if (
        rows
        and model_tool_name == "execute_logical_sql"
        and not oac_response_is_error(call_response)
    ):
        timeline_item["rowsPreview"] = rows[:50]
    return timeline_item


def default_oac_tool_arguments(
    *,
    tool_name: str,
    prompt: str,
    context: str,
    prior_outputs: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Return safe defaults for stable OAC MCP tool schemas."""
    if tool_name == "discover_data":
        lowered_prompt = prompt.lower()
        if "datasets only" in lowered_prompt or "only datasets" in lowered_prompt:
            return {"fetchType": "datasets"}
        return {}

    if tool_name == "describe_data":
        # Prefer the dataset/subject area the user actually asked about, matched
        # against real discover_data results. Only fall back to the sample-sales
        # heuristic when nothing was discovered (keeps the old demo working).
        target = match_data_target(prompt, discovered_data_targets(prior_outputs))
        if target:
            return {"datamodelName": target["datamodelName"]}
        subject_area = infer_subject_area(prompt) or infer_subject_area(context)
        if subject_area:
            return {"datamodelName": subject_area}
        return None

    if tool_name == "execute_logical_sql":
        # Match against the prompt/context only; do not scan discovery output,
        # which would let any "Sample Sales" dataset name hijack the query.
        sample_query = known_sample_sales_query(f"{prompt}\n{context}")
        if sample_query:
            return {"query": sample_query, "maxRows": 10}
        return None
    return None


def infer_subject_area(text: str) -> str:
    """Infer the known sample subject area from user/session text."""
    lowered = text.lower()
    if "sample sales lite" in lowered or "sample sales" in lowered:
        return "Sample Sales Lite"
    if "sample targets lite" in lowered or "sample targets" in lowered:
        return "Sample Targets Lite"
    if re.search(r"\bsales\b", lowered):
        return "Sales"

    match = re.search(
        r"(?:subject area|datamodel|data model)\s+['\"]([^'\"]+)['\"]",
        text,
        flags=re.I,
    )
    if match:
        return match.group(1).strip()

    return ""


def discovered_data_targets(prior_outputs: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract selectable (displayName, datamodelName) targets from discover_data.

    Datasets are referenced as XSA('<owner>'.'<name>'); subject areas use their
    own name. This lets describe_data/execute_logical_sql target the dataset the
    user actually asked about instead of a hardcoded sample subject area.
    """
    targets: list[dict[str, str]] = []
    seen: set[str] = set()
    for output in prior_outputs:
        if not isinstance(output, dict) or output.get("name") != "discover_data":
            continue
        parsed = None
        model_out = output.get("modelOutput")
        if isinstance(model_out, str):
            parsed = parse_json_like(model_out)
        if not isinstance(parsed, dict):
            parsed = unwrap_oac_text_json(output.get("output"))
        if not isinstance(parsed, dict):
            continue
        for item in parsed.get("Datasets") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            display = str(item.get("displayName") or "").strip() or name
            if name and display not in seen:
                seen.add(display)
                targets.append({"displayName": display, "datamodelName": f"XSA({name})"})
        for item in parsed.get("SubjectAreas") or []:
            if not isinstance(item, dict):
                continue
            sa = str(item.get("name") or item.get("model") or "").strip()
            if sa and sa not in seen:
                seen.add(sa)
                targets.append({"displayName": sa, "datamodelName": sa})
    return targets


def _fuzzy_term_overlap(a: set[str], b: set[str]) -> int:
    """Count terms in a that match a term in b (exact or 4+ char substring)."""
    score = 0
    for x in a:
        for y in b:
            if x == y or (min(len(x), len(y)) >= 4 and (x in y or y in x)):
                score += 1
                break
    return score


def match_data_target(prompt: str, targets: list[dict[str, str]]) -> dict[str, str] | None:
    """Pick the discovered target whose displayName best matches the prompt.

    Ties (e.g. "Sample Sales" vs "Sample Sales Enriched" vs "Sales History")
    are broken by overlap ratio so the most specific name wins.
    """
    prompt_terms = significant_terms(prompt)
    if not prompt_terms or not targets:
        return None
    best: dict[str, str] | None = None
    best_key: tuple[int, float] = (0, 0.0)
    for target in targets:
        name_terms = significant_terms(target["displayName"])
        score = _fuzzy_term_overlap(prompt_terms, name_terms)
        if score == 0:
            continue
        key = (score, score / max(len(name_terms), 1))
        if key > best_key:
            best_key = key
            best = target
    return best


def known_sample_sales_query(prompt: str) -> str:
    """Return known-good Logical SQL for common Sample Sales demo prompts."""
    lowered = prompt.lower()
    if "sample sales" not in lowered:
        return ""
    if (
        "product" in lowered
        and (
            "selling" in lowered
            or "sold" in lowered
            or "quantity" in lowered
            or "best" in lowered
            or "most" in lowered
        )
    ):
        return (
            'SELECT "Sample Sales Lite"."Products"."Product" AS "Product", '
            '"Sample Sales Lite"."Base Facts"."Billed Quantity" AS "Billed Quantity" '
            'FROM "Sample Sales Lite" '
            'ORDER BY "Billed Quantity" DESC FETCH FIRST 10 ROWS ONLY'
        )
    if "product type" in lowered and "revenue" in lowered:
        return (
            'SELECT "Sample Sales Lite"."Products"."Product Type" AS "Product Type", '
            '"Sample Sales Lite"."Base Facts"."Revenue" AS "Revenue" '
            'FROM "Sample Sales Lite" '
            'ORDER BY "Revenue" DESC FETCH FIRST 10 ROWS ONLY'
        )
    if ("year" in lowered or "per name year" in lowered) and "revenue" in lowered:
        return (
            'SELECT "Sample Sales Lite"."Time"."Per Name Year" AS "Year", '
            '"Sample Sales Lite"."Base Facts"."Revenue" AS "Revenue", '
            '"Sample Sales Lite"."Base Facts"."Billed Quantity" AS "Billed Quantity" '
            'FROM "Sample Sales Lite" '
            'ORDER BY "Year" FETCH FIRST 20 ROWS ONLY'
        )
    if ("lob" in lowered or "line of business" in lowered) and "target" in lowered:
        return (
            'SELECT "Sample Sales Lite"."Products"."LOB" AS "LOB", '
            '"Sample Sales Lite"."Base Facts"."Revenue" AS "Revenue", '
            '"Sample Sales Lite"."Base Facts"."Target Revenue" AS "Target Revenue" '
            'FROM "Sample Sales Lite" '
            'ORDER BY "Revenue" DESC FETCH FIRST 20 ROWS ONLY'
        )
    return ""


def plan_oac_tool_arguments(
    *,
    client: OpenAI,
    model: str,
    tool_name: str,
    mcp_name: str,
    schema: dict[str, Any],
    prompt: str,
    context: str,
    prior_outputs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Ask the model for a plain JSON argument object for one OAC tool."""
    target = match_data_target(prompt, discovered_data_targets(prior_outputs))
    target_hint = (
        f"Selected data source: {target['displayName']}. Reference it in the FROM "
        f"clause as {target['datamodelName']} (quote a subject-area name).\n\n"
        if target
        else ""
    )
    planning_prompt = (
        "Return only a JSON object of arguments for the next Oracle Analytics MCP tool call.\n"
        f"Tool model name: {tool_name}\n"
        f"Actual MCP tool name: {mcp_name}\n"
        f"Tool input schema JSON:\n{json.dumps(schema, indent=2, default=str)[:6000]}\n\n"
        f"User request:\n{prompt}\n\n"
        f"Conversation context:\n{context[:2000]}\n\n"
        f"{target_hint}"
        f"Prior OAC outputs:\n{compact_prior_outputs(prior_outputs)}\n\n"
        "Return only JSON, no markdown. Use an empty object if the schema has no required fields. "
        "For execute_logical_sql, return {\"query\":\"...\",\"maxRows\":N}. "
        f"{OAC_LOGICAL_SQL_RULES} Add aggregations and ORDER BY/FETCH FIRST as appropriate."
    )
    response = client.responses.create(
        model=model,
        input=planning_prompt,
        instructions=(
            "You produce strict JSON objects for Oracle Analytics MCP tool arguments. "
            "Do not include explanations or markdown."
        ),
        store=True,
    )
    return extract_json_object(str(getattr(response, "output_text", "") or "")) or {}


def repair_oac_tool_arguments(
    *,
    client: OpenAI,
    model: str,
    tool_name: str,
    mcp_name: str,
    schema: dict[str, Any],
    prompt: str,
    context: str,
    prior_outputs: list[dict[str, Any]],
    failed_arguments: dict[str, Any],
    error: str,
) -> dict[str, Any]:
    """Ask for corrected arguments after an OAC tool error."""
    repair_prompt = (
        "The Oracle Analytics MCP tool call failed. Return only corrected JSON arguments.\n"
        f"Tool model name: {tool_name}\n"
        f"Actual MCP tool name: {mcp_name}\n"
        f"Tool input schema JSON:\n{json.dumps(schema, indent=2, default=str)[:6000]}\n\n"
        f"Failed arguments:\n{json.dumps(failed_arguments, indent=2, default=str)}\n\n"
        f"Error:\n{error[:2000]}\n\n"
        f"User request:\n{prompt}\n\n"
        f"Context:\n{context[:2000]}\n\n"
        f"Prior OAC outputs:\n{compact_prior_outputs(prior_outputs)}\n\n"
        "Return only JSON, no markdown. For execute_logical_sql, return {\"query\":\"...\",\"maxRows\":N}. "
        f"{OAC_LOGICAL_SQL_RULES}"
    )
    response = client.responses.create(
        model=model,
        input=repair_prompt,
        instructions="Return only a strict JSON object.",
        store=True,
    )
    return extract_json_object(str(getattr(response, "output_text", "") or "")) or failed_arguments


def summarize_direct_oac_results(
    *,
    client: OpenAI,
    model: str,
    prompt: str,
    tool_timeline: list[dict[str, Any]],
    oac_tools: list[dict[str, Any]],
) -> Any:
    """Summarize direct OAC results with a normal text model call."""
    tool_summary = [
        {
            "name": tool.get("name"),
            "description": str(tool.get("description") or "")[:500],
        }
        for tool in oac_tools
    ]
    compact_timeline = []
    for call in tool_timeline:
        compact_timeline.append(
            {
                "name": call.get("name"),
                "status": call.get("status"),
                "arguments": call.get("arguments"),
                "rowsPreview": call.get("rowsPreview"),
                "result": call.get("modelOutput") or truncate_value(call.get("output"), limit=3000),
            }
        )
    summary_input = (
        f"User request:\n{prompt}\n\n"
        "Available Oracle Analytics MCP tools:\n"
        f"{json.dumps(tool_summary, indent=2, default=str)}\n\n"
        "Oracle Analytics tool results:\n"
        f"{json.dumps(compact_timeline, indent=2, default=str)[:26000]}\n\n"
        "Write the final business answer. Include Logical SQL if it appears in the tool results. "
        "If the user asks what they can do, list the tools, available subject areas, and concrete test questions. "
        "If only discover_data ran, do not invent Logical SQL examples; give natural-language test questions instead. "
        "If execution failed or no rows were returned, say that directly and explain the useful next step. "
        "Use ONLY data, column names, and values that appear in the tool results above. Never invent rows, "
        "columns, categories, counts, tables, or additional tool calls. If describe_data returned empty tables "
        "or execute_logical_sql failed, state that plainly and do not present any results table. "
        "Do not print raw MCP JSON, tool-call JSON, or internal timeline objects in the answer. "
        "Do not narrate tool planning. Never write phrases such as 'we need to call', 'we have to issue tool call', "
        "'now execute', 'let us call', or 'proceed'. Output only the final user-facing answer."
    )
    return client.responses.create(
        model=model,
        input=summary_input,
        instructions=OAC_ANALYST_INSTRUCTIONS,
        store=True,
    )


def compact_prior_outputs(outputs: list[dict[str, Any]]) -> str:
    """Return compact prior tool output JSON."""
    if not outputs:
        return "[]"
    compact = []
    for output in outputs:
        item = {
            "name": output.get("name"),
            "status": output.get("status"),
            "arguments": output.get("arguments"),
            "output": output.get("modelOutput") or output.get("output"),
        }
        compact.append(item)
    return json.dumps(compact, indent=2, default=str)[:18000]


def extract_json_object(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from model text."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.I)
        stripped = re.sub(r"\s*```$", "", stripped)
    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.S)
    if match:
        candidates.append(match.group(0))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def find_oac_tool(oac_tools: list[dict[str, Any]], mcp_name: str) -> dict[str, Any]:
    """Find one tool by exact MCP name."""
    for tool in oac_tools:
        if str(tool.get("name") or "") == mcp_name:
            return tool
    return {}


def should_describe_data(prompt: str) -> bool:
    """Return whether the direct flow should describe a data model."""
    lowered = prompt.lower()
    if is_capability_or_greeting_prompt(lowered):
        return False
    if any(phrase in lowered for phrase in ("do not describe", "don't describe", "only discover", "discover only")):
        return False
    # If we are going to run a query, we must describe first to get columns.
    if should_execute_logical_sql(prompt):
        return True
    return any(
        phrase in lowered
        for phrase in (
            "describe",
            "using sample",
            "sample sales",
            "sample targets",
            "columns",
            "measures",
            "dimensions",
            "metadata",
            "plot",
            "chart",
            "graph",
        )
    )


def should_execute_logical_sql(prompt: str) -> bool:
    """Return whether the direct flow should execute Logical SQL."""
    lowered = prompt.lower()
    if is_capability_or_greeting_prompt(lowered):
        return False
    if any(
        phrase in lowered
        for phrase in ("do not execute", "don't execute", "do not run", "don't run", "only discover", "discover only")
    ):
        return False
    execution_words = (
        "run",
        "execute",
        "analyze",
        "summarize",
        "show",
        "what are",
        "what is",
        "which",
        "top",
        "most",
        "best",
        "plot",
        "chart",
        "graph",
        "visualize",
        "visualise",
        "compare",
        "break down",
        "breakdown",
        "by ",
        "per ",
        "each",
        "how many",
        "number of",
        "count",
        "average",
        "total",
        "sum ",
        "distribution",
        "trend",
        "rank",
        "highest",
        "lowest",
        "logical sql",
    )
    return any(word in lowered for word in execution_words) or looks_like_analysis_prompt(lowered)


def looks_like_analysis_prompt(lowered_prompt: str) -> bool:
    """Return whether text asks for a data result rather than capabilities."""
    metric_terms = (
        "sales",
        "revenue",
        "product",
        "products",
        "selling",
        "sold",
        "quantity",
        "amount",
        "category",
        "target",
        "department",
        "leave",
        "month",
        "year",
    )
    intent_terms = (
        "what",
        "which",
        "show",
        "plot",
        "chart",
        "graph",
        "top",
        "most",
        "best",
        "by ",
        "compare",
        "summarize",
        "summary",
    )
    return any(term in lowered_prompt for term in metric_terms) and any(
        term in lowered_prompt for term in intent_terms
    )


def is_capability_or_greeting_prompt(lowered_prompt: str) -> bool:
    """Return whether the user is asking for capabilities, not analysis."""
    compact = lowered_prompt.strip()
    if compact in {"hi", "hello", "hey"}:
        return True
    return any(
        phrase in compact
        for phrase in (
            "what can i do",
            "what can this mcp",
            "what can the mcp",
            "what can this server",
            "capabilities",
            "available subject areas",
            "discover available",
        )
    )


class DirectOacMcpSession:
    """Minimal Streamable HTTP MCP client for OAC."""

    # The MCP version we ask for; the server may negotiate a different one back.
    REQUESTED_PROTOCOL_VERSION = "2025-06-18"

    def __init__(self, *, oac_url: str, token: str, timeout_seconds: float) -> None:
        self.oac_url = normalize_oac_mcp_url(oac_url)
        self.timeout_seconds = timeout_seconds
        self.session_id: str | None = None
        self.protocol_version: str | None = None
        self.http = requests.Session()
        self.http.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            }
        )

    def initialize(self) -> None:
        """Run the full MCP handshake: initialize, then notifications/initialized.

        The Streamable HTTP spec requires the client to send a
        notifications/initialized message after a successful initialize before
        it may issue any other request (tools/list, tools/call, ...). OAC, like
        Claude Desktop's MCP client, rejects or returns empty results for those
        requests when the notification is skipped, so we must send it here.
        """
        response = self.post(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": self.REQUESTED_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "react-oac-direct", "version": "1.0"},
                },
            }
        )
        self.session_id = response.get("session_id") or self.session_id
        # Use the version the server negotiated for the MCP-Protocol-Version
        # header on all later requests; fall back to what we requested.
        result = response.get("body", {}).get("result", {})
        if isinstance(result, dict):
            self.protocol_version = (
                result.get("protocolVersion") or self.REQUESTED_PROTOCOL_VERSION
            )
        else:
            self.protocol_version = self.REQUESTED_PROTOCOL_VERSION
        # Confirm initialization so the server marks the session ready.
        self.post(
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            allow_empty=True,
        )

    def list_tools(self) -> list[dict[str, Any]]:
        """Return OAC MCP tools."""
        response = self.post({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = response.get("body", {}).get("result", {}).get("tools", [])
        if not tools:
            original_session_id = self.session_id
            self.session_id = None
            try:
                response = self.post({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
                tools = response.get("body", {}).get("result", {}).get("tools", [])
            finally:
                self.session_id = self.session_id or original_session_id
        if not isinstance(tools, list):
            return []
        return [tool for tool in tools if isinstance(tool, dict)]

    def call_tool(self, *, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call one OAC MCP tool."""
        response = self.post(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            }
        )
        return response.get("body", {})

    def post(
        self, payload: dict[str, Any], *, allow_empty: bool = False
    ) -> dict[str, Any]:
        """Send one JSON-RPC request to OAC MCP."""
        headers = {}
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        if self.protocol_version:
            headers["MCP-Protocol-Version"] = self.protocol_version
        response = self.http.post(
            self.oac_url,
            json=payload,
            headers=headers,
            timeout=self.timeout_seconds,
            allow_redirects=False,
        )
        if response.is_redirect:
            raise RuntimeError(
                "OAC MCP returned an HTTP redirect (likely to the OAC login UI) "
                "instead of JSON-RPC. Use the endpoint ending in /api/mcp, not "
                "/ui/api/mcp."
            )
        if response.status_code >= 400:
            raise RuntimeError(
                f"OAC MCP HTTP {response.status_code}: {response.text[:2000]}"
            )
        body = parse_mcp_body(response.text, allow_empty=allow_empty)
        self.session_id = response.headers.get("Mcp-Session-Id") or self.session_id
        return {"body": body, "session_id": self.session_id}


def build_function_tools_from_oac_tools(
    oac_tools: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Convert MCP tool schemas into Responses function tools.

    Returns:
        A tuple of function tool definitions and model-name -> MCP-name mapping.
    """
    function_tools = []
    tool_name_map = {}
    for tool in oac_tools:
        mcp_name = str(tool.get("name") or "").strip()
        model_name = normalize_oac_tool_name(mcp_name)
        if model_name not in OAC_ALLOWED_TOOLS:
            continue
        parameters = tool.get("inputSchema") or tool.get("input_schema") or {}
        if not isinstance(parameters, dict):
            parameters = {}
        parameters = normalize_function_parameters(parameters)
        tool_name_map[model_name] = mcp_name
        function_tools.append(
            {
                "type": "function",
                "name": model_name,
                "description": str(tool.get("description") or f"Call OAC {model_name}."),
                "parameters": parameters,
            }
        )
    return function_tools, tool_name_map


def normalize_oac_tool_name(name: str) -> str:
    """Map OAC server-prefixed tool names to stable model-facing names."""
    name = name.strip()
    for allowed in OAC_ALLOWED_TOOLS:
        if name == allowed or name.endswith(f"-{allowed}") or name.endswith(f"_{allowed}"):
            return allowed
    return name


def normalize_function_parameters(schema: dict[str, Any]) -> dict[str, Any]:
    """Ensure a JSON Schema object is acceptable as function parameters."""
    normalized = json.loads(json.dumps(schema, default=str))
    normalized.setdefault("type", "object")
    normalized.setdefault("properties", {})
    if normalized.get("type") != "object":
        normalized = {"type": "object", "properties": {}}
    return normalized


def parse_function_arguments(raw_arguments: Any) -> dict[str, Any]:
    """Parse model function-call arguments."""
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not raw_arguments:
        return {}
    try:
        parsed = json.loads(str(raw_arguments))
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def pending_function_calls(
    response: Any, tool_name_map: dict[str, str]
) -> list[dict[str, Any]]:
    """Return model function calls that map to OAC MCP tools."""
    calls = []
    for item in getattr(response, "output", []) or []:
        plain = to_plain(item)
        if plain.get("type") != "function_call":
            continue
        if plain.get("name") not in tool_name_map:
            continue
        calls.append(plain)
    return calls


def public_tool_timeline(tool_timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Strip internal model-only context before returning tool calls to the UI."""
    public_calls = []
    for call in tool_timeline:
        public_calls.append(
            {
                key: value
                for key, value in call.items()
                if not key.startswith("_") and key not in {"modelOutput"}
            }
        )
    return public_calls


def compact_oac_tool_result_for_model(
    *, tool_name: str, value: Any, prompt: str
) -> str:
    """Return a compact, model-facing view of an OAC tool response."""
    parsed = unwrap_oac_text_json(value)
    if tool_name == "discover_data":
        if isinstance(parsed, dict) and ("SubjectAreas" in parsed or "Datasets" in parsed):
            compact: dict[str, Any] = {}
            # Keep BOTH governed subject areas and XSA datasets. Dropping
            # Datasets here made the model believe only "Sales" existed and
            # blind to datasets like "LA Crime Data".
            for key in ("SubjectAreas", "Datasets"):
                items = parsed.get(key)
                if isinstance(items, list):
                    compact[key] = [
                        {
                            "name": item.get("name"),
                            "displayName": item.get("displayName"),
                            "description": item.get("description"),
                            "model": item.get("model"),
                            "type": item.get("type"),
                        }
                        for item in items
                        if isinstance(item, dict)
                    ]
            if compact:
                return json.dumps(compact, ensure_ascii=True, default=str)

    if tool_name == "describe_data" and isinstance(parsed, dict):
        compact = compact_describe_metadata(parsed, prompt=prompt)
        if compact:
            return json.dumps(compact, ensure_ascii=True, default=str)

    if tool_name == "execute_logical_sql":
        rows = extract_rows_from_oac_value(value)
        if rows and not oac_response_is_error(value):
            return json.dumps({"rows": rows[:50]}, ensure_ascii=True, default=str)
        return compact_tool_output_for_model(value, limit=5000)

    return compact_tool_output_for_model(value, limit=12000)


def unwrap_oac_text_json(value: Any) -> Any:
    """Unwrap MCP content text that itself contains JSON."""
    if isinstance(value, dict):
        result = value.get("result")
        if isinstance(result, dict):
            content = result.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and isinstance(item.get("text"), str):
                        parsed = parse_json_like(item["text"])
                        if parsed is not None:
                            return parsed
        for key in ("body", "output", "content", "text"):
            if key in value:
                parsed = unwrap_oac_text_json(value[key])
                if parsed is not None:
                    return parsed
    if isinstance(value, list):
        for item in value:
            parsed = unwrap_oac_text_json(item)
            if parsed is not None:
                return parsed
    if isinstance(value, str):
        parsed = parse_json_like(value)
        if parsed is not None:
            return parsed
    return value


def compact_describe_metadata(value: dict[str, Any], *, prompt: str) -> dict[str, Any]:
    """Compact OAC describe_data metadata into SQL-grounding context."""
    tables = value.get("tables")
    if not isinstance(tables, list):
        return {}

    prompt_terms = significant_terms(prompt)
    compact_tables = []
    for table in tables:
        if not isinstance(table, dict):
            continue
        columns = table.get("columns") if isinstance(table.get("columns"), list) else []
        primary = []  # measures and columns that match the prompt
        secondary = []  # remaining dimensions / attributes
        for column in columns:
            if not isinstance(column, dict):
                continue
            name = str(column.get("name") or column.get("displayName") or "")
            display_name = str(column.get("displayName") or name)
            column_type = str(column.get("columnType") or "")
            aggregation = str(column.get("aggregation") or "")
            fq_name = str(column.get("fullyQualifiedName") or "")
            description = str(column.get("description") or "")
            compact_column = {
                "name": name,
                "displayName": display_name,
                "columnType": column_type,
                "dataType": column.get("dataType"),
                "aggregation": aggregation,
                "fullyQualifiedName": fq_name,
            }
            prioritized = (
                column_type.lower() == "measure"
                or bool(aggregation and aggregation.lower() not in {"none", "istimedimension"})
                or any(term in f"{name} {display_name} {description}".lower() for term in prompt_terms)
            )
            (primary if prioritized else secondary).append(compact_column)

        # Keep dimensions/attributes too (most relevant first). Previously only
        # measures and prompt-matching columns survived, so the model wrongly
        # concluded a dataset had no groupable column (e.g. "Area Name").
        compact_columns = (primary + secondary)[:60]

        compact_tables.append(
            {
                "fullQualifiedName": table.get("fullQualifiedName"),
                "name": table.get("name"),
                "columns": compact_columns,
            }
        )

    return {
        "instruction": (
            "Use these exact Oracle Analytics fullyQualifiedName values when building Logical SQL. "
            "Do not invent physical tables, joins, or aliases."
        ),
        "tables": compact_tables[:12],
    }


def significant_terms(text: str) -> set[str]:
    """Return prompt terms useful for selecting metadata columns."""
    terms = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_]{2,}", text.lower()))
    stop = {
        "using",
        "show",
        "include",
        "logical",
        "sql",
        "used",
        "result",
        "results",
        "summarize",
        "summary",
        "chart",
        "return",
        "data",
        "top",
    }
    return {term for term in terms if term not in stop}


def oac_response_is_error(value: Any) -> bool:
    """Return whether an OAC MCP tool response indicates a tool-level error."""
    if isinstance(value, dict):
        result = value.get("result")
        if isinstance(result, dict) and result.get("isError") is True:
            return True
        if value.get("isError") is True or value.get("error"):
            return True
    text = json.dumps(value, ensure_ascii=True, default=str)
    return '"isError": true' in text or "Tool dispatch failed" in text


def oac_error_text(value: Any) -> str:
    """Return compact OAC error text for repair prompts."""
    text = json.dumps(value, ensure_ascii=True, default=str)
    return text[:3000]


def non_repairable_oac_error(value: Any) -> bool:
    """Return whether retrying SQL text is unlikely to fix the OAC failure."""
    text = oac_error_text(value)
    return "NQ_SESSION.SAMPLEAPPDIR" in text or "session variable" in text.lower()


def build_chart_payload(tool_timeline: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Build a small Recharts-friendly payload from the last SQL result."""
    rows: list[dict[str, Any]] = []
    for call in reversed(tool_timeline):
        if call.get("name") != "execute_logical_sql":
            continue
        preview = call.get("rowsPreview")
        if isinstance(preview, list):
            rows = [row for row in preview if isinstance(row, dict)]
        if not rows:
            rows = extract_rows_from_oac_value(call.get("output"))
        if rows:
            break
    if not rows:
        return None

    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    if len(columns) < 2:
        return None

    numeric_keys = [
        key for key in columns if any(is_number(row.get(key)) for row in rows)
    ]
    if not numeric_keys:
        return None
    category_keys = [key for key in columns if key not in numeric_keys]
    category_key = category_keys[0] if category_keys else columns[0]
    value_keys = [key for key in numeric_keys if key != category_key][:3]
    if not value_keys:
        return None

    chart_rows = []
    for index, row in enumerate(rows[:20], start=1):
        chart_row = {category_key: str(row.get(category_key) or f"Row {index}")}
        for key in value_keys:
            value = coerce_number(row.get(key))
            chart_row[key] = value if value is not None else 0
        chart_rows.append(chart_row)

    return {
        "type": "bar",
        "title": "OAC result preview",
        "categoryKey": category_key,
        "valueKeys": value_keys,
        "data": chart_rows,
    }


def extract_rows_from_oac_value(value: Any, *, depth: int = 0) -> list[dict[str, Any]]:
    """Extract row-shaped data from common OAC MCP response envelopes."""
    if depth > 8 or value is None:
        return []

    if isinstance(value, str):
        parsed = parse_json_like(value)
        if parsed is not None:
            rows = extract_rows_from_oac_value(parsed, depth=depth + 1)
            if rows:
                return rows
        return parse_markdown_table(value)

    if isinstance(value, list):
        text_blocks = [
            item.get("text")
            for item in value
            if isinstance(item, dict) and isinstance(item.get("text"), str)
        ]
        for text in text_blocks:
            rows = extract_rows_from_oac_value(text, depth=depth + 1)
            if rows:
                return rows
        dict_rows = rows_from_dict_list(value)
        if dict_rows:
            return dict_rows
        for item in value:
            rows = extract_rows_from_oac_value(item, depth=depth + 1)
            if rows:
                return rows
        return []

    if not isinstance(value, dict):
        return []

    table_rows = rows_from_table_content(value)
    if table_rows:
        return table_rows

    column_rows = rows_from_columns_and_values(value)
    if column_rows:
        return column_rows

    # OAC execute_logical_sql returns {"metadata": ..., "batches": [{"data": [...]}]}.
    # Flatten the batch data rows before the generic fallback, otherwise the
    # batch wrapper objects get mistaken for the result rows.
    batch_rows = rows_from_batches(value)
    if batch_rows:
        return batch_rows

    for key in (
        "rows",
        "data",
        "records",
        "items",
        "result",
        "results",
        "resultSet",
        "content",
        "body",
        "output",
        "text",
    ):
        if key in value:
            rows = extract_rows_from_oac_value(value[key], depth=depth + 1)
            if rows:
                return rows

    for nested in value.values():
        rows = extract_rows_from_oac_value(nested, depth=depth + 1)
        if rows:
            return rows
    return []


def clean_oac_column_key(key: str) -> str:
    """Strip the XSA/folder prefix OAC adds to unaliased result columns.

    e.g. XSA('owner'.'LA Crime Data')."folder::crime_data"."Area Name" -> Area Name
    """
    text = str(key)
    quoted = re.findall(r'"([^"]+)"', text)
    if quoted:
        return quoted[-1]
    return text.rsplit(".", 1)[-1].strip('"')


def rows_from_batches(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten OAC streaming result batches into row dictionaries."""
    batches = value.get("batches")
    if not isinstance(batches, list):
        return []
    rows: list[dict[str, Any]] = []
    for batch in batches:
        if not isinstance(batch, dict):
            continue
        data = batch.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item:
                    rows.append(
                        {clean_oac_column_key(key): coerce_cell(cell) for key, cell in item.items()}
                    )
    return rows


def rows_from_dict_list(value: list[Any]) -> list[dict[str, Any]]:
    """Return normalized rows when a list already contains row dictionaries."""
    rows = [item for item in value if isinstance(item, dict)]
    if not rows or len(rows) != len(value):
        return []
    return [
        {str(key): coerce_cell(cell) for key, cell in row.items()}
        for row in rows
        if len(row) >= 2
    ]


def rows_from_table_content(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert MCP table content with array rows into row dictionaries."""
    if value.get("type") != "table":
        return []
    raw_rows = value.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        return []
    if not all(isinstance(row, list) for row in raw_rows):
        return []

    raw_columns = value.get("columns") or value.get("headers") or value.get("metadata")
    columns: list[str] = []
    if isinstance(raw_columns, list):
        for index, column in enumerate(raw_columns, start=1):
            if isinstance(column, dict):
                name = column.get("name") or column.get("displayName") or column.get("label")
            else:
                name = column
            columns.append(str(name or f"Column {index}"))
    if not columns:
        width = max(len(row) for row in raw_rows)
        columns = [f"Column {index}" for index in range(1, width + 1)]

    rows = []
    for raw_row in raw_rows:
        row = {}
        for index, column in enumerate(columns):
            row[column] = coerce_cell(raw_row[index]) if index < len(raw_row) else None
        if len(row) >= 2:
            rows.append(row)
    return rows


def rows_from_columns_and_values(value: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert {"columns": [...], "rows": [[...]]} style payloads."""
    raw_columns = (
        value.get("columns")
        or value.get("columnNames")
        or value.get("headers")
        or value.get("fields")
    )
    raw_rows = value.get("rows") or value.get("values") or value.get("data")
    if not isinstance(raw_columns, list) or not isinstance(raw_rows, list):
        return []
    if not raw_rows or not all(isinstance(row, list) for row in raw_rows):
        return []

    columns = []
    for index, column in enumerate(raw_columns, start=1):
        if isinstance(column, dict):
            name = (
                column.get("name")
                or column.get("displayName")
                or column.get("columnName")
                or column.get("label")
                or f"Column {index}"
            )
        else:
            name = column
        columns.append(str(name))

    rows = []
    for raw_row in raw_rows:
        row = {}
        for index, column in enumerate(columns):
            row[column] = coerce_cell(raw_row[index]) if index < len(raw_row) else None
        if len(row) >= 2:
            rows.append(row)
    return rows


def parse_json_like(value: str) -> Any:
    """Parse a JSON string or the first JSON object/array inside a string."""
    text = value.strip()
    candidates = [text]
    match = re.search(r"(\{.*\}|\[.*\])", text, flags=re.S)
    if match:
        candidates.append(match.group(1))
    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def parse_markdown_table(value: str) -> list[dict[str, Any]]:
    """Parse a simple markdown table into rows."""
    lines = [line.strip() for line in value.splitlines() if "|" in line]
    if len(lines) < 3:
        return []
    header_index = -1
    for index in range(len(lines) - 1):
        if re.fullmatch(
            r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?",
            lines[index + 1],
        ):
            header_index = index
            break
    if header_index < 0:
        return []
    headers = split_markdown_row(lines[header_index])
    if len(headers) < 2:
        return []
    rows = []
    for line in lines[header_index + 2 :]:
        cells = split_markdown_row(line)
        if len(cells) < 2:
            continue
        rows.append(
            {
                headers[index]: coerce_cell(cells[index])
                if index < len(cells)
                else None
                for index in range(len(headers))
            }
        )
    return rows


def split_markdown_row(line: str) -> list[str]:
    """Split one markdown table row."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def coerce_cell(value: Any) -> Any:
    """Keep categories readable while converting numeric-looking cells."""
    number = coerce_number(value)
    return number if number is not None else value


def coerce_number(value: Any) -> int | float | None:
    """Return a number when a value is numeric or numeric-looking."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        normalized = normalized.replace("$", "").replace("%", "")
        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", normalized):
            number = float(normalized)
            return int(number) if number.is_integer() else number
    return None


def is_number(value: Any) -> bool:
    """Return whether a value can be plotted as a number."""
    return coerce_number(value) is not None


def compact_tool_output_for_model(value: Any, *, limit: int = 14000) -> str:
    """Serialize and cap tool output before returning it to the model."""
    text = json.dumps(value, ensure_ascii=True, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n...<OAC tool output truncated; ask for a narrower query if needed>"


def parse_mcp_body(text: str, *, allow_empty: bool) -> dict[str, Any]:
    """Parse JSON or text/event-stream JSON-RPC bodies."""
    stripped = text.strip()
    if not stripped:
        if allow_empty:
            return {}
        raise RuntimeError("OAC MCP returned an empty response body.")
    if stripped.startswith("event:") or "\ndata:" in stripped or stripped.startswith("data:"):
        data_lines = [
            line.removeprefix("data:").strip()
            for line in stripped.splitlines()
            if line.startswith("data:")
        ]
        if not data_lines:
            if allow_empty:
                return {}
            raise RuntimeError(f"OAC MCP SSE response had no data lines: {stripped[:500]}")
        stripped = "\n".join(data_lines)
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        preview = stripped[:500]
        if "<html" in preview.lower() or "oauth2/v1/authorize" in preview:
            raise RuntimeError(
                "OAC MCP returned an HTML login/redirect page instead of JSON-RPC. "
                "Use the endpoint ending in /api/mcp and a fresh token for that exact OAC host."
            ) from exc
        raise RuntimeError(f"OAC MCP returned non-JSON response: {preview}") from exc


def resolve_oac_token(payload: dict[str, Any]) -> str:
    """Resolve an OAC access token without requiring a manual paste.

    Priority:
    1. Token pasted in the UI (payload "accessToken").
    2. The downloaded tokens.json refresh flow, which auto-renews the ~1 hour
       access token so the demo keeps working without re-pasting.
    3. OAC_ACCESS_TOKEN / MCP_BEARER_TOKEN from the environment.
    """
    manual_token = clean_bearer_token(str(payload.get("accessToken") or ""))
    if manual_token:
        return manual_token
    file_token = token_from_tokens_file()
    if file_token:
        return file_token
    env_token = clean_bearer_token(
        os.getenv("OAC_ACCESS_TOKEN") or os.getenv("MCP_BEARER_TOKEN") or ""
    )
    if env_token:
        return env_token
    raise ValueError(
        "No OAC access token available. Paste a token in the UI, set "
        "OAC_ACCESS_TOKEN/MCP_BEARER_TOKEN, or place a downloaded tokens.json "
        "next to package.json (the app root)."
    )


def oac_tokens_file_path() -> Path:
    """Return the configured downloaded-tokens path."""
    configured = os.getenv("OAC_TOKENS_FILE")
    return Path(configured).expanduser() if configured else DEFAULT_TOKENS_FILE


def oac_token_refresh_url() -> str:
    """Return the OAC token refresh endpoint for the configured instance."""
    explicit = os.getenv("OAC_TOKEN_REFRESH_URL", "").strip()
    if explicit:
        return explicit
    mcp_url = normalize_oac_mcp_url(os.getenv("OAC_MCP_SERVER_URL", DEFAULT_OAC_MCP_URL))
    parsed = urlparse(mcp_url)
    if parsed.scheme and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}/api/dv/api/v1/tokens/token/refresh"
    return DEFAULT_OAC_TOKEN_REFRESH_URL


def token_is_expiring(token: str, *, skew_seconds: int = 600) -> bool:
    """Return True if the JWT has no readable exp or expires within the skew.

    OAC's refresh endpoint authenticates the refresh request with the access
    token in the Authorization header, so a refresh only works while the access
    token is still valid. We use a wide 10 minute skew so any request late in
    the hour refreshes well before the token lapses; once it fully expires the
    only fix is downloading a fresh tokens.json.
    """
    claims = decode_jwt_claims(token)
    exp = claims.get("exp") if isinstance(claims, dict) else None
    if not isinstance(exp, (int, float)):
        return True
    return (exp - time.time()) <= skew_seconds


def token_from_tokens_file() -> str:
    """Return a usable access token from tokens.json, refreshing if needed."""
    path = oac_tokens_file_path()
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    access = clean_bearer_token(str(data.get("accessToken") or ""))
    refresh = str(data.get("refreshToken") or "").strip()
    # Use the stored token directly while it is still comfortably valid.
    if access and not token_is_expiring(access):
        return access
    # Otherwise try the downloaded-token refresh flow and persist the result.
    if access and refresh:
        try:
            from refresh_oac_tokens import refresh_oac_tokens_from_file

            refreshed = refresh_oac_tokens_from_file(
                token_file=path,
                refresh_url=oac_token_refresh_url(),
                save=True,
            )
            new_access = clean_bearer_token(str(refreshed.get("accessToken") or ""))
            if new_access:
                return new_access
        except Exception:  # pylint: disable=broad-exception-caught
            pass
    # Last resort: return whatever we have so initialize can report a clear 401.
    return access


def diagnostic_for_oac_status(status_code: int) -> str:
    """Return a concise human diagnostic for OAC MCP auth failures."""
    if status_code == 401:
        return "The OAC access token is missing, expired, malformed, or not accepted by this OAC instance."
    if status_code == 403:
        return (
            "OAC rejected the token for this MCP endpoint. Use a freshly refreshed "
            "OAC access token from this exact OAC instance."
        )
    return "Check the OAC MCP URL, token, and network reachability."


def token_failure_detail(payload: dict[str, Any], token: str) -> str:
    """Return a non-secret token diagnostic for auth errors."""
    source = effective_token_source(payload)
    detail = f"Token source used: {source}."
    claims = decode_jwt_claims(token)
    audience_detail = token_audience_detail(payload, claims)
    exp = claims.get("exp") if isinstance(claims, dict) else None
    if isinstance(exp, (int, float)):
        remaining = int(exp - time.time())
        if remaining <= 0:
            minutes = max(1, abs(remaining) // 60)
            return f"{detail} JWT is expired by about {minutes} minute(s). Paste a fresh OAC access token."
        minutes = max(1, remaining // 60)
        return (
            f"{detail} JWT expires in about {minutes} minute(s). {audience_detail} "
            "If OAC still rejects it, refresh/download a new token from this exact OAC instance."
        )
    return f"{detail} Could not read JWT expiry. {audience_detail} Paste a fresh OAC access token."


def token_diagnostics(payload: dict[str, Any], token: str) -> dict[str, Any]:
    """Return non-secret token diagnostics for the UI."""
    claims = decode_jwt_claims(token)
    exp = claims.get("exp") if isinstance(claims, dict) else None
    remaining_seconds = int(exp - time.time()) if isinstance(exp, (int, float)) else None
    expected_host = urlparse(
        normalize_oac_mcp_url(str(payload.get("oacMcpUrl") or os.getenv("OAC_MCP_SERVER_URL") or DEFAULT_OAC_MCP_URL))
    ).netloc.lower()
    raw_aud = claims.get("aud") if isinstance(claims, dict) else None
    audiences = raw_aud if isinstance(raw_aud, list) else [raw_aud] if raw_aud else []
    audience_hosts = []
    for audience in audiences:
        parsed = urlparse(str(audience))
        host = (parsed.netloc or str(audience)).lower()
        if host:
            audience_hosts.append(host)
    return {
        "source": effective_token_source(payload),
        "jwtReadable": bool(claims),
        "secondsUntilExpiry": remaining_seconds,
        "expired": remaining_seconds is not None and remaining_seconds <= 0,
        "expectedOacHost": expected_host,
        "audienceMatchesOacHost": expected_host in audience_hosts if audience_hosts else None,
        "audienceHosts": audience_hosts[:5],
        "subject": claims.get("sub") if isinstance(claims, dict) else None,
    }


def effective_token_source(payload: dict[str, Any]) -> str:
    """Return which OAC token source resolve_oac_token would actually use."""
    if clean_bearer_token(str(payload.get("accessToken") or "")):
        return "manual"
    if oac_tokens_file_path().exists():
        return "tokens.json"
    if (os.getenv("OAC_ACCESS_TOKEN") or os.getenv("MCP_BEARER_TOKEN") or "").strip():
        return "environment"
    return "manual"


def token_audience_detail(payload: dict[str, Any], claims: dict[str, Any]) -> str:
    """Return a non-secret diagnostic about token audience vs OAC host."""
    oac_url = normalize_oac_mcp_url(str(payload.get("oacMcpUrl") or os.getenv("OAC_MCP_SERVER_URL") or DEFAULT_OAC_MCP_URL))
    expected_host = urlparse(oac_url).netloc.lower()
    raw_aud = claims.get("aud") if isinstance(claims, dict) else None
    audiences = raw_aud if isinstance(raw_aud, list) else [raw_aud] if raw_aud else []
    audience_hosts = []
    for audience in audiences:
        parsed = urlparse(str(audience))
        host = (parsed.netloc or str(audience)).lower()
        if host:
            audience_hosts.append(host)
    if not expected_host or not audience_hosts:
        return ""
    if expected_host in audience_hosts:
        return "JWT audience matches the OAC host."
    return (
        "JWT audience does not include the configured OAC host "
        f"({expected_host}). The token may be from a different OAC instance."
    )


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Decode JWT claims without verifying the signature."""
    parts = clean_bearer_token(token).split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1] + "=" * ((4 - len(parts[1]) % 4) % 4)
    try:
        decoded = base64.urlsafe_b64decode(payload.encode("ascii"))
        parsed = json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def build_input(prompt: str, payload: dict[str, Any]) -> str:
    """Build a compact user turn with optional session notes."""
    notes = str(payload.get("sessionNotes") or "").strip()
    if not notes:
        return prompt
    return (
        f"Session context from prior turns:\n{notes[:2000]}\n\n"
        f"Current user request:\n{prompt}"
    )


def summarize_response(response: Any) -> list[dict[str, Any]]:
    """Return a redacted, compact summary of response output items."""
    summary = []
    for item in getattr(response, "output", []) or []:
        plain = to_plain(item)
        summary.append(
            {
                "type": plain.get("type"),
                "name": plain.get("name") or plain.get("tool_name"),
                "status": plain.get("status"),
                "server": plain.get("server_label"),
                "id": plain.get("id"),
            }
        )
    return summary


def build_session_notes(answer: str, tool_calls: list[dict[str, Any]]) -> str:
    """Build compact notes for the next turn."""
    tool_names = [call.get("name") for call in tool_calls if call.get("name")]
    sql = extract_logical_sql(answer, tool_calls)
    notes = []
    if tool_names:
        notes.append("OAC tools used: " + ", ".join(tool_names[-6:]))
    if sql:
        notes.append("Last Logical SQL:\n" + sql[-1][:1200])
    if answer:
        notes.append("Last answer summary:\n" + answer[:1200])
    return "\n\n".join(notes)


def _json_object_end(text: str, start: int) -> int:
    """Return the index just past a balanced JSON object at text[start], or -1."""
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    return -1


def _looks_like_tool_json(span: str) -> bool:
    """Return whether a JSON object span is a leaked tool-call/result echo."""
    if '"jsonrpc"' in span:
        return True
    if '"name"' in span and any(
        key in span
        for key in ('"arguments"', '"status"', '"result"', '"call_id"', '"mcpName"')
    ):
        return True
    # Leaked tool-argument objects, e.g. {"datamodelName": "..."} or
    # {"query": "...", "maxRows": 10}.
    if '"datamodelName"' in span or ('"query"' in span and '"maxRows"' in span):
        return True
    return False


def strip_leaked_tool_json(text: str) -> str:
    """Drop leaked tool-call / tool-result JSON that some models emit as text.

    gpt-oss occasionally narrates its tool use (e.g. "We will call
    describe_data.{\"name\": ...}{\"name\": ..., \"result\": ...}") into the
    final text. Remove any JSON object that looks like a tool-call/result echo,
    wherever it appears, plus leading planning sentences, keeping the prose.
    """
    out: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "{":
            end = _json_object_end(text, i)
            if end != -1 and _looks_like_tool_json(text[i:end]):
                i = end
                continue
        out.append(text[i])
        i += 1
    result = "".join(out)

    # Drop leading planning sentences left behind, e.g. "We will call describe_data."
    result = re.sub(
        r"^\s*(?:we(?:'ll| will| have to| need to)|let'?s|i(?:'ll| will))\b[^.\n]*[.\n]",
        "",
        result,
        flags=re.I,
    )
    return result.strip()


def sanitize_final_answer(answer: str) -> str:
    """Remove model planning chatter and leaked tool JSON from a final answer."""
    text = strip_leaked_tool_json(answer.strip())
    if not text:
        return text

    planning_patterns = (
        r"\bwe need to call\b",
        r"\bwe have to issue\b",
        r"\bnow (?:actually )?call\b",
        r"\bnow execute\b",
        r"\blet'?s (?:attempt|call|execute)\b",
        r"\bproceed\b",
        r"\btool call\b",
    )
    if not any(re.search(pattern, text, flags=re.I) for pattern in planning_patterns):
        return text

    markers = (
        "Answer\n",
        "Answer\r\n",
        "Result\n",
        "Result\r\n",
        "Logical SQL",
        "I attempted",
        "I tried",
        "The query",
    )
    starts = [text.find(marker) for marker in markers if text.find(marker) >= 0]
    if starts:
        return text[min(starts) :].strip()

    cleaned_lines = []
    for line in text.splitlines():
        if any(re.search(pattern, line, flags=re.I) for pattern in planning_patterns):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip() or text


def extract_logical_sql(answer: str, tool_calls: list[dict[str, Any]]) -> list[str]:
    """Extract likely Logical SQL snippets from answer and tool arguments."""
    if not any(call.get("name") == "execute_logical_sql" for call in tool_calls):
        return []
    candidates: list[str] = []
    fenced = re.findall(r"```(?:sql|text)?\s*(.*?)```", answer, flags=re.I | re.S)
    candidates.extend(fenced)
    if not candidates:
        select_blocks = re.findall(
            r"(^\s*(?:SELECT|WITH)\b.*?)(?=\n\s*\n|$)",
            answer,
            flags=re.I | re.M | re.S,
        )
        candidates.extend(select_blocks)
    for call in tool_calls:
        value = call.get("arguments")
        parsed = parse_json_like(value) if isinstance(value, str) else value
        if isinstance(parsed, dict) and isinstance(parsed.get("query"), str):
            candidates.append(parsed["query"])

    cleaned = []
    seen = set()
    for candidate in candidates:
        sql = candidate.strip().strip("`").strip()
        if not re.match(r"^\s*(SELECT|WITH)\b", sql, re.I):
            continue
        sql = sql[:4000]
        key = re.sub(r"\s+", " ", sql).lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(sql)
    return cleaned[-3:]


def parse_response_body(response: requests.Response) -> Any:
    """Parse JSON or SSE-ish MCP response body."""
    text = response.text
    try:
        return response.json()
    except ValueError:
        data_lines = [
            line[5:].strip()
            for line in text.splitlines()
            if line.startswith("data:")
        ]
        parsed = []
        for line in data_lines:
            try:
                parsed.append(json.loads(line))
            except ValueError:
                parsed.append(line)
        return parsed or text[:4000]


def required_value(payload: dict[str, Any], field: str, env_name: str) -> str:
    """Return a required payload or environment value."""
    value = str(payload.get(field) or os.getenv(env_name, "")).strip()
    if not value:
        raise ValueError(f"Missing {field}.")
    return value


def normalize_oac_mcp_url(url: str) -> str:
    """Normalize a copied OAC MCP URL to the JSON-RPC API endpoint.

    The /api/mcp path is the JSON-RPC endpoint. The /ui/api/mcp path is the
    browser UI route: hitting it programmatically returns a 302 to the OAC
    login UI (an HTML page), not JSON-RPC. We rewrite /ui/api/mcp -> /api/mcp
    so a token pasted from the OAC UI still reaches the working endpoint.
    """
    value = str(url or "").strip()
    if not value:
        return value
    return re.sub(r"/ui/api/mcp/?$", "/api/mcp", value)


def clean_bearer_token(token: str) -> str:
    """Return a token without the Bearer prefix."""
    token = token.strip().strip("'\"")
    if token.lower().startswith("authorization:"):
        token = token.split(":", 1)[1].strip()
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    return token.strip().strip("'\"")


def to_plain(value: Any) -> Any:
    """Convert SDK models into JSON-like structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_plain(item) for item in value]
    if hasattr(value, "model_dump"):
        return to_plain(value.model_dump())
    if hasattr(value, "dict"):
        return to_plain(value.dict())
    return str(value)


def truncate_value(value: Any, *, limit: int) -> Any:
    """Truncate nested data for UI display."""
    if value is None:
        return None
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "...<truncated>"
    text = json.dumps(value, ensure_ascii=True, default=str)
    return text if len(text) <= limit else text[:limit] + "...<truncated>"


if __name__ == "__main__":
    main()
