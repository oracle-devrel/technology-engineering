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
    def test_project_state_bucket_is_rendered_and_recorded(self):
        contract = json.loads(
            (
                ROOT / "contracts" / "deployment-contract.template.json"
            ).read_text(encoding="utf-8")
        )
        deployment = (ROOT / "docs" / "deployment.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(
            contract["project_state_bucket"],
            "__PROJECT_STATE_BUCKET__",
        )
        self.assertIn(
            "export PROJECT_STATE_BUCKET=example-project-state",
            deployment,
        )
        self.assertIn(
            "s/__STATE_BUCKET__/$ENV{PROJECT_STATE_BUCKET}/g",
            deployment,
        )

    def test_templates_default_to_recommended_profile(self):
        for template in ("nonprod-project-template", "prod-project-template"):
            contract = json.loads(
                (COMPONENTS / template / "control-plane.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(contract["security_profile"], "github-environments")

    def test_documentation_uses_paid_default_and_explicit_free_fallback(self):
        deployment = (ROOT / "docs" / "deployment.md").read_text(
            encoding="utf-8"
        )
        security = (ROOT / "docs" / "security.md").read_text(
            encoding="utf-8"
        )
        shared = (ROOT / "docs" / "shared-nonproduction.md").read_text(
            encoding="utf-8"
        )
        production = (ROOT / "docs" / "production.md").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "export NONPROD_SECURITY_PROFILE=github-environments",
            deployment,
        )
        self.assertIn(
            "export PROD_SECURITY_PROFILE=github-environments",
            deployment,
        )
        self.assertIn("## GitHub plan capability matrix", security)
        self.assertIn("GitHub Free private repository", security)
        self.assertIn("Pro/Team private repository", security)
        self.assertIn("Enterprise private repository", security)
        self.assertIn(
            "Organization runner groups require Team or Enterprise",
            security,
        )
        self.assertIn(
            "shared-nonproduction.md#github-free-fallback-repository-secrets",
            deployment,
        )
        self.assertNotIn(
            "shared-nonproduction.md#github-free-security-profile",
            deployment,
        )
        self.assertIn("repository-level runner", shared)
        self.assertIn("those two controls are unavailable", production)
        self.assertIn("required_status_checks: null", deployment)
        self.assertIn("require_code_owner_reviews: true", deployment)

    def test_templates_require_rendering_valid_codeowners(self):
        for template in ("nonprod-project-template", "prod-project-template"):
            github = COMPONENTS / template / ".github"
            self.assertFalse((github / "CODEOWNERS").exists())
            content = (github / "CODEOWNERS.template").read_text(encoding="utf-8")
            self.assertIn("__PLATFORM_OWNERS__", content)
            self.assertNotIn("@__CUSTOMER_ORG__", content)

        deployment = (ROOT / "docs" / "deployment.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("CODEOWNERS.template", deployment)
        self.assertIn("Every owner must already exist", deployment)

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
            self.assertIn("PLATFORM_CI_DEPLOY_KEY", workflow)

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

    def test_private_platform_ci_checkout_uses_only_the_read_deploy_key(self):
        for workflow_name in ("terraform-shared.yaml", "ansible-shared.yaml"):
            workflow = (
                COMPONENTS / "platform-ci" / ".github/workflows" / workflow_name
            ).read_text(encoding="utf-8")
            self.assertIn("PLATFORM_CI_DEPLOY_KEY:", workflow)
            self.assertEqual(
                workflow.count("ssh-key: ${{ secrets.PLATFORM_CI_DEPLOY_KEY }}"),
                2,
            )
            self.assertNotIn("secrets: inherit", workflow)

        deployment = (ROOT / "docs" / "deployment.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("platform-ci-readonly-deploy-key", deployment)
        self.assertIn("Do not enable write access", deployment)

    def test_ansible_bootstrap_uses_the_pinned_user_install(self):
        action = (
            COMPONENTS / "platform-ci" / "actions/ansible-execution/action.yml"
        ).read_text(encoding="utf-8")
        install = "python3.11 -m pip install ansible==9.0.1 oci-cli"
        user_path = 'export PATH="$HOME/.local/bin:$PATH"'
        collection_url = "https://galaxy.ansible.com/download/oracle-oci-5.5.0.tar.gz"
        collection_sha256 = (
            "4df1187e8728a91725ebe8d2f1e4eddb6193145c1ae4312c54caba6cdad4e60e"
        )
        galaxy = 'ansible-galaxy collection install "$collection_archive"'
        self.assertIn(install, action)
        self.assertIn(user_path, action)
        self.assertIn(collection_url, action)
        self.assertIn(collection_sha256, action)
        self.assertIn(galaxy, action)
        self.assertLess(action.index(install), action.index(user_path))
        self.assertLess(action.index(user_path), action.index(collection_url))
        self.assertLess(action.index(collection_url), action.index(galaxy))

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

    def test_generic_project_slug_is_valid_for_nsg_and_adb_requests(self):
        validator = load_validator()
        nsg = {
            "compartment_id": "ocid1.compartment.oc1..project",
            "display_name": "nsg-fra-dev-mccp-acceptance",
            "defined_tags": None,
            "freeform_tags": {
                "Project": "mccp",
                "Tier": "app",
                "ManagedBy": "platform-ci",
            },
            "ingress_rules": {},
            "egress_rules": {},
        }
        validator._validate_new_nsg(
            "NSG-FRA-LZ-DEV-MCCP-ACCEPTANCE-KEY",
            nsg,
            project="nonprod-mccp",
            declared_nsgs=frozenset(
                {"NSG-FRA-LZ-DEV-MCCP-ACCEPTANCE-KEY"}
            ),
        )

        adb = json.loads(
            (
                COMPONENTS
                / "gitops-templates"
                / "resources-catalog"
                / "oci"
                / "databases"
                / "project_database_template.auto.tfvars.json"
            ).read_text(encoding="utf-8")
        )["autonomous_databases_configuration"]["databases"]["__ADB_KEY__"]
        adb.update(
            {
                "db_name": "MCCPADB",
                "display_name": "adb-dev-mccp",
                "admin_password": "__DEV_ADB_ADMIN_PASSWORD__",
            }
        )
        adb["networking"]["subnet_id"] = (
            "ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase"
        )
        adb["networking"]["network_security_groups"] = [
            "NSG-FRA-LZ-DEV-MCCP-ACCEPTANCE-KEY"
        ]
        validator.validate_adb_declaration(
            "ADB-MCCP-KEY",
            adb,
            project="nonprod-mccp",
            environment="dev",
            region="eu-frankfurt-1",
        )

    def test_exacs_operation_requires_a_registered_database_and_target_home(self):
        validator = load_validator()
        registry = {
            "schema_version": 2,
            "databases": [
                {
                    "display_name": "orders-cdb",
                    "database_id": "ocid1.database.oc1.eu-frankfurt-1.example",
                    "compartment_id": "ocid1.compartment.oc1..example",
                    "vm_cluster_id": "ocid1.vmcluster.oc1.eu-frankfurt-1.example",
                    "service_model": "exacs",
                    "declarative_owner": "external",
                    "approved_target_db_homes": [
                        {
                            "id": "ocid1.dbhome.oc1.eu-frankfurt-1.target",
                            "db_version": "19.28.0.0.0",
                        }
                    ],
                }
            ],
        }
        request = {
            "operation_type": "exacs-database-out-of-place-patch",
            "targets": [
                {
                    "display_name": "orders-cdb",
                    "expected_source_db_home_id": "ocid1.dbhome.oc1.eu-frankfurt-1.source",
                    "target_db_home_id": "ocid1.dbhome.oc1.eu-frankfurt-1.target",
                    "target_db_version": "19.28.0.0.0",
                    "timeout_minutes": 240,
                }
            ],
        }
        self.assertIn(
            "approved-target-db-home",
            validator._validate_exacs_patch_change(request, registry),
        )

        request["targets"][0]["target_db_home_id"] = (
            "ocid1.dbhome.oc1.eu-frankfurt-1.unapproved"
        )
        with self.assertRaises(validator.ValidationFailure) as raised:
            validator._validate_exacs_patch_change(request, registry)
        self.assertEqual(raised.exception.code, "UNAPPROVED_TARGET_DB_HOME")

    def test_exacs_operation_uses_the_dedicated_runner_label(self):
        caller = (
            COMPONENTS
            / "nonprod-project-template"
            / ".github"
            / "workflows"
            / "ansible.yaml"
        ).read_text(encoding="utf-8")
        self.assertIn("exacs-database-out-of-place-patch", caller)
        self.assertIn("exacs-database-operations", caller)
        self.assertIn("wc -l", caller)
        self.assertIn("operation_file=$(printf", caller)
        self.assertIn('"$head_sha:$operation_file"', caller)

if __name__ == "__main__":
    unittest.main()
