"""Regression coverage for the single-file OP04 onboarding contract."""

from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

SPEC = importlib.util.spec_from_file_location(
    "validate_onboarding", SCRIPTS / "validate-onboarding.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
validate = MODULE.validate
RETIREMENT_SPEC = importlib.util.spec_from_file_location(
    "validate_retirement", SCRIPTS / "validate-retirement.py"
)
assert RETIREMENT_SPEC is not None and RETIREMENT_SPEC.loader is not None
RETIREMENT_MODULE = importlib.util.module_from_spec(RETIREMENT_SPEC)
RETIREMENT_SPEC.loader.exec_module(RETIREMENT_MODULE)
validate_retirement_change = RETIREMENT_MODULE.validate_retirement_change


PROJECT = "dev-project1-demo6"
IAM_PATH = "op04_manage_project/dev/dev-project1-demo6/iam.json"
RENDER_SCRIPT = SCRIPTS / "render-op04.py"
HANDOFF_SCRIPT = (
    SCRIPTS.parents[4]
    / "components/oci-landing-zone/scripts/render_project_handoff.py"
)
HANDOFF_SPEC = importlib.util.spec_from_file_location(
    "render_project_handoff", HANDOFF_SCRIPT
)
assert HANDOFF_SPEC is not None and HANDOFF_SPEC.loader is not None
HANDOFF_MODULE = importlib.util.module_from_spec(HANDOFF_SPEC)
HANDOFF_SPEC.loader.exec_module(HANDOFF_MODULE)
find_project_config = HANDOFF_MODULE.find_project_config


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, text=True, capture_output=True
    )
    return result.stdout.strip()


class ValidateOnboardingTests(unittest.TestCase):
    def test_accepts_one_new_project_iam_file_without_a_catalog(self) -> None:
        """The project directory must be the only onboarding declaration."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init", "--initial-branch=main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            git(repo, "remote", "add", "origin", "https://github.com/acme/lz.git")

            contract = {
                "contract_version": 4,
                "allowed_environments": ["dev", "test", "uat", "prod"],
                "environment_blueprints": {
                    "dev": "blueprints/dev/project-onboarding-environment.json"
                },
                "op04_generator": {
                    "repository": "oci-landing-zones/oci-landing-zone-operating-entities",
                    "release": "master",
                    "revision": "dab13856ba6701c45baafc163780bb76562c039a",
                    "adapter": "config/render.libsonnet",
                },
            }
            contract_path = repo / ".github/project-onboarding-contract.json"
            contract_path.parent.mkdir(parents=True)
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            blueprint_path = repo / "blueprints/dev/project-onboarding-environment.json"
            blueprint_path.parent.mkdir(parents=True)
            blueprint_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "environment": "dev",
                        "region": "eu-frankfurt-1",
                    }
                ),
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "base")
            base = git(repo, "rev-parse", "HEAD")
            git(repo, "switch", "-c", f"agent/project-onboard-{PROJECT}-{base[:12]}")

            manifest_path = repo / IAM_PATH
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "compartments_configuration": {"compartments": {}},
                        "identity_domain_groups_configuration": {"groups": {}},
                    }
                ),
                encoding="utf-8",
            )

            result = validate(repo, base, None, None)

            self.assertTrue(result["ok"])
            self.assertEqual(result["paths"], [IAM_PATH])
            self.assertEqual(
                result["summary"]["state_key"],
                "op04_manage_project/dev/dev-project1-demo6/terraform.tfstate",
            )


class RenderOp04Tests(unittest.TestCase):
    def test_renders_one_editable_iam_file_without_changing_the_catalog(self) -> None:
        """Onboarding must preserve the catalog and promote the OE baseline."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init", "--initial-branch=main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            git(repo, "remote", "add", "origin", "https://github.com/acme/lz.git")

            contract_path = repo / ".github/project-onboarding-contract.json"
            contract_path.parent.mkdir(parents=True)
            contract_path.write_text(
                json.dumps(
                    {
                        "contract_version": 4,
                        "allowed_environments": ["dev", "test", "uat", "prod"],
                        "environment_blueprints": {
                            "dev": "blueprints/dev/project-onboarding-environment.json"
                        },
                        "op04_generator": {
                            "repository": "oci-landing-zones/oci-landing-zone-operating-entities",
                            "release": "master",
                            "revision": "dab13856ba6701c45baafc163780bb76562c039a",
                            "adapter": "config/render.libsonnet",
                        },
                    }
                ),
                encoding="utf-8",
            )
            blueprint_path = repo / "blueprints/dev/project-onboarding-environment.json"
            blueprint_path.parent.mkdir(parents=True)
            blueprint_path.write_text(
                json.dumps(
                    {
                        "schema_version": 2,
                        "environment": "dev",
                        "region": "eu-frankfurt-1",
                    }
                ),
                encoding="utf-8",
            )
            catalog_path = repo / "config/projects.json"
            catalog_path.parent.mkdir()
            catalog = {"dev": [], "test": [], "uat": [], "prod": []}
            catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
            generator = repo / "scripts/generate_foundation.sh"
            generator.parent.mkdir()
            generator.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "mkdir -p op04_manage_project/dev/dev-project1-demo6/generated\n"
                "printf '%s\\n' '{\"compartments_configuration\":{},\"identity_domain_groups_configuration\":{}}' "
                "> op04_manage_project/dev/dev-project1-demo6/generated/iam.json\n",
                encoding="utf-8",
            )
            git(repo, "add", ".")
            git(repo, "commit", "-m", "base")
            base = git(repo, "rev-parse", "HEAD")
            git(repo, "switch", "-c", f"agent/project-onboard-{PROJECT}-{base[:12]}")

            result = subprocess.run(
                [
                    sys.executable,
                    str(RENDER_SCRIPT),
                    "--repo",
                    str(repo),
                    "--project",
                    PROJECT,
                    "--base-ref",
                    "main",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(catalog_path.read_text(encoding="utf-8")), catalog)
            self.assertTrue((repo / IAM_PATH).is_file())
            self.assertFalse((repo / f"{IAM_PATH.rsplit('/', 1)[0]}/generated").exists())
            self.assertEqual(
                git(repo, "status", "--porcelain", "--untracked-files=all"),
                f"?? {IAM_PATH}",
            )


class ValidateRetirementTests(unittest.TestCase):
    def test_accepts_deletion_of_one_project_iam_file(self) -> None:
        """Retiring a project must not require a duplicated catalog change."""
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            git(repo, "init", "--initial-branch=main")
            git(repo, "config", "user.email", "test@example.invalid")
            git(repo, "config", "user.name", "Test User")
            manifest_path = repo / IAM_PATH
            manifest_path.parent.mkdir(parents=True)
            manifest_path.write_text("{}\n", encoding="utf-8")
            git(repo, "add", ".")
            git(repo, "commit", "-m", "project foundation")
            base = git(repo, "rev-parse", "HEAD")

            manifest_path.unlink()

            validate_retirement_change(repo, base, PROJECT)


class HandoffConfigTests(unittest.TestCase):
    def test_reads_the_direct_editable_project_iam_file(self) -> None:
        """Handoff must use the same IAM file that OP04 applies."""
        with tempfile.TemporaryDirectory() as temp:
            project_directory = Path(temp)
            iam = {
                "compartments_configuration": {"compartments": {}},
                "identity_domain_groups_configuration": {"groups": {}},
            }
            (project_directory / "iam.json").write_text(
                json.dumps(iam), encoding="utf-8"
            )

            self.assertEqual(find_project_config(project_directory), iam)


if __name__ == "__main__":
    unittest.main()
