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


if __name__ == "__main__":
    unittest.main()
