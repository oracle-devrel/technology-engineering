import re
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class AutomaticCredentialTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text()

    def test_schema_rejects_duplicate_mapping_keys(self):
        class UniqueKeyLoader(yaml.SafeLoader):
            pass

        def unique_mapping(loader, node, deep=False):
            mapping = {}
            for key_node, value_node in node.value:
                key = loader.construct_object(key_node, deep=deep)
                if key in mapping:
                    raise ValueError(f"Duplicate schema key {key!r} at line {key_node.start_mark.line + 1}")
                mapping[key] = loader.construct_object(value_node, deep=deep)
            return mapping

        UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
        yaml.load(self.read("schema.yaml"), Loader=UniqueKeyLoader)
        with self.assertRaises(ValueError):
            yaml.load("visible: false\nvisible: true\n", Loader=UniqueKeyLoader)

    def test_form_keeps_credentials_and_iam_independent(self):
        variables = yaml.safe_load(self.read("schema.yaml"))["variables"]
        self.assertFalse(variables["create_automatic_credentials"]["default"])
        self.assertTrue(variables["auth_token"]["visible"])
        self.assertTrue(variables["auth_token"]["required"])
        self.assertEqual(variables["devops_iam_domain_id"]["dependsOn"]["compartmentId"], "${iam_domain_compartment_id}")
        for name in ("devops_iam_domain_id", "iam_domain_compartment_id"):
            self.assertEqual(variables[name]["visible"], "${create_automatic_credentials}")
        for name in ("pipeline_iam_domain_id", "pipeline_iam_domain_compartment_id"):
            self.assertEqual(variables[name]["visible"], "${create_iam}")
        self.assertEqual(variables["pipeline_iam_domain_id"]["dependsOn"]["compartmentId"], "${pipeline_iam_domain_compartment_id}")
        self.assertIn("State", variables["create_automatic_credentials"]["description"].title())
        self.assertFalse(variables["automatic_credentials_email"]["visible"])
        self.assertEqual(variables["automatic_credentials_email"]["default"], "automation@example.com")
        self.assertTrue(re.fullmatch(variables["automatic_credentials_email"]["pattern"], "ops@example.com"))
        self.assertIsNone(re.fullmatch(variables["automatic_credentials_email"]["pattern"], "invalid"))

    def test_form_group_order_and_help_length(self):
        schema = yaml.safe_load(self.read("schema.yaml"))
        groups = {group["title"]: group["variables"] for group in schema["variableGroups"]}
        self.assertEqual(groups["Applications"], ["application_definitions", "components"])
        for name in ("application_namespace_help", "cluster_administration_help", "automatic_credentials_compartment_id", "namespace_init_secret_compartment_id"):
            self.assertIn(name, groups["Hidden"])
        self.assertRegex(self.read("credentials.tf"), r"credentials_compartment_id\s*=\s*module.devops.devops_project_compartment_id")
        self.assertRegex(self.read("main.tf"), r"secret_compartment_id\s*=\s*module.devops.devops_project_compartment_id")
        iam = groups["IAM"]
        self.assertEqual(iam[-3:], ["create_automatic_credentials", "iam_domain_compartment_id", "devops_iam_domain_id"])
        for flag, fields in (("create_iam", ("pipeline_iam_domain_compartment_id", "pipeline_iam_domain_id")), ("create_automatic_credentials", ("iam_domain_compartment_id", "devops_iam_domain_id"))):
            for field in fields:
                self.assertLess(iam.index(flag), iam.index(field))
        self.assertEqual(schema["variables"]["create_automatic_credentials"]["title"], "Create OCI Vault and Credentials")
        help_field = schema["variables"]["application_namespace_help"]
        self.assertGreaterEqual(help_field["maxLength"], len(help_field["default"]))

    def test_seeding_waits_for_generated_policies_without_reseed_triggers(self):
        for filename, expected in (
            ("modules/devops/repositories.tf", 6),
            ("modules/devops/cluster_admin_repositories.tf", 4),
        ):
            source = self.read(filename)
            self.assertEqual(source.count("CREDENTIAL_POLICY_ID = var.credential_policy_ready"), expected)
            self.assertNotIn("credential_policy_ready", "".join(re.findall(r"triggers = \{(.*?)\n  \}", source, re.S)))
        self.assertIn("attempts=60", self.read("script/seed_repo.sh"))
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
        self.assertNotIn('var.create_automatic_credentials && var.create_iam', source)
        self.assertRegex(source, r'resource "oci_identity_policy" "automation" \{\s+count\s*=\s*var.create_automatic_credentials \? 1 : 0')
        self.assertRegex(source, re.compile(r'resource "oci_identity_policy" "automation" \{.*?compartment_id\s*=\s*module.devops.devops_project_compartment_id', re.S))
        self.assertIn('random_string.automation_policy_suffix[0].result', source)

    def test_tokens_are_sensitive_and_not_outputs(self):
        source = self.read("credentials.tf")
        self.assertRegex(source, r"effective_git_username\s*=\s*local.git_username")
        self.assertRegex(source, r"effective_git_password\s*=\s*var.auth_token")
        self.assertIn("sensitive(base64encode(oci_identity_domains_auth_token.automation[each.key].token))", source)
        outputs = self.read("outputs.tf")
        self.assertNotIn(".token)", outputs)
        self.assertNotIn(".token\n", outputs)
        self.assertIn("credentials.tf", self.read("release-files.txt").splitlines())

    def test_tokens_use_selected_domain(self):
        source = self.read("credentials.tf")
        self.assertNotIn('resource "oci_identity_auth_token"', source)
        self.assertIn('resource "oci_identity_domains_auth_token"', source)
        self.assertRegex(source, r"service_user\s*=\s*false")
        self.assertRegex(source, r"can_use_auth_tokens\s*=\s*true")
        self.assertRegex(source, r"can_use_console\s*=\s*false")
        self.assertRegex(source, r'attribute_sets\s*=\s*\["all"\]')
        self.assertRegex(self.read("modules/iam/dynamic-groups.tf"), r'attribute_sets\s*=\s*\["all"\]')
        self.assertIn("time_sleep.credentials_vault_dns", source)
        self.assertIn('create_duration = "60s"', source)

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
