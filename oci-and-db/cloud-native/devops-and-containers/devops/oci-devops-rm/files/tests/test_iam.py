import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class IamPolicyTests(unittest.TestCase):
    def test_secret_access_policy_is_created_in_vault_compartment(self):
        source = (ROOT / "modules/iam/policies.tf").read_text(encoding="utf-8")

        default_start = source.index("  default_statements = [")
        default_end = source.index("\n  ]", default_start)
        default_statements = source[default_start:default_end]
        self.assertNotIn("secret-family", default_statements)

        resource_start = source.index(
            'resource "oci_identity_policy" "devops_secret_access_policy" {'
        )
        secret_policy = source[resource_start:]
        self.assertIn("count = var.enable_secret_access ? 1 : 0", secret_policy)
        self.assertIn("compartment_id = var.secret_compartment_id", secret_policy)
        self.assertIn('name           = "${var.devops_policy_name}-secret-access"', secret_policy)
        self.assertIn("statements     = local.secret_statements", secret_policy)

        self.assertIn("read secret-family", source)
        self.assertIn("in compartment id ${var.secret_compartment_id}", source)

    def test_oke_and_network_policies_follow_enabled_capabilities(self):
        source = (ROOT / "modules/iam/policies.tf").read_text(encoding="utf-8")

        self.assertIn(
            "network_compartment_ids = var.enable_oke_access ?",
            source,
        )
        self.assertIn(
            "oke_compartment_ids = var.enable_oke_access ?",
            source,
        )


if __name__ == "__main__":
    unittest.main()
