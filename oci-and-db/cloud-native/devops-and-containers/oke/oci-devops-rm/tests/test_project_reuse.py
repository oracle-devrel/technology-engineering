import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class DevopsProjectReuseTests(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_resource_manager_exposes_create_or_reuse_choice(self):
        schema = yaml.safe_load(self.read("schema.yaml"))
        variables = schema["variables"]

        self.assertTrue(variables["create_devops_project"]["default"])
        self.assertIn("existing_devops_project_id", variables)
        self.assertEqual(
            variables["existing_devops_project_id"]["pattern"],
            r"^ocid1\.devopsproject\..+$",
        )

    def test_existing_project_is_resolved_without_managing_it(self):
        project = self.read("modules/devops/project.tf")
        data = self.read("modules/devops/data.tf")
        locals_source = self.read("modules/devops/locals.tf")

        self.assertIn('count = var.create_devops_project ? 1 : 0', project)
        self.assertIn('data "oci_devops_project" "existing"', data)
        self.assertIn("devops_project_id = var.create_devops_project", locals_source)
        self.assertIn("devops_project_name = var.create_devops_project", locals_source)
        self.assertIn(
            "devops_project_compartment_id = var.create_devops_project",
            locals_source,
        )

    def test_generated_resources_use_resolved_project(self):
        for path in (ROOT / "modules/devops").glob("*.tf"):
            source = path.read_text(encoding="utf-8")
            if path.name != "locals.tf":
                self.assertNotIn(
                    "oci_devops_project.devops_project.id",
                    source,
                    f"{path.name} bypasses the resolved project ID",
                )

    def test_existing_project_keeps_project_wide_repository_settings(self):
        settings = self.read("modules/devops/repository_settings.tf")
        self.assertIn("count = var.create_devops_project ? 1 : 0", settings)

    def test_existing_project_logging_is_hidden_and_not_created(self):
        schema = yaml.safe_load(self.read("schema.yaml"))["variables"]
        self.assertEqual(
            schema["devops_log_is_enabled"]["visible"],
            "${create_devops_project}",
        )
        for variable_name in (
            "devops_log_group_name",
            "devops_log_group_description",
            "devops_log_name",
            "devops_log_retention_period_in_days",
        ):
            self.assertEqual(
                schema[variable_name]["visible"]["and"],
                ["${create_devops_project}", "${devops_log_is_enabled}"],
            )

        project = self.read("modules/devops/project.tf")
        self.assertEqual(
            project.count(
                "count = var.create_devops_project && var.devops_log_is_enabled ? 1 : 0"
            ),
            2,
        )

    def test_existing_created_projects_keep_their_state_address(self):
        migration = self.read("modules/devops/migrations.tf")
        self.assertIn("from = oci_devops_project.devops_project", migration)
        self.assertIn("to   = oci_devops_project.devops_project[0]", migration)

    def test_release_archive_excludes_maintainer_assets(self):
        packaging = self.read("update.sh")
        for exclusion in (
            '--exclude ".agents"',
            '--exclude ".agents.zip"',
            '--exclude "downloads"',
            '--exclude "script/package_maintainer_skill.sh"',
            '--exclude "*.zip"',
        ):
            self.assertIn(exclusion, packaging)


if __name__ == "__main__":
    unittest.main()
