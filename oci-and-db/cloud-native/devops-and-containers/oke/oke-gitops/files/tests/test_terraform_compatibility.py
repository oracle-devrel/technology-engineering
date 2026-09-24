import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TerraformCompatibilityTests(unittest.TestCase):
    def test_project_reuse_uses_root_check(self):
        variables = (ROOT / "variables.tf").read_text(encoding="utf-8")
        checks = (ROOT / "checks.tf").read_text(encoding="utf-8")

        self.assertNotIn("var.create_devops_project || can(regex", variables)
        self.assertIn('check "existing_devops_project"', checks)
        self.assertIn("var.create_devops_project || can(regex", checks)

    def test_devops_projects_require_a_child_compartment(self):
        project = (ROOT / "modules/devops/project.tf").read_text(encoding="utf-8")
        data = (ROOT / "modules/devops/data.tf").read_text(encoding="utf-8")
        schema = (ROOT / "schema.yaml").read_text(encoding="utf-8")

        self.assertIn("precondition", project)
        self.assertIn("var.compartment_id != var.tenancy_id", project)
        self.assertIn("postcondition", data)
        self.assertIn("self.compartment_id != var.tenancy_id", data)
        self.assertIn("The tenancy root is not supported", schema)

    def test_vault_secrets_use_the_devops_project_compartment(self):
        root_main = (ROOT / "main.tf").read_text(encoding="utf-8")
        root_variables = (ROOT / "variables.tf").read_text(encoding="utf-8")
        schema = (ROOT / "schema.yaml").read_text(encoding="utf-8")
        iam_variables = (ROOT / "modules/iam/variables.tf").read_text(encoding="utf-8")
        policies = (ROOT / "modules/iam/policies.tf").read_text(encoding="utf-8")

        for content in (root_main, root_variables, schema, iam_variables, policies):
            self.assertNotIn("kms_compartment_id", content)

        self.assertIn(
            "read secret-bundles in compartment id ${var.compartment_id}",
            policies,
        )


if __name__ == "__main__":
    unittest.main()
