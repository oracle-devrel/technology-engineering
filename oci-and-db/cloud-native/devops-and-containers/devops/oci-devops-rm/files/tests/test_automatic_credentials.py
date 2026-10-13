import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class AutomaticCredentialTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text()

    def test_form_keeps_credentials_and_iam_independent(self):
        variables = yaml.safe_load(self.read("schema.yaml"))["variables"]
        self.assertFalse(variables["create_automatic_credentials"]["default"])
        self.assertEqual(variables["auth_token"]["visible"], {"not": ["${create_automatic_credentials}"]})
        for name in ("devops_iam_domain_id", "iam_domain_compartment_id"):
            self.assertEqual(variables[name]["visible"]["or"], ["${create_iam}", "${create_automatic_credentials}"])
        self.assertIn("State", variables["create_automatic_credentials"]["description"].title())
        self.assertTrue(variables["automatic_credentials_email"]["required"])
        self.assertTrue(re.fullmatch(variables["automatic_credentials_email"]["pattern"], "ops@example.com"))
        self.assertIsNone(re.fullmatch(variables["automatic_credentials_email"]["pattern"], "invalid"))

    def test_seeding_waits_for_generated_policies_without_reseed_triggers(self):
        for filename, expected in (
            ("modules/devops/repositories.tf", 6),
            ("modules/devops/cluster_admin_repositories.tf", 4),
        ):
            source = self.read(filename)
            self.assertEqual(source.count("CREDENTIAL_POLICY_ID = var.credential_policy_ready"), expected)
            self.assertNotIn("credential_policy_ready", "".join(re.findall(r"triggers = \{(.*?)\n  \}", source, re.S)))
        self.assertIn("attempts=30", self.read("script/seed_repo.sh"))
        self.assertIn('git clone "${REPO_CLONE_URL}"', self.read("script/seed_repo.sh"))

    def test_scoped_dynamic_group_includes_all_generated_execution_types(self):
        group = self.read("modules/iam/dynamic-groups.tf")
        self.assertIn("resource.id =", group)
        self.assertNotIn("resource.compartment.id", group)
        outputs = self.read("modules/devops/outputs.tf")
        section = outputs[outputs.index('output "execution_resource_ids"'):outputs.index('output "devops_project_name"')]
        for path in (ROOT / "modules/devops").glob("*.tf"):
            for kind, name in re.findall(r'resource "(oci_devops_(?:repository|build_pipeline|deploy_pipeline|trigger))" "([^"]+)"', path.read_text()):
                self.assertIn(f"{kind}.{name}", section)

    def test_pull_account_is_separate_and_has_no_push_grant(self):
        source = self.read("credentials.tf")
        self.assertIn('local.application_delivery_enabled ? { pull =', source)
        self.assertIn('group.automation["pull"].ocid} to read repos', source)
        self.assertNotIn('group.automation["pull"].ocid} to manage', source)
        self.assertIn("target.repo.name =", source)
        self.assertIn("target.repository.id =", source)
        self.assertIn('var.create_automatic_credentials && var.create_iam', source)

    def test_tokens_are_sensitive_and_not_outputs(self):
        source = self.read("credentials.tf")
        self.assertIn('sensitive(oci_identity_auth_token.automation["bootstrap"].token)', source)
        self.assertIn("sensitive(base64encode(oci_identity_auth_token.automation[each.key].token))", source)
        outputs = self.read("outputs.tf")
        self.assertNotIn(".token)", outputs)
        self.assertNotIn(".token\n", outputs)
        self.assertIn("credentials.tf", self.read("release-files.txt").splitlines())

    def test_secret_access_is_only_for_bootstrap_pipelines(self):
        source = self.read("modules/iam/policies.tf")
        self.assertIn("var.secret_reader_ids", source)
        self.assertIn("request.principal.id", source)
        self.assertIn("target.secret.id", source)
        self.assertIn("var.secret_ids", source)

    def test_form_boolean_expressions_use_binary_operators(self):
        schema = yaml.safe_load(self.read("schema.yaml"))

        def inspect(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key in ("and", "or"):
                        self.assertEqual(len(child), 2)
                    if key == "not":
                        self.assertEqual(len(child), 1)
                    inspect(child)
            elif isinstance(value, list):
                for child in value:
                    inspect(child)

        inspect(schema["variables"])
        for output in schema["outputs"].values():
            if "visible" in output:
                self.assertIsInstance(output["visible"], bool)


if __name__ == "__main__":
    unittest.main()
