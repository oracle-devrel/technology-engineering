"""
File name: mcp_local_fs.py
Author: Luigi Saetta
Date last modified: 2025-12-12
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server that provides read-only access
    to the local file system. It exposes two tools:
    - list_folder: list the contents of a folder (directories and files)
    - read_file: return the textual content of a file

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_local_fs import list_folder, read_file

        items = list_folder("docs")
        content = read_file("README.md")
        # Or run the server: python mcp_local_fs.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework.
    For safety, all paths are resolved relative to a configurable root directory (read-only sandbox).
    Set the environment variable MCP_FS_ROOT to choose the root directory.
    If MCP_FS_ROOT is not set, the current working directory is used.

Warnings:
    This module is in development and may change in future versions.
    - Only text is returned; binary files may produce unreadable output.
    - Large files are truncated to a maximum size to avoid memory/latency issues.
    - Any attempt to access paths outside the configured root is rejected.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from mcp_utils import create_server, run_server


# -------------------------
# Configuration
# -------------------------

# Read-only root directory for all operations.
# You can set MCP_FS_ROOT=/some/safe/folder before launching the server.
_FS_ROOT = Path(os.getenv("MCP_FS_ROOT", os.getcwd())).expanduser().resolve()

# Max bytes read from a file (to prevent huge payloads).
_MAX_READ_BYTES = int(os.getenv("MCP_FS_MAX_READ_BYTES", "1048576"))  # 1 MiB default


mcp = create_server("Local FS MCP (Read-Only)")


# -------------------------
# Helpers
# -------------------------

def _resolve_under_root(user_path: str) -> Path:
    """
    Resolve a user-provided path under the configured root directory.

    - Accepts relative paths (preferred).
    - If an absolute path is provided, it must still be inside the root.
    - Rejects any path that escapes the root (e.g., via '..' traversal or symlinks).
    """
    if not isinstance(user_path, str) or not user_path.strip():
        raise ValueError("path must be a non-empty string")

    # Normalize: treat as relative unless explicitly absolute
    p = Path(user_path).expanduser()
    if not p.is_absolute():
        p = _FS_ROOT / p

    resolved = p.resolve()
    try:
        resolved.relative_to(_FS_ROOT)
    except ValueError as exc:
        raise ValueError(f"Access denied: path is outside root '{_FS_ROOT}'") from exc

    return resolved


def _safe_stat(path: Path) -> Dict[str, Any]:
    st = path.stat()
    return {
        "name": path.name,
        "path": str(path.relative_to(_FS_ROOT)),
        "is_dir": path.is_dir(),
        "is_file": path.is_file(),
        "size_bytes": int(st.st_size),
        "mtime_epoch": float(st.st_mtime),
    }


# -------------------------
# MCP tools
# -------------------------

@mcp.tool()
def list_folder(path: str = ".") -> Dict[str, Any]:
    """
    List the contents of a folder (directories and files), relative to the configured root.

    Parameters
    ----------
    path : str
        Folder path relative to the root directory (default: ".").

    Returns
    -------
    dict
        JSON object with directory listing:

        {
          "root": str,
          "path": str,
          "exists": bool,
          "is_dir": bool,
          "items": [
            {
              "name": str,
              "path": str,        # relative to root
              "is_dir": bool,
              "is_file": bool,
              "size_bytes": int,
              "mtime_epoch": float
            },
            ...
          ]
        }

    Notes
    -----
    - Items are returned unsorted by default filesystem order; callers can sort as needed.
    - Access outside root is rejected.
    """
    folder = _resolve_under_root(path)

    if not folder.exists():
        return {
            "root": str(_FS_ROOT),
            "path": str(Path(path)),
            "exists": False,
            "is_dir": False,
            "items": [],
        }

    if not folder.is_dir():
        return {
            "root": str(_FS_ROOT),
            "path": str(Path(path)),
            "exists": True,
            "is_dir": False,
            "items": [],
        }

    items: List[Dict[str, Any]] = []
    for child in folder.iterdir():
        # We still enforce under-root in case of weird symlink layouts
        try:
            resolved_child = child.resolve()
            resolved_child.relative_to(_FS_ROOT)
        except Exception:
            # Skip anything that resolves outside root
            continue

        try:
            items.append(_safe_stat(resolved_child))
        except Exception:
            # Skip unreadable entries
            continue

    return {
        "root": str(_FS_ROOT),
        "path": str(folder.relative_to(_FS_ROOT)),
        "exists": True,
        "is_dir": True,
        "items": items,
    }


@mcp.tool()
def read_file(path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    Read a text file and return its content (truncated to a max size), relative to the configured root.

    Parameters
    ----------
    path : str
        File path relative to the root directory.
    encoding : str
        Text encoding to decode bytes (default: "utf-8"). Decoding uses errors="replace".

    Returns
    -------
    dict
        JSON object with file content:

        {
          "root": str,
          "path": str,
          "exists": bool,
          "is_file": bool,
          "truncated": bool,
          "max_read_bytes": int,
          "content": str | None,
          "message": str
        }

    Notes
    -----
    - Binary files will be decoded with replacement characters; callers should avoid reading binaries.
    - Access outside root is rejected.
    """
    file_path = _resolve_under_root(path)

    if not file_path.exists():
        return {
            "root": str(_FS_ROOT),
            "path": str(Path(path)),
            "exists": False,
            "is_file": False,
            "truncated": False,
            "max_read_bytes": _MAX_READ_BYTES,
            "content": None,
            "message": "File not found.",
        }

    if not file_path.is_file():
        return {
            "root": str(_FS_ROOT),
            "path": str(Path(path)),
            "exists": True,
            "is_file": False,
            "truncated": False,
            "max_read_bytes": _MAX_READ_BYTES,
            "content": None,
            "message": "Path is not a file.",
        }

    # Read bytes, cap at max size (+1 to detect truncation)
    with open(file_path, "rb") as f:
        data = f.read(_MAX_READ_BYTES + 1)

    truncated = len(data) > _MAX_READ_BYTES
    if truncated:
        data = data[:_MAX_READ_BYTES]

    text = data.decode(encoding, errors="replace")

    return {
        "root": str(_FS_ROOT),
        "path": str(file_path.relative_to(_FS_ROOT)),
        "exists": True,
        "is_file": True,
        "truncated": truncated,
        "max_read_bytes": _MAX_READ_BYTES,
        "content": text,
        "message": "OK" if not truncated else "OK (content truncated to max_read_bytes).",
    }


if __name__ == "__main__":
    run_server(mcp)
