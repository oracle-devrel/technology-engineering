"""Safe reading and validation of project handoff information."""

from __future__ import annotations

import ipaddress
import os
from pathlib import Path
import re
import stat

from .common import (
    REGION_PATTERN,
    ValidationFailure,
    decode_text,
    failure,
    valid_ocid,
)


MAX_HANDOFF_BYTES = 65_536
_failure = failure
_decode_text = decode_text
_valid_ocid = valid_ocid


def safe_file(repo: Path, relative_path: str, *, size_limit: int) -> bytes:
    """Read one regular repository file without following symlinks."""
    relative = Path(relative_path)
    if (relative.is_absolute() or not relative.parts or ".." in relative.parts
            or size_limit < 0):
        _failure("INVALID_PATH", "A repository path is invalid.")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    directory_descriptors: list[int] = []
    file_descriptor: int | None = None
    try:
        directory_descriptors.append(os.open(repo, directory_flags))
        for component in relative.parts[:-1]:
            directory_descriptors.append(
                os.open(component, directory_flags, dir_fd=directory_descriptors[-1]))
        file_descriptor = os.open(
            relative.parts[-1], file_flags, dir_fd=directory_descriptors[-1])
        stat_result = os.fstat(file_descriptor)
        if not stat.S_ISREG(stat_result.st_mode):
            _failure("INVALID_PATH", "A repository file is invalid.")
        if stat_result.st_size > size_limit:
            _failure("FILE_SIZE_LIMIT", "A repository file exceeded its size limit.")
        chunks: list[bytes] = []
        remaining = size_limit + 1
        while remaining:
            chunk = os.read(file_descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > size_limit:
            _failure("FILE_SIZE_LIMIT", "A repository file exceeded its size limit.")
        return content
    except ValidationFailure:
        raise
    except (OSError, ValueError) as exc:
        raise ValidationFailure("INVALID_PATH", "A repository file is invalid.") from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        for descriptor in reversed(directory_descriptors):
            os.close(descriptor)


def validate_handoff(repo: Path, project: str, environment: str) -> dict[str, str]:
    """Validate the human-only project handoff marker without parsing it as input."""
    layout = project.split("-", 1)[0]
    if (
        (layout == "prod" and environment != "prod")
        or (layout == "nonprod" and environment not in {"dev", "test", "uat"})
    ):
        _failure("INVALID_HANDOFF", "Project environment does not match its repository.")
    content = safe_file(
        repo,
        f"environments/{environment}/environment_information.md",
        size_limit=MAX_HANDOFF_BYTES,
    )
    text = _decode_text(content, "INVALID_HANDOFF", "Project handoff is invalid.")
    if "<fill during handoff>" in text.casefold():
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    rows: dict[str, list[list[str]]] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if not cells or all(re.fullmatch(r"-+", cell) is not None for cell in cells):
            continue
        rows.setdefault(cells[0], []).append(cells[1:])

    def one_row(label: str, length: int) -> list[str] | None:
        matches = rows.get(label, [])
        if len(matches) != 1 or len(matches[0]) != length:
            return None
        return matches[0]

    project_match = re.search(r"project(?P<number>[0-9]+)$", project)
    project_key = project.split("-", 1)[-1]
    short_project = f"proj{project_match.group('number')}" if project_match else ""
    project_row = one_row("Project", 1)
    environment_row = one_row("Environment", 1)
    region_row = one_row("OCI region", 1)
    if (
        project_row is None
        or project_row[0] not in (short_project, project_key, project)
        or environment_row != [environment]
        or region_row is None
        or REGION_PATTERN.fullmatch(region_row[0]) is None
    ):
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    region = region_row[0]
    compartment_rows = {
        "project_root": "Project root",
        "application": "App compartment",
        "database": "DB compartment",
        "infrastructure": "Infra compartment",
    }
    compartments: dict[str, str] = {}
    for role, label in compartment_rows.items():
        row = one_row(label, 2)
        if row is None or not _valid_ocid(row[-1], "compartment"):
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
        compartments[role] = row[-1]
    if len(set(compartments.values())) != 4:
        _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    for label, kind in (
        ("Projects VCN", "vcn"),
        ("Web subnet", "subnet"),
        ("App subnet", "subnet"),
        ("DB subnet", "subnet"),
        ("Infra subnet", "subnet"),
    ):
        row = one_row(label, 4)
        if row is None or not _valid_ocid(row[-1], kind, region):
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
        try:
            network = ipaddress.ip_network(row[-2], strict=True)
        except ValueError as exc:
            raise ValidationFailure(
                "INVALID_HANDOFF", "Project handoff is incomplete or invalid."
            ) from exc
        if str(network) != row[-2]:
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    return compartments
