"""
File name: dep_license_check.py
Author: L. Saetta
Date last modified: 2026-01-12
Python Version: 3.11
License: MIT

Description:
    Checks licenses for dependencies listed in requirements.txt (direct deps).

    Primary source:
    - Installed package metadata (importlib.metadata)

    Fallback source (when installed metadata cannot determine license):
    - PyPI JSON API for the *installed version* (best-effort)

    Limitations:
    - If dependencies are not installed in the environment running the agent, licenses will be NOT_INSTALLED.
    - Requirements parsing is intentionally conservative; complex pip options are ignored.
    - PyPI fallback requires network access and relies on PyPI metadata quality.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Iterable

from agent.utils import get_console_logger


logger = get_console_logger()

# ---- Data models ----


@dataclass(frozen=True)
class DepLicenseInfo:
    requirement: str  # original requirement line (cleaned)
    distribution: str  # normalized dist name (best-effort)
    version: str | None
    license: str  # normalized license id or UNKNOWN/NOT_INSTALLED
    source: str  # license_field | classifier | pypi_json | unknown | not_installed


@dataclass(frozen=True)
class DepLicenseCheckResult:
    ok: bool
    deps: list[DepLicenseInfo]
    failures: list[DepLicenseInfo]
    warnings: list[DepLicenseInfo]
    message: str


# ---- Requirements parsing (direct deps only) ----

_REQ_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")  # dist name at start
_IGNORE_PREFIXES = (
    "-r",
    "--requirement",
    "--index-url",
    "--extra-index-url",
    "--find-links",
    "--trusted-host",
)


def parse_requirements_txt(text: str) -> list[str]:
    """
    Returns cleaned requirement lines (direct deps).
    Ignores comments, empty lines, and pip options.
    Keeps markers/extras/version pins as part of the requirement string, but extracts dist name separately later.
    """
    reqs: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith(_IGNORE_PREFIXES):
            # conservative: ignore includes and index directives
            continue
        # drop inline comments: "pkg==1.2  # comment"
        if " #" in line:
            line = line.split(" #", 1)[0].rstrip()
        reqs.append(line)
    return reqs


def extract_dist_name(requirement: str) -> str | None:
    """
    Best-effort extraction of distribution name from a requirement line.
    Handles:
      - requests==2.32.3
      - pydantic>=2
      - fastapi[standard]>=0.100
      - package ; python_version < "3.12"
    """
    # Strip environment marker
    base = requirement.split(";", 1)[0].strip()
    # Strip extras
    base = base.split("[", 1)[0].strip()
    m = _REQ_NAME_RE.match(base)
    if not m:
        return None
    return m.group(1)


# ---- License extraction helpers ----


def _normalize_license_string(s: str) -> str:
    """
    Normalize common license strings to SPDX-ish ids.
    Keep it conservative; expand mapping as you need.
    """
    v = (s or "").strip()
    if not v:
        return "UNKNOWN"

    u = v.upper().strip()
    if u in {"UNKNOWN", "NONE", "N/A"}:
        return "UNKNOWN"

    # Common normalizations
    # for now I don't want to add GPL
    mapping = {
        # Apache
        "APACHE": "Apache-2.0",
        "APACHE 2.0": "Apache-2.0",
        "APACHE-2.0": "Apache-2.0",
        "APACHE SOFTWARE LICENSE": "Apache-2.0",
        # MIT
        "MIT": "MIT",
        "MIT LICENSE": "MIT",
        # BSD
        "BSD": "BSD",
        # BSD variants commonly seen in metadata
        "MODIFIED BSD LICENSE": "BSD",
        "NEW BSD LICENSE": "BSD-3-Clause",
        "REVISED BSD LICENSE": "BSD-3-Clause",
        "BSD-3-CLAUSE": "BSD-3-Clause",
        "BSD 3-CLAUSE": "BSD-3-Clause",
        "BSD-2-CLAUSE": "BSD-2-Clause",
        "BSD 2-CLAUSE": "BSD-2-Clause",
        # ISC
        "ISC": "ISC",
        # MPL
        "MPL 2.0": "MPL-2.0",
        "MPL-2.0": "MPL-2.0",
        "MOZILLA PUBLIC LICENSE 2.0": "MPL-2.0",
        # UPL (Oracle / Universal Permissive License)
        "UPL-1.0": "UPL-1.0",
        "UPL 1.0": "UPL-1.0",
        "UNIVERSAL PERMISSIVE LICENSE 1.0": "UPL-1.0",
        "UNIVERSAL PERMISSIVE LICENSE (UPL) 1.0": "UPL-1.0",
    }

    if "MODIFIED BSD" in u:
        return "BSD"

    if u in mapping:
        return mapping[u]

    # Substring matches
    if "APACHE" in u and "2" in u:
        return "Apache-2.0"
    if "MIT" in u:
        return "MIT"
    if "BSD" in u and "3" in u:
        return "BSD-3-Clause"
    if "BSD" in u and "2" in u:
        return "BSD-2-Clause"
    if "MPL" in u and "2" in u:
        return "MPL-2.0"
    if "ISC" in u:
        return "ISC"
    if "UPL" in u:
        return "UPL-1.0"

    # Keep original (but trimmed) if it looks like an SPDX-ish token
    if re.fullmatch(r"[A-Za-z0-9.\-+]+", v):
        return v

    return v  # last resort


def _license_from_classifiers(classifiers: Iterable[str]) -> str | None:
    """
    Map Trove classifiers to normalized license ids.
    """
    trove_map = {
        "License :: OSI Approved :: MIT License": "MIT",
        "License :: OSI Approved :: Apache Software License": "Apache-2.0",
        "License :: OSI Approved :: BSD License": "BSD",
        "License :: OSI Approved :: ISC License (ISCL)": "ISC",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
        'License :: OSI Approved :: BSD 3-Clause "New" or "Revised" License': "BSD-3-Clause",
        'License :: OSI Approved :: BSD 2-Clause "Simplified" License': "BSD-2-Clause",
        # Note: UPL does not reliably appear as a Trove classifier; use license_expression instead.
    }
    for c in classifiers:
        c = c.strip()
        if c in trove_map:
            return trove_map[c]

    # fallback: keyword scan
    for c in classifiers:
        u = c.upper()
        if "LICENSE ::" not in u:
            continue
        if "MIT" in u:
            return "MIT"
        if "APACHE" in u:
            return "Apache-2.0"
        if "BSD 3-CLAUSE" in u or ("BSD" in u and "3" in u):
            return "BSD-3-Clause"
        if "BSD 2-CLAUSE" in u or ("BSD" in u and "2" in u):
            return "BSD-2-Clause"
        if "MPL" in u and "2" in u:
            return "MPL-2.0"
        if "ISC" in u:
            return "ISC"
    return None


def _normalize_dist_for_pypi(name: str) -> str:
    """
    Normalize project name for PyPI URLs (PEP 503-ish):
    lowercase and replace runs of [-_.] with '-'.
    """
    return re.sub(r"[-_.]+", "-", name.strip().lower())


# Simple in-process cache to avoid repeated HTTP calls
_PYPI_LICENSE_CACHE: dict[tuple[str, str | None], str | None] = {}


def _license_from_pypi_json(payload: dict[str, Any]) -> str | None:
    """
    Extract license from PyPI JSON payload (best-effort), including PEP 639 fields.

    Returns a normalized license string (e.g., 'UPL-1.0', 'MIT', 'Apache-2.0') or None.
    """
    info = payload.get("info") or {}

    # 1) PEP 639: license_expression (preferred)
    lic_expr = (info.get("license_expression") or "").strip()
    if lic_expr:
        lic_norm = _normalize_license_string(lic_expr)
        if lic_norm != "UNKNOWN":
            return lic_norm

    # 2) Alternative shape: info.license could be a dict with expression
    lic_obj = info.get("license")
    if isinstance(lic_obj, dict):
        expr = (lic_obj.get("expression") or "").strip()
        if expr:
            expr_norm = _normalize_license_string(expr)
            if expr_norm != "UNKNOWN":
                return expr_norm

    # 3) Trove classifiers
    classifiers = info.get("classifiers") or []
    lic = _license_from_classifiers(classifiers)
    if lic:
        return lic

    # 4) Legacy string field: info.license
    if isinstance(lic_obj, str):
        lic_raw = lic_obj.strip()
    else:
        lic_raw = (info.get("license") or "").strip()

    if lic_raw:
        lic_norm = _normalize_license_string(lic_raw)
        if lic_norm != "UNKNOWN":
            return lic_norm

    return None


def _get_license_from_pypi(
    dist_name: str, version: str | None, *, timeout_s: int = 5
) -> str | None:
    """
    Best-effort PyPI fallback: query PyPI JSON API for the given dist and (if provided) version.

    Returns a normalized license string, or None if not found / network error / ambiguous.
    """
    key = (dist_name, version)
    if key in _PYPI_LICENSE_CACHE:
        return _PYPI_LICENSE_CACHE[key]

    pypi_name = _normalize_dist_for_pypi(dist_name)

    # Prefer version-specific endpoint for determinism.
    if version:
        url = f"https://pypi.org/pypi/{pypi_name}/{version}/json"
    else:
        url = f"https://pypi.org/pypi/{pypi_name}/json"

    logger.info("   Fetching license info from PyPI for %s", dist_name)

    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "code-quality-agent/1.0 (license-check)",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        _PYPI_LICENSE_CACHE[key] = None
        return None

    lic = _license_from_pypi_json(data)
    _PYPI_LICENSE_CACHE[key] = lic
    return lic


def extract_pinned_version(requirement: str) -> str | None:
    """
    Extracts the pinned version from a requirement line if it uses '=='.
    Returns None if no pinned version is found.
    """
    base = requirement.split(";", 1)[0].strip()
    m = re.search(r"==\s*([A-Za-z0-9][A-Za-z0-9.\-+]*)", base)
    return m.group(1) if m else None


def get_installed_dist_license(
    dist_name: str, *, version_hint: str | None = None
) -> DepLicenseInfo:
    """
    dist_name is a distribution name (best-effort).

    Returns DepLicenseInfo with license info from installed metadata.
    If not installed, tries PyPI fallback (prefer version_hint if provided).
    If license cannot be determined, license is UNKNOWN.
    """
    try:
        md = metadata.metadata(dist_name)
        ver = metadata.version(dist_name)
        installed = True
    except metadata.PackageNotFoundError:
        md = None
        ver = None
        installed = False

    # CHANGE: If not installed, try PyPI fallback instead of returning immediately
    if not installed:
        lic_web = _get_license_from_pypi(dist_name, version_hint)
        if lic_web:
            return DepLicenseInfo(
                requirement=dist_name,
                distribution=dist_name,
                version=version_hint,
                license=lic_web,
                source="pypi_json",
            )
        return DepLicenseInfo(
            requirement=dist_name,
            distribution=dist_name,
            version=version_hint,
            license="NOT_INSTALLED",
            source="not_installed",
        )

    # 1) Local metadata: License field
    lic_raw = (md.get("License") or "").strip()
    lic = _normalize_license_string(lic_raw)
    if lic not in {"UNKNOWN"} and lic_raw:
        return DepLicenseInfo(
            requirement=dist_name,
            distribution=dist_name,
            version=ver,
            license=lic,
            source="license_field",
        )

    # 2) Local metadata: Trove classifiers
    classifiers = md.get_all("Classifier") or []
    lic2 = _license_from_classifiers(classifiers)
    if lic2:
        return DepLicenseInfo(
            requirement=dist_name,
            distribution=dist_name,
            version=ver,
            license=lic2,
            source="classifier",
        )

    # CHANGE: PyPI fallback when local metadata is insufficient (license would be UNKNOWN)
    lic3 = _get_license_from_pypi(dist_name, ver)
    if lic3:
        return DepLicenseInfo(
            requirement=dist_name,
            distribution=dist_name,
            version=ver,
            license=lic3,
            source="pypi_json",
        )

    return DepLicenseInfo(
        requirement=dist_name,
        distribution=dist_name,
        version=ver,
        license="UNKNOWN",
        source="unknown",
    )


def check_dependency_licenses(
    *,
    requirements_text: str,
    accepted_licenses: set[str],
    fail_on_unknown: bool,
    fail_on_not_installed: bool,
) -> DepLicenseCheckResult:
    req_lines = parse_requirements_txt(requirements_text)

    infos: list[DepLicenseInfo] = []
    failures: list[DepLicenseInfo] = []
    warnings: list[DepLicenseInfo] = []

    # Process each requirement in requirements.txt
    for req in req_lines:
        dist = extract_dist_name(req)
        if not dist:
            warnings.append(
                DepLicenseInfo(
                    requirement=req,
                    distribution="(unparsed)",
                    version=None,
                    license="UNKNOWN",
                    source="unknown",
                )
            )
            continue

        pinned = extract_pinned_version(req)
        info = get_installed_dist_license(dist, version_hint=pinned)

        # Keep original requirement for traceability
        info = DepLicenseInfo(
            requirement=req,
            distribution=info.distribution,
            version=info.version,
            license=info.license,
            source=info.source,
        )
        infos.append(info)

        # Evaluate
        if info.license == "NOT_INSTALLED":
            if fail_on_not_installed:
                failures.append(info)
            else:
                warnings.append(info)
            continue

        if info.license == "UNKNOWN" or info.license == "BSD":
            # BSD is ambiguous; treat as warning unless you explicitly allow "BSD"
            if info.license in accepted_licenses:
                continue
            if fail_on_unknown:
                failures.append(info)
            else:
                warnings.append(info)
            continue

        if info.license not in accepted_licenses:
            failures.append(info)

    ok = len(failures) == 0
    msg = (
        f"Checked {len(infos)} direct dependencies from requirements.txt. "
        f"Failures: {len(failures)}. Warnings: {len(warnings)}."
    )
    return DepLicenseCheckResult(
        ok=ok, deps=infos, failures=failures, warnings=warnings, message=msg
    )
