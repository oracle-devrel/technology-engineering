import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "components"
VALIDATOR = (
    ROOT
    / "plugins"
    / "project-gitops"
    / "skills"
    / "project-gitops"
    / "scripts"
    / "validate-change.py"
)


def load_validator():
    spec = importlib.util.spec_from_file_location("packaged_validate_change", VALIDATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load packaged validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class SecurityProfileTests(unittest.TestCase):
    def test_templates_default_to_recommended_profile(self):
        for template in ("nonprod-project-template", "prod-project-template"):
            contract = json.loads(
                (COMPONENTS / template / "control-plane.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(contract["security_profile"], "github-environments")

    def test_hardened_callers_resolve_repository_profile(self):
        workflows = (
            COMPONENTS / "nonprod-project-template" / ".github/workflows/terraform.yaml",
            COMPONENTS / "nonprod-project-template" / ".github/workflows/ansible.yaml",
            COMPONENTS / "prod-project-template" / ".github/workflows/terraform.yaml",
        )
        for workflow_path in workflows:
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn("pull_request_target:", workflow)
            self.assertIn('test "$all_changed" = "$changed"', workflow)
            self.assertIn("git ls-tree", workflow)
            self.assertIn("jq -e .", workflow)
            self.assertIn("platform_ci_ref:", workflow)
            self.assertIn("manifest_ref:", workflow)
            self.assertIn("security_profile:", workflow)

    def test_production_day2_is_rejected_and_has_no_caller(self):
        validator = load_validator()
        with self.assertRaises(validator.ValidationFailure) as raised:
            validator.validate_manifest_scope(
                "prod", "lifecycle_operations/adb-lifecycle.json"
            )
        self.assertEqual(raised.exception.code, "UNSUPPORTED_PRODUCTION_DAY2")
        self.assertFalse(
            (
                COMPONENTS
                / "prod-project-template"
                / ".github"
                / "workflows"
                / "ansible.yaml"
            ).exists()
        )

    def test_environment_profile_records_only_execution_deployments(self):
        terraform = (
            COMPONENTS / "platform-ci" / ".github/workflows/terraform-shared.yaml"
        ).read_text(encoding="utf-8")
        ansible = (
            COMPONENTS / "platform-ci" / ".github/workflows/ansible-shared.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("inputs.mode == 'apply'", terraform)
        self.assertIn("inputs.mode == 'execute'", ansible)

    def test_reusable_workflow_enforces_exclusive_secret_sources(self):
        terraform = (
            COMPONENTS / "platform-ci" / ".github/workflows/terraform-shared.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("ENVIRONMENT_SECRET_VALUES", terraform)
        self.assertIn("REPOSITORY_SECRET_VALUES", terraform)
        self.assertIn('test -z "$REPOSITORY_SECRET_VALUES"', terraform)
        self.assertIn('test -z "$ENVIRONMENT_SECRET_VALUES"', terraform)
        self.assertIn("secrets.GITOPS_SECRET_VALUES", terraform)
        self.assertIn("secrets.repository_secret_values", terraform)
        self.assertNotIn("secrets: inherit", terraform)
        self.assertNotIn("toJSON(secrets)", terraform)


if __name__ == "__main__":
    unittest.main()
