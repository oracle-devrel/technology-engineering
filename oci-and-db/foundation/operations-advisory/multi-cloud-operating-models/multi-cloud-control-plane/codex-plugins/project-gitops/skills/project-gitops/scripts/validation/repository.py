"""Fail-closed collection of one governed repository change."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import os
from pathlib import Path

from .common import (
    BASE_REF_RE, BRANCH_PATTERN, EXECUTABLE_GIT_CONFIG_PATTERN, MAX_HANDOFF_BYTES,
    MAX_JSON_BYTES, PATH_PATTERN, RepositoryChange, SAFE_COMMAND_CONFIG_KEYS, SHA_RE,
    SHA256_RE, ValidationFailure, decode_text, failure, run_git, strict_json,
)
from .handoff import safe_file, validate_handoff
from .identity import parse_origin
from .preview import render_diff

_decode_text = decode_text
_failure = failure
_safe_file = safe_file
_render_diff = render_diff
_SAFE_COMMAND_CONFIG_KEYS = SAFE_COMMAND_CONFIG_KEYS
_EXECUTABLE_GIT_CONFIG_PATTERN = EXECUTABLE_GIT_CONFIG_PATTERN


def decode_git(output: bytes) -> str:
    return _decode_text(output, "INVALID_GIT_OUTPUT", "Git returned invalid text.")


def validated_repository(repo: str | os.PathLike[str]) -> Path:
    absolute = Path(os.path.abspath(os.fspath(Path(repo))))
    try:
        resolved = absolute.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ValidationFailure("INVALID_REPOSITORY", "Repository worktree is invalid.") from exc
    if absolute.is_symlink() or not resolved.is_dir():
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    if (resolved / ".git").is_symlink():
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    top_level = decode_git(run_git(resolved, "rev-parse", "--show-toplevel")).strip()
    if not top_level:
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    try:
        git_root = Path(os.path.abspath(top_level)).resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ValidationFailure(
            "INVALID_REPOSITORY", "Repository worktree is invalid."
        ) from exc
    if git_root != resolved:
        _failure("INVALID_REPOSITORY", "Repository worktree is invalid.")
    return resolved


def validate_base_ref(base_ref: str) -> None:
    if (BASE_REF_RE.fullmatch(base_ref) is None or ".." in base_ref
            or "//" in base_ref or base_ref.endswith("/")):
        _failure("INVALID_BASE_REF", "The base reference is invalid.")


def resolve_base_sha(repository: Path, base_ref: str) -> str:
    validate_base_ref(base_ref)
    base_sha = decode_git(run_git(repository, "rev-parse", f"{base_ref}^{{commit}}")).strip()
    if SHA_RE.fullmatch(base_sha) is None:
        _failure("INVALID_BASE_SHA", "The base commit is invalid.")
    return base_sha


def porcelain_path(status_output: bytes) -> tuple[str, str]:
    records = status_output.split(b"\0")
    if records[-1] != b"":
        _failure("INVALID_CHANGE", "The repository change is invalid.")
    records = records[:-1]
    if len(records) != 1:
        _failure("INVALID_CHANGE", "Exactly one manifest must be modified.")
    record = records[0]
    if (
        len(record) < 4
        or record[2:3] != b" "
        or record[:2] not in (b" M", b"M ", b"MM", b"??")
    ):
        _failure("INVALID_CHANGE", "The manifest change is not allowed.")
    try:
        return (
            record[3:].decode("utf-8", errors="strict"),
            record[:2].decode("ascii", errors="strict"),
        )
    except UnicodeDecodeError as exc:
        raise ValidationFailure("INVALID_CHANGE", "The repository change is invalid.") from exc


def validate_effective_git_config(repository: Path) -> None:
    output = decode_git(run_git(repository, "config", "--includes", "--show-scope",
                                "--name-only", "--list"))
    for raw_record in output.splitlines():
        try:
            raw_scope, raw_key = raw_record.split("\t", 1)
        except ValueError as exc:
            raise ValidationFailure("INVALID_GIT_OUTPUT",
                                    "Git returned invalid configuration data.") from exc
        normalized_scope = raw_scope.strip().casefold()
        normalized_key = raw_key.strip().casefold()
        if normalized_scope == "command" and normalized_key in _SAFE_COMMAND_CONFIG_KEYS:
            continue
        if _EXECUTABLE_GIT_CONFIG_PATTERN.fullmatch(normalized_key):
            _failure("UNSAFE_GIT_CONFIG",
                     "Executable repository Git configuration is not allowed.")


def validate_preview(change: RepositoryChange, expect_base_sha: str | None,
                     expect_content_sha256: str | None) -> None:
    if expect_base_sha is None:
        return
    if (SHA_RE.fullmatch(expect_base_sha) is None
            or SHA256_RE.fullmatch(expect_content_sha256 or "") is None
            or expect_base_sha != change.base_sha
            or expect_content_sha256
            != hashlib.sha256(change.candidate_content).hexdigest()):
        _failure("PREVIEW_DRIFT", "The expected preview no longer matches.")


def validate_expected_base(expected_base_sha: str, current_base_sha: str) -> None:
    if SHA_RE.fullmatch(expected_base_sha) is None or expected_base_sha != current_base_sha:
        _failure("PREVIEW_DRIFT", "The expected preview no longer matches.")


def finalize_change(change: RepositoryChange) -> RepositoryChange:
    if change.base_content:
        strict_json(change.base_content)
    strict_json(change.candidate_content)
    return replace(
        change,
        diff=_render_diff(change.path, change.base_content, change.candidate_content),
    )


def collect_change(
    repo: str | os.PathLike[str],
    base_ref: str,
) -> RepositoryChange:
    """Collect one stable read-only canonical manifest modification."""
    repository = validated_repository(repo)
    origin = decode_git(run_git(repository, "remote", "get-url", "origin")).strip()
    organization, project = parse_origin(origin)
    branch = decode_git(run_git(repository, "branch", "--show-current")).strip()
    if branch == "main" or BRANCH_PATTERN.fullmatch(branch) is None:
        _failure("INVALID_BRANCH", "The current branch is not allowed.")
    base_sha = resolve_base_sha(repository, base_ref)
    validate_effective_git_config(repository)
    path, status = porcelain_path(
        run_git(
            repository,
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "-z",
        )
    )
    path_match = PATH_PATTERN.fullmatch(path)
    if path_match is None:
        _failure("INVALID_MANIFEST_PATH", "The modified manifest path is not allowed.")
    environment = path_match.group("environment")
    cloud = path_match.group("cloud")
    if cloud == "oci":
        workload_compartments = validate_handoff(repository, project, environment)
    else:
        workload_compartments = {}
        handoff_content = _safe_file(
            repository,
            f"environments/{environment}/environment_information.md",
            size_limit=MAX_HANDOFF_BYTES,
        )
        handoff_text = _decode_text(
            handoff_content, "INVALID_HANDOFF", "Project handoff is invalid."
        )
        if "<fill during handoff>" in handoff_text.casefold():
            _failure("INVALID_HANDOFF", "Project handoff is incomplete or invalid.")
    kind = path_match.group("kind")
    is_new = status == "??"
    if is_new and not kind.startswith("lifecycle_operations/"):
        _failure(
            "INVALID_CHANGE",
            "Only a canonical lifecycle operation manifest may be added.",
        )
    expected_resource = {
        "database/database.json": "adb",
        "workloads/adb.json": "adb",
        "compute/compute.json": "vm",
        "network/project-nsgs.json": "nsg",
        "lifecycle_operations/adb-lifecycle.json": "adb",
    }[kind]
    if not branch.startswith(f"agent/{expected_resource}-"):
        _failure("INVALID_BRANCH", "The current branch does not match the manifest resource.")
    candidate_content = _safe_file(repository, path, size_limit=MAX_JSON_BYTES)
    name_status = decode_git(run_git(
        repository, "diff", "--name-status", "--no-renames", base_sha))
    if is_new:
        base_entry = decode_git(
            run_git(repository, "ls-tree", "--name-only", base_sha, "--", path)
        )
        if name_status or base_entry:
            _failure(
                "INVALID_CHANGE",
                "Exactly one new lifecycle operation manifest must be added.",
            )
    elif name_status != f"M\t{path}\n":
        _failure("INVALID_CHANGE", "Exactly one existing manifest must be modified.")
    run_git(repository, "diff", "--check", base_sha)
    inspection_diff = (
        b""
        if is_new
        else run_git(
            repository,
            "diff",
            "--no-ext-diff",
            "--no-textconv",
            "--no-color",
            base_sha,
            "--",
            path,
        )
    )
    verified_candidate_content = _safe_file(repository, path, size_limit=MAX_JSON_BYTES)
    if verified_candidate_content != candidate_content:
        _failure("WORKTREE_CHANGED", "The worktree changed during validation.")
    if any(
        line == b"GIT binary patch"
        or (line.startswith(b"Binary files ") and line.endswith(b" differ"))
        for line in inspection_diff.splitlines()
    ):
        _failure("BINARY_DIFF", "Binary manifest diffs are not allowed.")
    base_content = b"" if is_new else run_git(repository, "show", f"{base_sha}:{path}")
    region = path_match.group("region")
    return RepositoryChange(
        repo=repository, project=project, branch=branch, base_ref=base_ref,
        base_sha=base_sha, path=path, environment=environment, region=region,
        kind=kind,
        base_content=base_content, candidate_content=candidate_content, diff="",
        workload_compartments=workload_compartments, organization=organization)
