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
        self.assertIn("terraform-environments:", terraform)
        self.assertIn("terraform-repository:", terraform)
        self.assertIn("ansible-environments:", ansible)
        self.assertIn("ansible-repository:", ansible)
        self.assertIn("format('{0}-apply', inputs.environment_name)", terraform)
        self.assertIn("deployment: ${{ inputs.mode == 'apply' }}", terraform)
        self.assertIn("format('{0}-apply', inputs.environment_name)", ansible)
        self.assertIn("deployment: ${{ inputs.mode == 'execute' }}", ansible)
        self.assertNotIn("|| null", terraform)
        self.assertNotIn("|| null", ansible)

        terraform_repository = terraform.split("  terraform-repository:", 1)[1]
        ansible_repository = ansible.split("  ansible-repository:", 1)[1]
        self.assertNotIn("\n    environment:", terraform_repository)
        self.assertNotIn("\n    environment:", ansible_repository)

    def test_execution_steps_are_defined_once_in_composite_actions(self):
        terraform_workflow = (
            COMPONENTS / "platform-ci" / ".github/workflows/terraform-shared.yaml"
        ).read_text(encoding="utf-8")
        ansible_workflow = (
            COMPONENTS / "platform-ci" / ".github/workflows/ansible-shared.yaml"
        ).read_text(encoding="utf-8")
        terraform_action = (
            COMPONENTS / "platform-ci" / "actions/terraform-execution/action.yml"
        ).read_text(encoding="utf-8")
        ansible_action = (
            COMPONENTS / "platform-ci" / "actions/ansible-execution/action.yml"
        ).read_text(encoding="utf-8")

        self.assertEqual(terraform_workflow.count("Execute Terraform"), 2)
        self.assertEqual(ansible_workflow.count("Execute Ansible"), 2)
        self.assertNotIn("Terraform plan", terraform_workflow)
        self.assertNotIn("Ansible check", ansible_workflow)
        self.assertIn("using: composite", terraform_action)
        self.assertIn("using: composite", ansible_action)
        self.assertEqual(terraform_action.count("- name: Terraform plan"), 1)
        self.assertEqual(ansible_action.count("- name: Ansible check"), 1)

    def test_reusable_workflow_enforces_exclusive_secret_sources(self):
        terraform = (
            COMPONENTS / "platform-ci" / ".github/workflows/terraform-shared.yaml"
        ).read_text(encoding="utf-8")
        terraform_action = (
            COMPONENTS / "platform-ci" / "actions/terraform-execution/action.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("ENVIRONMENT_SECRET_VALUES", terraform_action)
        self.assertIn("REPOSITORY_SECRET_VALUES", terraform_action)
        self.assertIn('test -z "$REPOSITORY_SECRET_VALUES"', terraform_action)
        self.assertIn('test -z "$ENVIRONMENT_SECRET_VALUES"', terraform_action)
        self.assertIn("secrets.GITOPS_SECRET_VALUES", terraform)
        self.assertIn("secrets.repository_secret_values", terraform)
        self.assertNotIn("secrets: inherit", terraform)
        self.assertNotIn("toJSON(secrets)", terraform)

    def test_environment_profile_uses_same_named_fail_closed_secret_slots(self):
        workflows = (
            COMPONENTS / "nonprod-project-template" / ".github/workflows/terraform.yaml",
            COMPONENTS / "nonprod-project-template" / ".github/workflows/ansible.yaml",
            COMPONENTS / "prod-project-template" / ".github/workflows/terraform.yaml",
        )
        for workflow_path in workflows:
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn(
                "security_profile == 'github-environments' && "
                "secrets.READINESS_MARKER || ''",
                workflow,
            )

        for workflow_path in (workflows[0], workflows[2]):
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn(
                "security_profile == 'github-environments' && "
                "secrets.GITOPS_SECRET_VALUES || ''",
                workflow,
            )

    def test_project_skill_documents_environment_aware_paths(self):
        skill = (
            ROOT
            / "plugins"
            / "project-gitops"
            / "skills"
            / "project-gitops"
        )
        safety = (skill / "references/safety-boundaries.md").read_text(
            encoding="utf-8"
        )
        operations = (skill / "references/operations.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("{cloud}/{environment}/{region}/", safety)
        self.assertIn("gcp/{environment}/{region}/workloads/adb.json", safety)
        self.assertNotIn("{cloud}/{region}/lifecycle_operations/", safety)
        self.assertIn(
            "environments/<environment>/environment_information.md", operations
        )

if __name__ == "__main__":
    unittest.main()
