#!/usr/bin/env python3
"""Compare rendered MCCP component source with a published component tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXCLUDED_DIRECTORIES = frozenset({".git", "__pycache__", "tests"})


def _source_files(directory: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or EXCLUDED_DIRECTORIES.intersection(path.parts):
            continue
        files[path.relative_to(directory).as_posix()] = path.read_bytes()
    return files


def _render(
    content: bytes,
    substitutions: dict[str, str],
    path: str,
    release_placeholders: frozenset[str],
) -> bytes:
    try:
        rendered = content.decode("utf-8")
    except UnicodeDecodeError:
        return content
    for token, value in substitutions.items():
        rendered = rendered.replace(token, value)
    unresolved = sorted(token for token in release_placeholders if token in rendered)
    if unresolved:
        tokens = ", ".join(sorted(set(unresolved)))
        raise ValueError(f"Unresolved placeholder in {path}: {tokens}")
    return rendered.encode("utf-8")


def project_component(
    source_root: Path,
    source_relative: str,
    substitutions: dict[str, str],
    release_placeholders: frozenset[str] = frozenset(),
) -> dict[str, bytes]:
    """Return the rendered publishable component tree keyed by relative path."""
    component = source_root / source_relative
    if not component.is_dir():
        raise ValueError(f"Source component is missing: {source_relative}")
    projected = {
        path: _render(content, substitutions, path, release_placeholders)
        for path, content in _source_files(component).items()
    }
    license_file = source_root / "LICENSE"
    if license_file.is_file() and "LICENSE" not in projected:
        projected["LICENSE"] = license_file.read_bytes()
    return projected


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def compare_component(
    source_root: Path,
    source_relative: str,
    published_component: Path,
    substitutions: dict[str, str],
    release_placeholders: frozenset[str] = frozenset(),
) -> dict[str, list[str]]:
    """Return sorted missing, unexpected, different, and equal relative paths."""
    expected = project_component(
        source_root, source_relative, substitutions, release_placeholders
    )
    actual = _source_files(published_component)
    expected_paths = set(expected)
    actual_paths = set(actual)
    common_paths = expected_paths.intersection(actual_paths)
    return {
        "missing": sorted(expected_paths - actual_paths),
        "unexpected": sorted(actual_paths - expected_paths),
        "different": sorted(
            path
            for path in common_paths
            if _sha256(expected[path]) != _sha256(actual[path])
        ),
        "equal": sorted(
            path
            for path in common_paths
            if _sha256(expected[path]) == _sha256(actual[path])
        ),
    }


def _load_substitutions(path: Path | None, customer_org: str) -> dict[str, str]:
    substitutions = {"__CUSTOMER_ORG__": customer_org}
    if path is None:
        return substitutions
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in data.items()
    ):
        raise ValueError("Substitutions must be a JSON object of string values")
    substitutions.update(data)
    return substitutions


def _release_placeholders(manifest: dict[str, object]) -> frozenset[str]:
    placeholders = manifest.get("release_placeholders", [])
    if not isinstance(placeholders, list) or not all(
        isinstance(token, str) and token.startswith("__") and token.endswith("__")
        for token in placeholders
    ):
        raise ValueError("Manifest release_placeholders must be a list of tokens")
    return frozenset(placeholders)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify rendered MCCP component parity against published trees."
    )
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--published-root", type=Path, required=True)
    parser.add_argument("--customer-org", required=True)
    parser.add_argument("--substitutions", type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    components = manifest.get("component_repositories")
    if not isinstance(components, dict):
        raise ValueError("Manifest component_repositories must be an object")
    source_root = args.manifest.parent.parent
    substitutions = _load_substitutions(args.substitutions, args.customer_org)
    release_placeholders = _release_placeholders(manifest)
    report = {
        repository: compare_component(
            source_root,
            source_relative,
            args.published_root / repository,
            substitutions,
            release_placeholders,
        )
        for repository, source_relative in sorted(components.items())
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if all(
        not result["missing"] and not result["unexpected"] and not result["different"]
        for result in report.values()
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
