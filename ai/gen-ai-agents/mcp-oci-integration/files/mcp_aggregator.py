"""
MCP Aggregator (HTTP-only, FastMCP v2)

- Re-exports tools 1:1 from remote MCP servers over Streamable HTTP.
- Aligns input schema: generates a dynamic function signature
  that matches each remote tool's inputSchema.
- Respects output schema: if the remote tool declares `x-fastmcp-wrap-result: true`,
  the aggregator wraps the returned value as `{"result": <value>}`.
- No persistent client sessions: each call opens/closes a FastMCP Client
  (robust across event loops).
- Toggleable structured logging via the DEBUG constant.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

import yaml

# fastmcp >= 2.x (recommended >= 2.10.0)
from fastmcp import FastMCP, Client
from fastmcp.server.auth.providers.jwt import JWTVerifier

from llm_with_mcp import default_jwt_supplier

# ---------- DEBUG TOGGLE ----------
DEBUG = False  # Set to True for verbose logging (DEBUG), False for quieter logs (INFO)


# ---------- logging ----------
def setup_logging():
    """
    Initialize structured JSON logging at the level determined by the DEBUG flag.
    """
    level = logging.DEBUG if DEBUG else logging.INFO
    logging.basicConfig(level=level, format="%(message)s")
    logging.log(
        level,
        json.dumps({"event": "logger.init", "level": "DEBUG" if DEBUG else "INFO"}),
    )


def log_json(**kwargs):
    """
    Emit a single structured JSON log line.
    Uses DEBUG level when DEBUG=True, otherwise INFO level.
    """
    msg = json.dumps(kwargs, ensure_ascii=False)
    if DEBUG:
        logging.debug(msg)
    else:
        logging.info(msg)


# ---------- schema utilities ----------
def _py_hint(json_schema: dict) -> str:
    """
    Map a JSON Schema 'type' to a Python type hint string for generated tool signatures.

    Args:
        json_schema: The JSON Schema node for a single property.

    Returns:
        A Python type hint string (e.g., "str", "int", "dict").
    """
    t = json_schema.get("type")
    if isinstance(t, list):
        # If union includes "null", prefer the non-null type for the hint.
        t = [x for x in t if x != "null"]
        t = t[0] if t else "object"
    return {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
        "array": "list",
        "object": "dict",
    }.get(t, "object")


# ---------- aggregator ----------
class Aggregator:
    """
    MCP Aggregator server that re-exports remote MCP tools over HTTP.

    Key responsibilities:
    - Discover tools from configured backends.
    - Register local proxy tools with function signatures that mirror
      the remote input schemas (no **kwargs).
    - For each invocation, create a short-lived FastMCP Client to call the remote tool.
    - Normalize outputs and wrap result when the remote outputSchema requires it.

    Notes:
    - Transport is HTTP-only (Streamable HTTP). No stdio and no explicit SSE.
    - Tool naming can be optionally namespaced as "<backend>.<tool>" via config.
    """

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize the aggregator from a YAML config.

        Config keys:
            timeout_seconds (float, optional): HTTP timeout for remote calls (default 15).
            use_namespace (bool, optional): Whether to expose tools as "<backend>.<tool>".
            backends (list[dict]): Each item requires:
                - name (str): Logical backend name.
                - url (str): MCP HTTP endpoint (e.g., http://host:port/mcp).

        Args:
            config_path: Path to the YAML configuration file.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}

        self.timeout: float = float(cfg.get("timeout_seconds", 15))
        self.host: str = str(cfg.get("host", "0.0.0.0"))
        self.port: int = int(cfg.get("port", 6000))

        self.backends_cfg: List[dict] = cfg.get("backends", [])
        if not self.backends_cfg:
            raise RuntimeError("config.yaml: 'backends' section is missing or empty")

        if cfg.get("enable_jwt_tokens", False):
            # config to check that a valid JWT token is provided
            iam_base_url = cfg.get("iam_base_url", "").strip().rstrip("/")
            issuer = cfg.get("issuer", "")
            audience = cfg.get("audience", [])
            self.auth = JWTVerifier(
                # this is the url to get the public key from IAM
                # the PK is used to check the JWT
                jwks_uri=f"{iam_base_url}/admin/v1/SigningCert/jwk",
                issuer=issuer,
                audience=audience,
            )
            self.jwt_supplier = default_jwt_supplier()
        else:
            self.auth = None
            self.jwt_supplier = default_jwt_supplier()

        # Optional namespacing of exposed tool names
        self.use_namespace: bool = bool(cfg.get("use_namespace", False))

        self.server = FastMCP(name="mcp-aggregator", auth=self.auth)

        # Registry: exposed tool name -> backend info and schema
        # info = {
        #   "url": str,
        #   "backend": str,
        #   "in_schema": dict | None,
        #   "out_schema": dict | None,
        #   "wrap": bool  # whether to wrap output as {"result": value}
        # }
        self.registry: Dict[str, dict] = {}

    async def bootstrap(self) -> None:
        """
        Discover remote tools from all backends, then register corresponding local proxy tools.

        For each remote tool:
            - Determine the exposed name (optionally namespaced).
            - Persist input/output schemas and whether 'x-fastmcp-wrap-result' is set.
            - Generate a proxy function with a signature matching the input schema.
            - Register the proxy function as a local tool on this server.
        """
        setup_logging()

        for backend in self.backends_cfg:
            backend_name = backend["name"]
            backend_url = backend["url"]

            # One-time discovery with a short-lived client
            async with Client(
                backend_url, timeout=self.timeout, auth=self.jwt_supplier
            ) as client:
                tools = await client.list_tools()

            for t in tools:
                remote_name = t.name
                exposed_name = (
                    f"{backend_name}.{remote_name}"
                    if self.use_namespace
                    else remote_name
                )
                if exposed_name in self.registry:
                    raise RuntimeError(
                        f"Tool name collision: '{exposed_name}' already registered"
                    )

                in_schema: Optional[dict] = getattr(t, "inputSchema", None)
                out_schema: Optional[dict] = getattr(t, "outputSchema", None)
                wrap_result: bool = bool(
                    out_schema and out_schema.get("x-fastmcp-wrap-result")
                )

                desc = (
                    getattr(t, "description", None)
                    or f"Proxy to {backend_name}:{remote_name}"
                )

                self.registry[exposed_name] = {
                    "url": backend_url,
                    "backend": backend_name,
                    "in_schema": in_schema,
                    "out_schema": out_schema,
                    "wrap": wrap_result,
                }

                proxy_fn = self._make_proxy_with_signature(
                    backend_url=backend_url,
                    backend_name=backend_name,
                    tool_name=remote_name,
                    input_schema=in_schema,
                    wrap_result=wrap_result,
                )

                self.server.tool(name=exposed_name, description=desc)(proxy_fn)

                log_json(
                    event="registry.tool",
                    exposed_tool=exposed_name,
                    backend=backend_name,
                    url=backend_url,
                    has_input_schema=bool(in_schema),
                    has_output_schema=bool(out_schema),
                    wrap_result=wrap_result,
                )

    def _make_proxy_with_signature(
        self,
        backend_url: str,
        backend_name: str,
        tool_name: str,
        input_schema: Optional[dict],
        wrap_result: bool,
    ):
        """
        Build a proxy coroutine whose signature mirrors the remote tool's input schema.

        - If an input schema is present, generate a function with explicit parameters for
          each property (no **kwargs), using type hints inferred from JSON Schema types.
          Optional params default to None; only non-None values are forwarded.
        - If no input schema is provided, expose a generic proxy with a single
          parameter: `arguments: dict`.

        Output handling:
        - Prefer `res.data` if present.
        - Else prefer `res.text`.
        - Else concatenate any text fragments from `res.content`.
        - If the remote output schema marks `x-fastmcp-wrap-result: true`, wrap the
          value as `{"result": value}` before returning.

        Args:
            backend_url: Remote MCP HTTP endpoint for the tool.
            backend_name: Human-friendly backend name (used for logs and namespacing).
            tool_name: Remote tool name to call.
            input_schema: JSON Schema describing the tool input.
            wrap_result: Whether to wrap the final value as {"result": value}.

        Returns:
            A coroutine function (async def) ready to be registered as a FastMCP tool.
        """
        # Fallback: generic proxy with a single 'arguments: dict' parameter
        if not input_schema or not isinstance(input_schema, dict):

            async def proxy(arguments: dict):
                async with Client(
                    backend_url, timeout=self.timeout, auth=self.jwt_supplier
                ) as c:
                    res = await c.call_tool(tool_name, arguments or {})
                # Normalize output
                val = getattr(res, "data", None)
                if val is None:
                    txt = getattr(res, "text", None)
                    if txt:
                        val = txt
                    else:
                        parts = getattr(res, "content", None) or []
                        texts = [
                            getattr(p, "text", None)
                            for p in parts
                            if getattr(p, "text", None)
                        ]
                        val = "\n".join(texts) if texts else {"ok": True}
                # Respect remote wrapping contract if requested
                return {"result": val} if wrap_result else val

            log_json(
                event="proxy.signature",
                backend=backend_name,
                tool=tool_name,
                signature="arguments: dict",
            )
            return proxy

        # Build a Python signature from the JSON Schema properties
        props = input_schema.get("properties", {}) or {}
        required = set(input_schema.get("required", []) or [])

        params_code = []
        for name, spec in props.items():
            hint = _py_hint(spec)
            if name in required:
                params_code.append(f"{name}: {hint}")
            else:
                params_code.append(f"{name}: {hint} | None = None")
        signature = ", ".join(params_code) if params_code else ""

        # Function body:
        # - collect only non-None parameters
        # - call the remote tool via a short-lived Client
        # - normalize output
        # - wrap if needed (x-fastmcp-wrap-result)
        body_lines = [
            "    args = {}",
        ]
        for name in props.keys():
            body_lines.append(f"    if {name} is not None: args['{name}'] = {name}")
        body_lines += [
            "    async with Client(__backend_url, timeout=__timeout) as c:",
            "        res = await c.call_tool(__tool_name, args)",
            "    val = getattr(res, 'data', None)",
            "    if val is None:",
            "        txt = getattr(res, 'text', None)",
            "        if txt is not None and txt != '':",
            "            val = txt",
            "        else:",
            "            parts = getattr(res, 'content', None) or []",
            "            texts = [getattr(p, 'text', None) for p in parts if getattr(p, 'text', None)]",
            "            val = '\\n'.join(texts) if texts else {'ok': True}",
            "    return {'result': val} if __wrap_result else val",
        ]
        src = "async def proxy(" + signature + "):\n" + "\n".join(body_lines)

        # Make `__backend_url`, `__tool_name`, `__timeout`, `__wrap_result` available as globals
        glb = {
            "Client": Client,
            "__backend_url": backend_url,
            "__tool_name": tool_name,
            "__timeout": self.timeout,
            "__wrap_result": wrap_result,
        }
        lcl = {}
        exec(src, glb, lcl)
        proxy = lcl["proxy"]

        log_json(
            event="proxy.signature",
            backend=backend_name,
            tool=tool_name,
            signature=signature or "<no-args>",
        )
        return proxy

    def run(self, host: str = "0.0.0.0", port: int = 6000) -> None:
        """
        Start the FastMCP server over Streamable HTTP.

        Args:
            host: Bind address for the HTTP server.
            port: TCP port for the HTTP server.
        """
        self.server.run(transport="http", host=host, port=port)


if __name__ == "__main__":
    # Entry point: load config, bootstrap (discover & register tools), then serve HTTP.
    agg = Aggregator("aggregator_config.yaml")
    asyncio.run(agg.bootstrap())
    agg.run(host=agg.host, port=agg.port)
