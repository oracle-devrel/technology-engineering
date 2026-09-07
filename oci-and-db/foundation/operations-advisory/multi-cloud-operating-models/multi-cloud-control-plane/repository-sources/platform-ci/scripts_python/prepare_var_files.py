#!/usr/bin/env python3
"""Prepare Terraform JSON var-files with environment-backed placeholders."""

import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Optional


# Authoritative placeholder grammar. The Codex plugin applies a stricter one as
# an early convenience check; when they disagree this one decides, and it is
# deliberately the more permissive of the two so nothing reaches Terraform
# unresolved.
PLACEHOLDER_RE = re.compile(r"(?<![A-Za-z0-9_])(__[A-Za-z0-9_]+__)(?![A-Za-z0-9_])")
ALLOWED_ENVIRONMENTS = {"dev", "test", "uat", "prod"}


def find_placeholders(value: Any) -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, item in value.items():
            found.update(find_placeholders(key))
            found.update(find_placeholders(item))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(find_placeholders(item))
        return found
    if isinstance(value, str):
        return set(PLACEHOLDER_RE.findall(value))
    return set()


def load_secret_values(environment: str) -> dict[str, str]:
    raw = os.environ.get("GITOPS_SECRET_VALUES", "").strip() or "{}"
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("GITOPS_SECRET_VALUES must be a JSON object") from exc
    if not isinstance(decoded, dict):
        raise ValueError("GITOPS_SECRET_VALUES must be a JSON object")
    secret_values = {
        str(key): str(value)
        for key, value in decoded.items()
        if value not in (None, "")
    }
    expected_prefix = f"{environment.upper()}_"
    invalid_names = sorted(
        name for name in secret_values if not name.startswith(expected_prefix)
    )
    if invalid_names:
        joined = ", ".join(invalid_names)
        raise ValueError(
            f"GITOPS_SECRET_VALUES contains names outside {environment}: {joined}"
        )
    return secret_values


def replacement_for(token: str, secret_values: dict[str, str]) -> Optional[str]:
    return secret_values.get(token[2:-2])


def validate_placeholder_environment(token: str, environment: str) -> None:
    expected_prefix = f"__{environment.upper()}_"
    if not token.startswith(expected_prefix):
        raise ValueError(
            f"placeholder {token} is not qualified for environment {environment}"
        )


def mask_secret_values(secret_values: dict[str, str]) -> None:
    """Mask each JSON member before tools can print resolved values in Actions."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    for value in sorted(set(secret_values.values())):
        # stdout is reserved for the caller's Terraform -var-file arguments.
        print(f"::add-mask::{value}", file=sys.stderr)


def replace_string(value: str, replacements: dict[str, str]) -> str:
    return PLACEHOLDER_RE.sub(lambda match: replacements.get(match.group(1), match.group(1)), value)


def replace_placeholders(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        replaced: dict[str, Any] = {}
        for key, item in value.items():
            replaced_key = replace_placeholders(key, replacements)
            replaced[str(replaced_key)] = replace_placeholders(item, replacements)
        return replaced
    if isinstance(value, list):
        return [replace_placeholders(item, replacements) for item in value]
    if isinstance(value, str):
        if value in replacements:
            return replacements[value]
        return replace_string(value, replacements)
    return value


def terraform_json_files(config_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in config_dir.rglob("*.json")
        if not {"ansible", "lifecycle_operations"}.intersection(path.relative_to(config_dir).parts)
    )


def prepare_file(
    source: Path,
    destination: Path,
    secret_values: dict[str, str],
    environment: str,
) -> None:
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{source}: invalid JSON: {exc}") from exc

    placeholders = find_placeholders(data)
    replacements: dict[str, str] = {}
    missing: list[str] = []
    for token in sorted(placeholders):
        validate_placeholder_environment(token, environment)
        replacement = replacement_for(token, secret_values)
        if replacement is None:
            missing.append(token)
        else:
            replacements[token] = replacement

    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{source}: unresolved placeholders without environment values: {joined}")

    prepared = replace_placeholders(data, replacements)
    remaining = find_placeholders(prepared)
    if remaining:
        joined = ", ".join(sorted(remaining))
        raise ValueError(f"{source}: unresolved placeholders after replacement: {joined}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(prepared, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 4:
        print(
            "Usage: prepare_var_files.py <config-dir> <output-dir> <environment>",
            file=sys.stderr,
        )
        return 2

    config_dir = Path(sys.argv[1]).resolve()
    output_dir = Path(sys.argv[2]).resolve()
    environment = sys.argv[3].lower()
    if environment not in ALLOWED_ENVIRONMENTS:
        print(f"Unsupported deployment environment: {environment}", file=sys.stderr)
        return 1
    if not config_dir.is_dir():
        print(f"Config directory not found: {config_dir}", file=sys.stderr)
        return 1

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    prepared_files: list[Path] = []
    try:
        secret_values = load_secret_values(environment)
        mask_secret_values(secret_values)
        for source in terraform_json_files(config_dir):
            destination = output_dir / source.relative_to(config_dir)
            prepare_file(source, destination, secret_values, environment)
            prepared_files.append(destination)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(" ".join(f"-var-file {shlex.quote(str(path))}" for path in prepared_files))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
