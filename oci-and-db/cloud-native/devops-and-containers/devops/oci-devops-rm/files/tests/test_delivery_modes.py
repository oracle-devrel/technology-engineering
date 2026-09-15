import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class DeliveryModeTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_public_mode_contract_uses_build_only_name(self):
        variables = self.read("variables.tf")
        schema = self.read("schema.yaml")

        self.assertIn('["oci_devops", "build_only"]', variables)
        self.assertIn("- build_only", schema)
        self.assertNotIn("ci_only", variables)
        self.assertNotIn("ci_only", schema)

    def test_shared_repository_name_is_configurable(self):
        variables = self.read("variables.tf")
        repositories = self.read("modules/devops/repositories.tf")
        checks = self.read("checks.tf")

        self.assertRegex(variables, r'default\s*=\s*"devops-pipelines"')
        self.assertIn("name            = var.devops_pipeline_repository_name", repositories)
        self.assertIn("lower(var.devops_pipeline_repository_name)", checks)

    def test_delivery_resources_are_gated_by_capability_maps(self):
        expected = {
            "modules/devops/artifacts.tf": (
                "local.delivery_applications_by_name",
                "local.delivery_components_by_name",
            ),
            "modules/devops/deploy_pipelines.tf": (
                "local.delivery_applications_by_name",
                "local.delivery_components_by_name",
            ),
            "modules/devops/triggers.tf": ("local.delivery_applications_by_name",),
            "modules/devops/protected_branches.tf": (
                "local.delivery_applications_by_name",
            ),
        }

        for path, capability_maps in expected.items():
            source = self.read(path)
            for capability_map in capability_maps:
                self.assertIn(capability_map, source, path)

        environments = self.read("modules/devops/environment.tf")
        self.assertEqual(environments.count("count = local.oke_environments_required ? 1 : 0"), 2)

    def test_build_and_pr_pipelines_exist_in_both_modes(self):
        pipelines = self.read("modules/devops/build_pipelines.tf")
        triggers = self.read("modules/devops/triggers.tf")

        self.assertIn(
            'resource "oci_devops_build_pipeline" "application_delivery"', pipelines
        )
        self.assertIn(
            'resource "oci_devops_build_pipeline" "application_pull_request"', pipelines
        )
        self.assertIn("for_each = local.components_by_name", pipelines)
        self.assertIn('events         = ["PULL_REQUEST_CREATED", "PULL_REQUEST_UPDATED"]', triggers)

    def test_build_only_stage_has_no_chart_or_deployment_contract(self):
        template = self.read("templates/build-only-pipeline.yaml.tpl")
        pipelines = self.read("modules/devops/build_pipelines.tf")

        self.assertIn('git rev-parse --short=7 HEAD', template)
        self.assertIn('script/build-push-image.sh', template)
        self.assertNotIn("chart_version", template)
        self.assertNotIn("helm", template.lower())
        self.assertIn(
            'for_each = local.delivery_components_by_name',
            pipelines[pipelines.index(
                'resource "oci_devops_build_pipeline_stage" "trigger_dev_deployment"'
            ):],
        )

    def test_oke_and_secret_iam_are_capability_gated(self):
        main = self.read("main.tf")
        policies = self.read("modules/iam/policies.tf")

        self.assertIn("enable_oke_access           = local.oke_environments_required", main)
        self.assertIn("enable_secret_access        = local.application_delivery_enabled", main)
        self.assertIn("var.enable_oke_access ?", policies)
        self.assertIn("count = var.enable_secret_access ? 1 : 0", policies)

    def test_cross_variable_requirements_use_root_checks(self):
        variables = self.read("variables.tf")
        checks = self.read("checks.tf")

        self.assertNotIn(
            'condition     = (var.application_delivery_mode == "build_only"',
            variables,
        )
        self.assertNotIn(
            "[lower(var.devops_pipeline_repository_name), \"cluster-admin\"]",
            variables,
        )
        self.assertIn('check "conditional_inputs"', checks)
        self.assertIn('check "repository_names_are_unique"', checks)

    def test_delivery_outputs_are_empty_or_null_when_resources_are_absent(self):
        outputs = self.read("modules/devops/outputs.tf")
        locals = self.read("modules/devops/locals.tf")

        self.assertIn("local.delivery_applications_by_name", outputs)
        self.assertIn("local.delivery_components_by_name", outputs)
        self.assertIn(
            "try(oci_devops_deploy_environment.oke_environment[0].id, null)", locals
        )
        self.assertIn(
            "try(oci_devops_deploy_environment.prod_oke_environment[0].id, null)",
            locals,
        )


if __name__ == "__main__":
    unittest.main()
