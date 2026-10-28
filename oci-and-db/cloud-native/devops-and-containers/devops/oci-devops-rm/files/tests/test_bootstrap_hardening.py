import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class BootstrapHardeningTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text()

    def test_policy_attachment_and_grants_are_separate(self):
        source = self.read("modules/iam/policies.tf")
        self.assertIn("compartment_id = var.policy_compartment_id", source)
        self.assertIn("in compartment id ${var.compartment_id}", source)
        self.assertIn("compartment_id = var.secret_compartment_id", source)
        self.assertIn(
            "coalesce(var.iam_policy_compartment_id, var.tenancy_ocid)",
            self.read("main.tf"),
        )
        schema = yaml.safe_load(self.read("schema.yaml"))
        field = schema["variables"]["iam_policy_compartment_id"]
        self.assertEqual(field["default"], "${tenancy_ocid}")
        self.assertEqual(field["visible"], "${create_iam}")

    def test_root_project_guard_covers_create_and_reuse(self):
        for path, compartment, guard in (
            ("modules/devops/project.tf", "var.compartment_id", "precondition"),
            ("modules/devops/data.tf", "self.compartment_id", "postcondition"),
        ):
            source = self.read(path)
            self.assertIn(guard, source)
            self.assertIn(
                f"!local.oke_environments_required || {compartment} != var.tenancy_id",
                source,
            )
        locals_source = self.read("modules/devops/locals.tf")
        self.assertIn(
            "local.application_delivery_enabled || local.cluster_admin_enabled",
            locals_source,
        )

    def test_native_helm_pipelines_support_unchanged_reruns(self):
        source = self.read("modules/devops/deploy_pipelines.tf")
        for resource in ("deploy_application", "deploy_component"):
            block = source.split(
                f'resource "oci_devops_deploy_pipeline" "{resource}" {{', 1
            )[1].split('\nresource "', 1)[0]
            self.assertIn('name          = "ENFORCE_HELM_DEPLOYMENT"', block)
            self.assertIn('default_value = "true"', block)
            self.assertIn("ignore_changes = all", block)


if __name__ == "__main__":
    unittest.main()
