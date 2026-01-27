"""
File name: gitignore_utils.py
Author: Unknown
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Minimal .gitignore matcher (best-effort, no external deps).

    Supports:
    - blank lines / comments
    - negation: !pattern
    - directory patterns ending with /
    - simple globbing via fnmatch
    - patterns are evaluated against repo-relative POSIX paths

    Limitations:
    - does not fully implement gitignore spec (e.g., anchored patterns, **, etc.)
    - good enough for policy gating (downgrade FAIL->WARN) but not for exact git behavior
"""

from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

from agent.utils import get_console_logger

logger = get_console_logger()


@dataclass(frozen=True)
class GitIgnoreRule:
    pattern: str
    negated: bool
    is_dir: bool


def parse_gitignore(text: str) -> list[GitIgnoreRule]:
    rules: list[GitIgnoreRule] = []

    logger.info("Scanning .gitignore...")

    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        neg = line.startswith("!")
        if neg:
            line = line[1:].strip()
            if not line:
                continue

        is_dir = line.endswith("/")
        pat = line[:-1] if is_dir else line

        # Normalize to POSIX-like
        pat = pat.replace("\\", "/")

        rules.append(GitIgnoreRule(pattern=pat, negated=neg, is_dir=is_dir))
    return rules


def _match_rule(rel_posix: str, rule: GitIgnoreRule) -> bool:
    # Directory rule: match if path is under that directory
    if rule.is_dir:
        prefix = rule.pattern.rstrip("/") + "/"
        return rel_posix.startswith(prefix)

    # Glob match against full rel path OR basename
    return fnmatch(rel_posix, rule.pattern) or fnmatch(
        Path(rel_posix).name, rule.pattern
    )


def is_ignored(rel_posix: str, rules: list[GitIgnoreRule]) -> bool:
    """
    Apply rules in order (like git): last match wins; negation un-ignores.
    """
    ignored = False
    for r in rules:
        if _match_rule(rel_posix, r):
            ignored = not r.negated
    return ignored
