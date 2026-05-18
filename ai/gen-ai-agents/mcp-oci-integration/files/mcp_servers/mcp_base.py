"""
File name: mcp_base.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module provides the base class for MCP (Model Context Protocol) servers.
    It defines abstract methods and common functionality for server implementations,
    such as handling requests, authentication, and error management in a distributed system.

Usage:
    Import this module and subclass MCPBase to create custom server implementations.
    Example:
        from mcp_servers.mcp_base import MCPBase

        class MyServer(MCPBase):
            def process_request(self, request_data):
                # Implement custom logic here
                pass

License:
    This code is released under the MIT License.

Notes:
    This is a foundational part of the MCP-OCI integration framework, designed for extensibility.
    Subclasses should implement all abstract methods to ensure compatibility with MCP tools and APIs.

Warnings:
    This module is in development and may change in future versions. Ensure subclasses handle
    potential breaking changes in abstract method signatures.
"""

from typing import Callable, Optional
from functools import wraps

from mcp_utils import create_server, run_server
from utils import get_console_logger


def expose_tool(name: Optional[str] = None, description: Optional[str] = None):
    """
    Marker decorator for instance methods to export as MCP tools.

    Args:
        name: Optional tool name; defaults to method name.
        description: Optional doc override shown in MCP discovery.
    """

    def _decorator(fn: Callable):
        setattr(fn, "_mcp_expose", True)
        if name:
            setattr(fn, "_mcp_tool_name", name)
        if description:
            setattr(fn, "_mcp_tool_desc", description)
        return fn

    return _decorator


class BaseMCPServer:
    """
    Subclass and decorate instance methods with @expose_tool to export them.

    Parameters
    ----------
    server_name : str
        The MCP server name (surfaced in discovery).
    debug : bool
        Toggle extra logging.
    wrap_result : bool
        If True, wrap successful results as {"result": <value>}.
    on_call : Optional[Callable[[str, tuple, dict], None]]
        Optional hook invoked before each tool call with (tool_name, args, kwargs).
    on_error : Optional[Callable[[str, Exception], None]]
        Optional hook invoked when a tool raises.
    """

    def __init__(
        self,
        server_name: str,
        *,
        debug: bool = False,
        wrap_result: bool = False,
        on_call: Optional[Callable[[str, tuple, dict], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None,
    ):
        self.server_name = server_name
        self.debug = debug
        self.wrap_result = wrap_result
        self.on_call = on_call
        self.on_error = on_error

        self.logger = get_console_logger()
        # SECURITY/JWT is handled entirely by create_server; nothing here.
        self.mcp = create_server(server_name)

        self._register_tools()

    def _wrap_tool(self, method: Callable, tool_name: str, tool_desc: Optional[str]):
        """
        Wrap the bound method with logging, optional hooks, result wrapping, and error handling.
        """

        @wraps(method)
        def _wrapped(*args, **kwargs):
            if self.debug:
                self.logger.info(
                    "[%s] %s called | args=%s kwargs=%s",
                    self.server_name,
                    tool_name,
                    args,
                    kwargs,
                )
            if self.on_call:
                try:
                    self.on_call(tool_name, args, kwargs)
                except Exception:
                    # Never let hooks break the tool
                    pass

            try:
                out = method(*args, **kwargs)
                # Uniform, JSON-serializable success path
                return {"result": out} if self.wrap_result else out
            except Exception as e:
                if self.on_error:
                    try:
                        self.on_error(tool_name, e)
                    except Exception:
                        pass
                self.logger.exception(
                    "[%s] %s error: %s", self.server_name, tool_name, e
                )
                # Always return a serializable error envelope
                return {"error": str(e)}

        # Description for MCP discovery
        if tool_desc:
            _wrapped.__doc__ = tool_desc
        elif not getattr(_wrapped, "__doc__", None):
            _wrapped.__doc__ = f"MCP tool: {tool_name}"

        # Programmatic registration (same effect as @mcp.tool)
        self.mcp.tool(_wrapped)
        return _wrapped

    def _register_tools(self):
        """
        Find and register all @expose_tool methods.
        """
        for attr_name in dir(self):
            if attr_name.startswith("_"):
                continue
            method = getattr(self, attr_name)
            if not callable(method):
                continue
            if getattr(method, "_mcp_expose", False):
                tool_name = getattr(method, "_mcp_tool_name", attr_name)
                tool_desc = getattr(method, "_mcp_tool_desc", None)
                self._wrap_tool(method, tool_name, tool_desc)

    def run(self):
        """
        Delegate to shared run_server (reads host/port etc. from CLI).
        """
        if self.debug:
            self.logger.info("Starting MCP server '%s'...", self.server_name)
        run_server(self.mcp)
