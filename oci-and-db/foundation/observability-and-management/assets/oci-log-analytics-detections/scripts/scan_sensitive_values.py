#!/usr/bin/env python3
"""Scan commit-candidate files for sensitive or tenant-specific values."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable

PROJECT_DIR = Path(__file__).resolve().parent.parent

IGNORED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".sentinel",
    ".sigmahq",
    ".terraform",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}

ALLOWED_VALUE_FRAGMENTS = (
    "cap-",
    "changeme",
    "default-",
    "dummy",
    "example",
    "fake",
    "placeholder",
    "redacted",
    "sample",
    "synthetic",
    "test-only",
    "your-",
)

PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(?P<key>[A-Z0-9_.-]*(?:api[_-]?key|auth[_-]?token|client[_-]?secret|"
    r"password|passwd|private[_-]?key|secret|token)[A-Z0-9_.-]*)\b"
    r"\s*(?::(?!:)|=)\s*(?P<quote>['\"]?)(?P<value>[^'\"\s#]+)"
)
# Allow an optional closing quote after `id` (dict-style ``'opc-request-id': '...'``)
# and include ``/`` in the value so multi-segment request IDs are fully captured.
OPC_REQUEST_ID_RE = re.compile(
    r"(?i)\bopc[-_]request[-_]id\b['\"]?\s*[:=]\s*['\"]?(?P<value>[A-Za-z0-9._:/-]{12,})"
)
OCID_RE = re.compile(r"\bocid1\.[A-Za-z0-9][A-Za-z0-9._-]{8,}\b", re.IGNORECASE)
# A Log Analytics namespace embedded in a REST path fingerprints a tenancy and
# leaks through live error payloads. (Generic OCI service hostnames are public and
# intentionally NOT flagged -- only the namespace inside the path is sensitive.)
LA_NAMESPACE_PATH_RE = re.compile(r"/namespaces/(?P<value>[a-z0-9]{6,})/", re.IGNORECASE)
IPV4_RE = re.compile(
    r"(?<![\d.])"
    r"(?:25[0-5]|2[0-4]\d|1?\d?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}"
    r"(?![\d.])"
)


def _project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_DIR))
    except ValueError:
        return str(path)


def _is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIR_NAMES for part in path.parts)


def _is_binary(path: Path) -> bool:
    try:
        return b"\0" in path.read_bytes()[:4096]
    except OSError:
        return True


def _read_text(path: Path) -> str | None:
    if _is_binary(path):
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    except OSError:
        return None


def _default_git_files() -> list[Path] | None:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=PROJECT_DIR,
            capture_output=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    files = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        path = PROJECT_DIR / raw.decode("utf-8", errors="replace")
        if path.is_file() and not _is_ignored_path(path.relative_to(PROJECT_DIR)):
            files.append(path)
    return sorted(files)


def _walk_files(root: Path) -> Iterable[Path]:
    if root.is_file():
        if not _is_ignored_path(root):
            yield root
        return
    for current_root, dir_names, file_names in os.walk(root):
        current = Path(current_root)
        dir_names[:] = [name for name in dir_names if name not in IGNORED_DIR_NAMES]
        if _is_ignored_path(current):
            continue
        for file_name in file_names:
            path = current / file_name
            if path.is_file() and not _is_ignored_path(path):
                yield path


def iter_scan_files(paths: list[Path] | None = None) -> list[Path]:
    """Return files to scan, using git's exclude rules for the default repo scan."""
    if not paths:
        git_files = _default_git_files()
        if git_files is not None:
            return git_files
        paths = [PROJECT_DIR]
    files = []
    for path in paths:
        files.extend(_walk_files(path))
    return sorted({file.resolve() for file in files})


def _has_allowed_marker(line: str) -> bool:
    return "scanner-fixture" in line or "allow-sensitive-value" in line


def _relative_path(path: Path) -> Path:
    try:
        return path.resolve().relative_to(PROJECT_DIR)
    except ValueError:
        return path


def _is_synthetic_fixture_path(path: Path) -> bool:
    relative = _relative_path(path)
    normalized = relative.as_posix()
    fixture_suffixes = (
        "scripts/generate_geo_health_logs.py",
        "scripts/generate_test_logs.py",
        "scripts/schemas/oci_audit_schema.py",
        "scripts/setup_log_sources.py",
    )
    # Synthetic-generator packages carved out of the exempt monoliths above
    # (T1 module split). scripts/testlogs/** holds the synthetic attack-log
    # builders (legitimate threat-intel IOC IPs/domains for detection content)
    # extracted from generate_test_logs.py; scripts/logsources/** holds the
    # source/field definitions extracted from setup_log_sources.py. Both inherit
    # the synthetic-fixture exemption. NOTE: scripts/dashboards/** (carved from
    # deploy_dashboard.py, which was never exempt) is deliberately still scanned.
    fixture_dir_prefixes = (
        "scripts/testlogs/",
        "scripts/logsources/",
    )
    return (
        any(normalized.endswith(suffix) for suffix in fixture_suffixes)
        or any(normalized.startswith(prefix) for prefix in fixture_dir_prefixes)
        or (normalized.startswith("queries/") and not _is_generated_report(relative))
        or normalized.startswith("rules/")
    )


def _is_generated_report(relative: Path) -> bool:
    """Generated reports/evidence under queries/ can carry live tenancy data, so they
    must NOT be exempted as fixtures even though they live beside detection queries."""
    name = relative.name.lower()
    return relative.suffix == ".json" and any(
        token in name for token in ("report", "result", "evidence", "live", "validation", "conversion")
    )


