import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class UniqueKeyLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        keys = [self.construct_object(key, deep=deep) for key, _ in node.value]
        if len(keys) != len(set(keys)):
            raise ValueError("Duplicate Resource Manager schema mapping key")
        return super().construct_mapping(node, deep=deep)


class SchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = yaml.load((ROOT / "schema.yaml").read_text(), Loader=UniqueKeyLoader)

    def test_all_group_entries_are_declared_once(self):
        entries = [name for group in self.schema["variableGroups"] for name in group["variables"]]
        self.assertEqual(len(entries), len(set(entries)))
        context = {"tenancy_ocid", "region", "current_user_ocid", "compartment_ocid"}
        self.assertEqual(set(entries) - context, set(self.schema["variables"]))

    def test_feature_fields_are_consecutive_below_their_flags(self):
        iam = next(group for group in self.schema["variableGroups"] if group["title"] == "IAM")["variables"]
        self.assertEqual(iam, [
            "auth_token", "create_iam", "iam_policy_compartment_id", "devops_policy_name",
            "iam_domain_compartment_id", "devops_iam_domain_id", "devops_dynamic_group_name",
            "create_automatic_credentials", "automation_iam_domain_compartment_id", "automation_iam_domain_id",
        ])
        variables = self.schema["variables"]
        for name in iam[2:7]:
            self.assertEqual(variables[name]["visible"], "${create_iam}")
        for name in iam[8:]:
            self.assertEqual(variables[name]["visible"], "${create_automatic_credentials}")

    def test_automation_and_execution_domain_pickers_are_independent(self):
        variables = self.schema["variables"]
        self.assertEqual(variables["automation_iam_domain_id"]["dependsOn"]["compartmentId"], "${automation_iam_domain_compartment_id}")
        self.assertEqual(variables["devops_iam_domain_id"]["dependsOn"]["compartmentId"], "${iam_domain_compartment_id}")
        self.assertFalse(variables["automatic_credentials_email"]["visible"])
        self.assertFalse(variables["devops_policy_name"]["required"])
        self.assertTrue(variables["auth_token"]["required"])

    def test_execution_iam_description_discloses_devops_management_scope(self):
        description = self.schema["variables"]["create_iam"]["description"]
        self.assertIn("bootstrap and installer", description)
        self.assertIn("devops-family management", description)
        self.assertIn("DevOps project compartment", description)
        self.assertIn("Mirror and OCI resource access remain separately scoped", description)

    def test_duplicate_mapping_keys_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            yaml.load("visible: true\nvisible: false\n", Loader=UniqueKeyLoader)

    def test_new_stack_defaults_and_hidden_development_switch(self):
        variables = self.schema["variables"]
        self.assertEqual(variables["gitops_agent"]["default"], "argocd")
        self.assertEqual(variables["gitops_scope"]["default"], "cluster_admin")
        self.assertEqual(variables["ocir_repo_path_prefix"]["default"], "company-name/org")
        development = variables["development_overwrite_repositories"]
        self.assertFalse(development["visible"])
        self.assertFalse(development["default"])
        hidden = next(group for group in self.schema["variableGroups"] if group["title"] == "Hidden")
        self.assertIn("development_overwrite_repositories", hidden["variables"])


if __name__ == "__main__":
    unittest.main()
