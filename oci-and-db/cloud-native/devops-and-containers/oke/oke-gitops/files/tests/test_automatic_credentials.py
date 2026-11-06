import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AutomaticCredentialTests(unittest.TestCase):
    def test_work_and_recovery_email_are_explicit(self):
        credentials = (ROOT / "credentials.tf").read_text()
        blocks = re.findall(r"emails\s*\{([^{}]*)\}", credentials)
        self.assertEqual(len(blocks), 2)
        by_type = {re.search(r'type\s*=\s*"([^"]+)"', block).group(1): block for block in blocks}
        self.assertEqual(set(by_type), {"work", "recovery"})
        for block in blocks:
            self.assertRegex(block, r"value\s*=\s*var.automatic_credentials_email")
        self.assertRegex(by_type["work"], r"primary\s*=\s*true")
        self.assertRegex(by_type["recovery"], r"primary\s*=\s*false")

    def test_seeding_keeps_the_applying_users_token(self):
        main = (ROOT / "main.tf").read_text()
        self.assertIn("git_password", main)
        self.assertRegex(main, r"git_password\s*= var.auth_token")
        self.assertNotIn("automation[\"git\"].token", main)

    def test_runtime_secrets_are_username_password_json(self):
        credentials = (ROOT / "credentials.tf").read_text()
        self.assertIn("sensitive(base64encode(jsonencode({", credentials)
        self.assertIn("username = local.credential_usernames[each.key]", credentials)
        self.assertIn("password = oci_identity_domains_auth_token.automation[each.key].token", credentials)
        self.assertIn('key == "git" ? data.oci_identity_tenancy.current_tenancy.name', credentials)
        self.assertIn("data.oci_artifacts_container_configuration.credentials[0].namespace", credentials)

    def test_runtime_permissions_are_read_only_and_scoped(self):
        credentials = (ROOT / "credentials.tf").read_text()
        self.assertNotIn(" to manage ", credentials)
        self.assertNotIn(" to use ", credentials)
        self.assertIn("target.project.id", credentials)
        self.assertIn("target.repository.id", credentials)
        self.assertIn(r'target.repo.name = /${replace(var.ocir_repo_path_prefix, "/", "\\/")}\\/*/', credentials)
        self.assertNotIn("target.repo.name = /${var.ocir_repo_path_prefix}/*/", credentials)
        outputs = (ROOT / "modules/devops/outputs.tf").read_text()
        section = outputs.split('output "gitops_repository_ids"')[1].split('output "')[0]
        self.assertNotIn("devops_pipelines_repo", section)
        self.assertIn("fleet_config_repo", section)

    def test_build_and_install_pipelines_default_to_the_same_secrets(self):
        for name in ("build_pipeline.tf", "deployment.tf"):
            pipeline = (ROOT / "modules/devops" / name).read_text()
            self.assertIn("default_value = var.git_read_credentials_secret_ocid", pipeline)
            self.assertIn("default_value = var.registry_pull_secret_ocid", pipeline)

    def test_tokens_are_not_outputs(self):
        outputs = (ROOT / "output.tf").read_text()
        self.assertNotIn(".token", outputs)
        self.assertNotIn("secret_content", outputs)


if __name__ == "__main__":
    unittest.main()
