import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "components"


class ProjectAutomationGateTests(unittest.TestCase):
    def test_project_callers_require_completed_handoff(self):
        workflows = (
            COMPONENTS
            / "nonprod-project-template"
            / ".github/workflows/terraform.yaml",
            COMPONENTS
            / "nonprod-project-template"
            / ".github/workflows/ansible.yaml",
            COMPONENTS
            / "prod-project-template"
            / ".github/workflows/terraform.yaml",
        )
        for workflow_path in workflows:
            workflow = workflow_path.read_text(encoding="utf-8")
            self.assertIn(
                "if: vars.PROJECT_AUTOMATION_READY == 'true'", workflow
            )

    def test_runbook_requires_explicit_automation_enablement(self):
        deployment = (ROOT / "docs" / "deployment.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("PROJECT_AUTOMATION_READY", deployment)
        self.assertIn("can allocate a runner", deployment)


if __name__ == "__main__":
    unittest.main()
