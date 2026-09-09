#!/usr/bin/env python3
"""Render agent metadata from plugin.json and fail on divergence."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
AGENT = ROOT / "skills" / "project-gitops" / "agents" / "openai.yaml"


def render(plugin: dict[str, object]) -> str:
    interface = plugin.get("interface")
    if not isinstance(interface, dict):
        raise ValueError("plugin interface metadata is missing")
    display_name = interface.get("displayName")
    short_description = interface.get("shortDescription")
    prompts = interface.get("defaultPrompt")
    if (
        not isinstance(display_name, str)
        or not isinstance(short_description, str)
        or not isinstance(prompts, list)
        or len(prompts) != 1
        or not isinstance(prompts[0], str)
    ):
        raise ValueError("plugin interface metadata is invalid")
    return (
        "interface:\n"
        f'  display_name: {json.dumps(display_name)}\n'
        f'  short_description: {json.dumps(short_description)}\n'
        f'  default_prompt: {json.dumps(prompts[0])}\n'
    )


def main() -> int:
    try:
        expected = render(json.loads(PLUGIN.read_text(encoding="utf-8")))
        actual = AGENT.read_text(encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"metadata check failed: {error}", file=sys.stderr)
        return 2
    if actual != expected:
        print("metadata check failed: openai.yaml diverges from plugin.json", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
