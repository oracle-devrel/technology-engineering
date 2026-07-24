#!/usr/bin/env python3
"""Render one project repository from its pinned template and handoff."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

from project_repository_contract import (
    RepositoryContractError,
    git,
    load_initialization,
    render_codeowners,
    validate_origin,
    validate_template_placeholders,
)


def regular_file(path: Path) -> bool:
    try:
        return stat.S_ISREG(path.lstat().st_mode)
    except OSError:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--deployment-contract", required=True)
    parser.add_argument("--handoff-json", required=True)
    parser.add_argument("--handoff-markdown", required=True)
    parser.add_argument("--project", required=True)
    args = parser.parse_args()
    try:
        repo = Path(os.path.abspath(args.repo)).resolve()
        if (
            not repo.is_dir()
            or Path(
                git(repo, "rev-parse", "--show-toplevel").strip()
            ).resolve()
            != repo
            or git(
                repo,
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
            ).strip()
        ):
            raise RepositoryContractError(
                "The project repository must be a clean Git worktree."
            )
        deployment_contract = Path(
            os.path.abspath(args.deployment_contract)
        )
        handoff_json = Path(os.path.abspath(args.handoff_json))
        handoff_markdown = Path(
            os.path.abspath(args.handoff_markdown)
        )
        initialization = load_initialization(
            deployment_contract,
            handoff_json,
            args.project,
        )
        validate_origin(repo, initialization)
        validate_template_placeholders(repo, initialization)
        validator = Path(__file__).with_name("validate-handoff.py")
        validation = subprocess.run(
            [
                sys.executable,
                str(validator),
                "--handoff-json",
                str(handoff_json),
                "--handoff-markdown",
                str(handoff_markdown),
                "--project",
                args.project,
            ],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        if validation.returncode:
            raise RepositoryContractError(
                "The source handoff artifacts are invalid."
            )
        control_plane_path = repo / "control-plane.json"
        codeowners_template_path = repo / ".github/CODEOWNERS.template"
        codeowners_path = repo / ".github/CODEOWNERS"
        handoff_path = repo / initialization.handoff_path
        if (
            not regular_file(control_plane_path)
            or not regular_file(codeowners_template_path)
            or codeowners_path.exists()
            or not regular_file(handoff_path)
            or not regular_file(handoff_markdown)
        ):
            raise RepositoryContractError(
                "The pinned project template tree is invalid."
            )
        control_plane = json.loads(
            control_plane_path.read_text(encoding="utf-8")
        )
        expected_template_target = (
            f"{'prod' if initialization.identity.environment == 'prod' else 'nonprod'}"
            "-__PROJECT__"
        )
        if (
            control_plane.get("repository_layout")
            != initialization.repository_layout
            or control_plane.get("target_repository")
            != expected_template_target
            or control_plane.get("security_profile")
            not in {"github-environments", "repository-secrets"}
        ):
            raise RepositoryContractError(
                "The protected project template contract is invalid."
            )
        codeowners = render_codeowners(
            codeowners_template_path.read_text(encoding="utf-8"),
            initialization,
        )
        control_plane["target_repository"] = (
            initialization.target_repository
        )
        control_plane["security_profile"] = (
            initialization.security_profile
        )
        control_plane_path.write_text(
            json.dumps(control_plane, indent=2) + "\n",
            encoding="utf-8",
        )
        codeowners_path.write_text(codeowners, encoding="utf-8")
        codeowners_template_path.unlink()
        handoff_path.write_bytes(handoff_markdown.read_bytes())
        print(
            json.dumps(
                {
                    "ok": True,
                    "project": args.project,
                    "target_repository":
                        initialization.target_repository,
                    "security_profile":
                        initialization.security_profile,
                    "handoff_path": initialization.handoff_path,
                },
                separators=(",", ":"),
            )
        )
        return 0
    except (
        RepositoryContractError,
        OSError,
        json.JSONDecodeError,
    ) as exc:
        print(
            json.dumps(
                {"ok": False, "error": " ".join(str(exc).split())[:256]},
                separators=(",", ":"),
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