def _is_test_fixture_path(path: Path) -> bool:
    relative = _relative_path(path)
    return relative.name.startswith("test_") and relative.suffix == ".py"


def _is_placeholder(value: str) -> bool:
    stripped = value.strip().strip("'\"")
    lowered = stripped.lower()
    if not stripped:
        return True
    if stripped.startswith("<") and stripped.endswith(">"):
        return True
    if stripped.startswith("${") and stripped.endswith("}"):
        return True
    return any(fragment in lowered for fragment in ALLOWED_VALUE_FRAGMENTS)


def _looks_like_detection_or_code_token(value: str, line: str) -> bool:
    stripped = value.strip().strip("'\"")
    lowered_line = line.lower()
    if len(stripped) < 8:
        return True
    if re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?", stripped):
        return True
    if stripped.startswith(("[", "{", "(", "r'", 'r"', "re.")):
        return True
    if any(char in stripped for char in ("(", "[", "]", "\\")):
        return True
    if "*" in stripped:
        return True
    return any(
        marker in lowered_line
        for marker in (
            "'command line' like",
            "'request url' like",
            " token::",
            "token::",
            "userpassword=",
            "re.compile",
            "tokenize",
            "unsupported logan output token",
        )
    )


def _is_allowed_secret(value: str, line: str, path: Path) -> bool:
    return (
        _has_allowed_marker(line)
        or _is_placeholder(value)
        or _looks_like_detection_or_code_token(value, line)
        or _is_synthetic_fixture_path(path)
    )


def _is_allowed_ocid(value: str, line: str, path: Path) -> bool:
    lowered = value.lower()
    if _has_allowed_marker(line) or _is_placeholder(value):
        return True
    if lowered.endswith(".example") or "..example" in lowered:
        return True
    return _is_synthetic_fixture_path(path) or _is_test_fixture_path(path)


def _is_public_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return bool(ip.is_global)


def _is_allowed_public_ip(path: Path, line: str) -> bool:
    return _has_allowed_marker(line) or _is_synthetic_fixture_path(path) or _is_test_fixture_path(path)


def _redacted_preview(line: str, start: int, end: int, kind: str) -> str:
    before = line[:start][-90:]
    after = line[end:][:90]
    preview = f"{before}<redacted:{kind}>{after}".strip()
    return preview[:240]


def _finding(path: Path, line_number: int, kind: str, severity: str, line: str, start: int, end: int) -> dict:
    return {
        "path": _project_relative(path),
        "line": line_number,
        "kind": kind,
        "severity": severity,
        "preview": _redacted_preview(line, start, end, kind),
    }


def scan_file(path: Path) -> list[dict]:
    """Scan one text file and return redacted finding records."""
    text = _read_text(path)
    if text is None:
        return []

    findings = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _has_allowed_marker(line):
            continue

        private_key = PRIVATE_KEY_RE.search(line)
        if private_key:
            findings.append(_finding(path, line_number, "private_key", "critical", line, private_key.start(), private_key.end()))

        for match in SECRET_ASSIGNMENT_RE.finditer(line):
            value = match.group("value")
            if _is_allowed_secret(value, line, path):
                continue
            findings.append(
                _finding(
                    path,
                    line_number,
                    "secret_assignment",
                    "high",
                    line,
                    match.start("value"),
                    match.end("value"),
                )
            )

        for match in OPC_REQUEST_ID_RE.finditer(line):
            value = match.group("value")
            if _is_placeholder(value):
                continue
            findings.append(
                _finding(
                    path,
                    line_number,
                    "opc_request_id",
                    "medium",
                    line,
                    match.start("value"),
                    match.end("value"),
                )
            )

        for match in OCID_RE.finditer(line):
            value = match.group(0)
            if _is_allowed_ocid(value, line, path):
                continue
            findings.append(_finding(path, line_number, "ocid", "high", line, match.start(), match.end()))

        for match in IPV4_RE.finditer(line):
            value = match.group(0)
            if not _is_public_ip(value) or _is_allowed_public_ip(path, line):
                continue
            findings.append(_finding(path, line_number, "public_ip", "medium", line, match.start(), match.end()))

        for match in LA_NAMESPACE_PATH_RE.finditer(line):
            if _is_placeholder(match.group("value")):
                continue
            findings.append(_finding(path, line_number, "la_namespace", "medium", line, match.start("value"), match.end("value")))

    return findings


def scan_paths(paths: list[Path] | None = None) -> list[dict]:
    """Scan one or more roots and return sorted, redacted findings."""
    findings = []
    for path in iter_scan_files(paths):
        findings.extend(scan_file(path))
    return sorted(findings, key=lambda item: (item["path"], item["line"], item["kind"]))


def build_report(findings: list[dict]) -> dict:
    return {
        "ok": not findings,
        "finding_count": len(findings),
        "findings": findings,
    }


def print_human(report: dict) -> None:
    if report["ok"]:
        print("OK - no sensitive values found")
        return
    print(f"Sensitive value scan failed: {report['finding_count']} finding(s)")
    for finding in report["findings"][:100]:
        print(
            f"{finding['path']}:{finding['line']} "
            f"[{finding['severity']} {finding['kind']}] {finding['preview']}"
        )
    if report["finding_count"] > 100:
        print(f"... {report['finding_count'] - 100} more finding(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan commit-candidate files for sensitive values")
    parser.add_argument("paths", nargs="*", help="Optional files or directories to scan. Defaults to git commit candidates.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args(argv)

    paths = [Path(path) for path in args.paths] if args.paths else None
    report = build_report(scan_paths(paths))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
