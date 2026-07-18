import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "oci-landing-zone"
SCRIPTS = COMPONENT / "scripts"
CLOUD_SKILL = (
    ROOT
    / "plugins"
    / "cloud-operator-gitops"
    / "skills"
    / "cloud-operator-gitops"
)
sys.path.insert(0, str(SCRIPTS))

from render_project_handoff import (  # noqa: E402
    SUBNET_KEYS,
    VCN_KEY,
    build_handoff_data,
    build_machine_handoff,
    load_json,
)


class LandingZoneContractTests(unittest.TestCase):
    def machine_data(self, environment):
        return {
            "project": f"{environment}-payments",
            "environment": environment,
            "region": "eu-frankfurt-1",
            "compartments": {
                role: {"ocid": f"ocid1.compartment.oc1..{role}"}
                for role in ("app", "database", "infrastructure")
            },
            "vcn": {"ocid": "ocid1.vcn.oc1..projects"},
            "subnets": {
                role: {"ocid": f"ocid1.subnet.oc1..{role}"}
                for role in ("web", "app", "database", "infrastructure")
            },
        }

    def machine_handoff(self, environment):
        target = (
            "prod-payments" if environment == "prod" else "nonprod-payments"
        )
        return build_machine_handoff(
            self.machine_data(environment),
            {
                "repository": "customer/oci-landing-zone",
                "workflow": "handoff",
                "run": "42",
                "commit": "c" * 40,
            },
            f"op02_manage_environment/{environment}/terraform.tfstate",
            f"op04_manage_project/{environment}/{environment}-payments/terraform.tfstate",
            target,
            f"environments/{environment}/environment_information.md",
        )

    def test_runtime_contract_maps_all_foundations(self):
        contract = json.loads(
            (COMPONENT / ".github/project-onboarding-contract.json").read_text()
        )
        self.assertEqual(contract["allowed_environments"], ["dev", "test", "uat", "prod"])
        self.assertIs(contract["same_slug_repository"], False)
        self.assertEqual(
            contract["target_repository_prefixes"],
            {"dev": "nonprod", "test": "nonprod", "uat": "nonprod", "prod": "prod"},
        )
        pattern = re.compile(contract["project_slug_pattern"])
        for environment in contract["allowed_environments"]:
            self.assertIsNotNone(pattern.fullmatch(f"{environment}-payments"))
            handoff = self.machine_handoff(environment)
            expected_layout = (
                "production-v1" if environment == "prod" else "shared-nonprod-v2"
            )
            self.assertEqual(handoff["repository_layout"], expected_layout)

    def test_renderer_consumes_nested_terraform_outputs_and_runtime_region(self):
        parent = "CMP-LZP-P-PAYMENTS-KEY"
        children = {
            "app": "CMP-LZP-P-PAYMENTS-APP-KEY",
            "database": "CMP-LZP-P-PAYMENTS-DB-KEY",
            "infrastructure": "CMP-LZP-P-PAYMENTS-INFRA-KEY",
        }
        project_config = {
            "compartments_configuration": {
                "compartments": {
                    parent: {"children": {key: {} for key in children.values()}}
                }
            }
        }
        network_config = {
            "network_configuration": {
                "network_configuration_categories": {
                    "prod": {
                        "vcns": {
                            VCN_KEY: {
                                "display_name": "projects",
                                "cidr_blocks": ["10.0.0.0/16"],
                                "subnets": {
                                    key: {
                                        "display_name": role,
                                        "cidr_block": f"10.0.{index}.0/24",
                                    }
                                    for index, (role, key) in enumerate(
                                        SUBNET_KEYS.items(), start=1
                                    )
                                },
                            }
                        }
                    }
                }
            }
        }
        terraform_outputs = {
            "op04": {
                "iam_resources": {
                    "sensitive": False,
                    "type": ["object", {}],
                    "value": {
                        "compartments": {
                            key: {"id": f"ocid1.compartment.oc1..{role}"}
                            for role, key in children.items()
                        }
                    },
                }
            },
            "op02": {
                "network_resources": {
                    "sensitive": False,
                    "type": ["object", {}],
                    "value": {
                        "vcns": {VCN_KEY: {"id": "ocid1.vcn.oc1..projects"}},
                        "subnets": {
                            key: {"id": f"ocid1.subnet.oc1..{role}"}
                            for role, key in SUBNET_KEYS.items()
                        },
                    },
                }
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            output_paths = {}
            for name, output in terraform_outputs.items():
                output_paths[name] = fixture / f"{name}-output.json"
                output_paths[name].write_text(json.dumps(output), encoding="utf-8")
            result = build_handoff_data(
                "prod-payments",
                project_config,
                load_json(output_paths["op04"]),
                load_json(output_paths["op02"]),
                network_config,
                "uk-london-1",
            )
        self.assertEqual(result["region"], "uk-london-1")

    def test_workflows_are_environment_aware_and_complete(self):
        workflows = COMPONENT / ".github/workflows"
        op02 = (workflows / "oci-op02-terraform.yaml").read_text()
        op04 = (workflows / "oci-op04-terraform.yaml").read_text()
        handoff = (workflows / "oci-project-handoff.yaml").read_text()
        self.assertFalse((workflows / "oci-op02-prod-terraform.yaml").exists())
        self.assertIn("op02_manage_environment/**", op02)
        self.assertIn("^(dev|test|uat|prod)$", op02)
        self.assertIn("^(dev|test|uat|prod)-", op04)
        self.assertNotIn("oe-(prod|dev)", op04)
        self.assertIn('git cat-file -e "$CONTRACT_REF:$BLUEPRINT_PATH"', op04)
        self.assertIn(".environment_blueprints[$environment]", op04)
        self.assertIn('--target-repository "$TARGET_REPOSITORY"', handoff)
        self.assertIn('--handoff-path "$HANDOFF_PATH"', handoff)
        self.assertNotIn("enviroment_information.md", handoff)

    def test_foundation_workflows_fail_closed_until_explicitly_enabled(self):
        workflows = COMPONENT / ".github/workflows"
        guarded = (
            "oci-bootstrap-terraform.yaml",
            "oci-op00-terraform.yaml",
            "oci-op01-terraform.yaml",
            "oci-op02-terraform.yaml",
            "oci-op03-platform-gitops-terraform.yaml",
            "oci-op04-terraform.yaml",
            "oci-project-handoff.yaml",
        )
        for workflow in guarded:
            content = (workflows / workflow).read_text(encoding="utf-8")
            self.assertIn(
                "vars.FOUNDATION_AUTOMATION_READY == 'true'", content, workflow
            )

    def test_packaged_cloud_skill_validates_handoff_and_write_boundaries(self):
        handoff = self.machine_handoff("test")
        markdown = " ".join(
            ["test-payments", "test", handoff["region"]]
            + [
                handoff[field]
                for field in (
                    "app_compartment",
                    "database_compartment",
                    "infrastructure_compartment",
                    "vcn",
                )
            ]
            + list(handoff["subnets"].values())
        )
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            json_path = fixture / "project-foundation-handoff.json"
            markdown_path = fixture / "environment_information.md"
            json_path.write_text(json.dumps(handoff), encoding="utf-8")
            markdown_path.write_text(markdown, encoding="utf-8")
            command = [
                sys.executable,
                str(CLOUD_SKILL / "scripts/validate-handoff.py"),
                "--handoff-json",
                str(json_path),
                "--handoff-markdown",
                str(markdown_path),
                "--project",
                "test-payments",
            ]
            accepted = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            handoff["target_repository"] = "nonprod-other"
            json_path.write_text(json.dumps(handoff), encoding="utf-8")
            rejected = subprocess.run(command, check=False, capture_output=True, text=True)
            self.assertNotEqual(rejected.returncode, 0)

        skill = (CLOUD_SKILL / "SKILL.md").read_text()
        safety = (CLOUD_SKILL / "references/safety-boundaries.md").read_text()
        self.assertIn("validate-handoff.py", skill)
        self.assertIn("exact contract-pinned template", safety)
        self.assertNotIn("Never create or write a project repository", safety)


if __name__ == "__main__":
    unittest.main()
