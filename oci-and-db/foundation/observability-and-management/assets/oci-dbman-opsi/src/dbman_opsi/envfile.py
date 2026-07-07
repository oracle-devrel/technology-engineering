"""Load local environment variables without committing secrets."""

from __future__ import annotations

import os
from pathlib import Path


def _strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            if index == 0 or value[index - 1].isspace():
                return value[:index].rstrip()
    return value


def _parse_value(value: str) -> str:
    value = _strip_inline_comment(value.strip())
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def load_env_file(path: str | Path = ".env.local", *, override: bool = False) -> tuple[str, ...]:
    """Load KEY=VALUE pairs from a local env file.

    Existing process variables win by default, so CI/Cloud Shell can override
    local defaults. The parser is intentionally small: it supports comments,
    blank lines, `export KEY=VALUE`, quoted values, and inline comments after
    unquoted values.
    """

    env_path = Path(path)
    if not env_path.exists():
        return ()

    loaded: list[str] = []
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        key = key.strip()
        if not key or (key in os.environ and not override):
            continue
        os.environ[key] = _parse_value(raw_value)
        loaded.append(key)
    return tuple(loaded)
