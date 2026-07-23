import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "components" / "oci-landing-zone"
SCRIPTS = COMPONENT / "scripts"
ORCHESTRATOR_REVISION = "fcf1d7f02c0b4faa1ff55f1776c396452dd51761"
OE_REVISION = "172809932c53467ab20ec6d1b44290a487211b36"
sys.path.insert(0, str(SCRIPTS))

from render_project_handoff import (  # noqa: E402
    build_handoff_data,
    build_machine_handoff,
    render_markdown,
)


class LandingZoneContractTests(unittest.TestCase):
    def environment_blueprint(self, environment="dev"):
        token = environment.upper()
        return {
            "schema_version": 2,
            "environment": environment,
            "region": "eu-frankfurt-1",
            "tenancy_ocid": "ocid1.tenancy.oc1..example",
            "parent_compartment_key": f"CMP-LZ-{token}-PROJECTS-KEY",
            "parent_compartment_ocid":
                "ocid1.compartment.oc1..projects",
            "compartments": {
                "projects": {
                    "key": f"CMP-LZ-{token}-PROJECTS-KEY",
                    "ocid": "ocid1.compartment.oc1..projects",
                },
                "network": {
                    "key": f"CMP-LZ-{token}-NETWORK-KEY",
                    "ocid": "ocid1.compartment.oc1..network",
                },
                "security": {
                    "key": f"CMP-LZ-{token}-SECURITY-KEY",
                    "ocid": "ocid1.compartment.oc1..security",
                },
            },
            "network": {
                "vcn": {
                    "key": f"VCN-FRA-LZ-{token}-PROJECTS-KEY",
                    "name": "projects",
                    "cidr": "10.20.0.0/21",
                    "ocid":
                        "ocid1.vcn.oc1.eu-frankfurt-1.example",
                },
                "subnets": {
                    role: {
                        "key":
                            f"SN-FRA-LZ-{token}-{role.upper()}-KEY",
                        "name": role,
                        "cidr": f"10.20.{index}.0/24",
                        "ocid":
                            "ocid1.subnet.oc1.eu-frankfurt-1."
                            f"{role}",
                    }
                    for index, role in enumerate(
                        ("web", "app", "database", "infrastructure"),
                        start=1,
                    )
                },
            },
            "op02_state_key":
                f"op02_manage_environment/{environment}/terraform.tfstate",
            "source": {
                "repository": "customer/oci-landing-zone",
                "workflow": "oci-op02-terraform.yaml",
                "run_id": "42",
                "commit_sha": "c" * 40,
            },
        }

    def project_config(self, environment="dev", project_name="payments"):
        key = f"CMP-LZ-{environment.upper()}-{project_name.upper()}-KEY"
        return {
            "compartments_configuration": {
                "compartments": {
                    key: {
                        "name":
                            f"cmp-lz-{environment}-{project_name}",
                    },
                }
            }
        }

    def op04_output(self, environment="dev", project_name="payments"):
        key = f"CMP-LZ-{environment.upper()}-{project_name.upper()}-KEY"
        return {
            "iam_resources": {
                "compartments": {
                    key: {"id": "ocid1.compartment.oc1..project"},
                }
            }
        }

    def test_deployment_contract_pins_all_official_sources(self):
        contract = json.loads(
            (ROOT / "contracts/deployment-contract.template.json").read_text()
        )
        self.assertEqual(
            contract["oci_orchestrator"]["revision"],
            ORCHESTRATOR_REVISION,
        )
        self.assertEqual(
            contract["oci_landing_zone_operating_entities"],
            {
                "repository":
                    "oci-landing-zones/"
                    "oci-landing-zone-operating-entities",
                "release": "v3.1.0",
                "revision": OE_REVISION,
            },
        )
        self.assertEqual(
            contract["oci_database_modules"]["revision"],
            "55eeee14808f864e450db550530d760f9e0b0105",
        )
        self.assertEqual(contract["terraform"]["version"], "1.15.8")

    def test_foundation_is_multistack_and_bootstrap_is_read_only(self):
        workflows = COMPONENT / ".github/workflows"
        bootstrap = (workflows / "oci-bootstrap-readiness.yaml").read_text()
        self.assertNotIn("terraform plan", bootstrap)
        self.assertNotIn("terraform apply", bootstrap)
        self.assertIn("--auth instance_principal", bootstrap)
        self.assertIn('.versioning == "Enabled"', bootstrap)
        for phase, state_key in {
            "oci-op00-terraform.yaml":
                "op00_manage_global_landing_zone/terraform.tfstate",
            "oci-op01-terraform.yaml":
                "op01_manage_landing_zone_environment/terraform.tfstate",
            "oci-op03-platform-gitops-terraform.yaml":
                "op03_manage_platform_gitops/terraform.tfstate",
        }.items():
            content = (workflows / phase).read_text()
            self.assertIn(ORCHESTRATOR_REVISION, content)
            self.assertIn(state_key, content)
            self.assertIn("terraform_version: 1.15.8", content)
            self.assertIn("terraform_wrapper: false", content)
            self.assertIn('required_version = ">= 1.5.0"', content)
            self.assertIn("pull_request_target:", content)
            self.assertIn(
                'rm -rf -- "$GITHUB_WORKSPACE/ORCH"',
                content,
            )
            self.assertIn("apply", content.lower())
        for phase in (
            "oci-op02-terraform.yaml",
            "oci-op04-terraform.yaml",
        ):
            content = (workflows / phase).read_text()
            self.assertIn("terraform_version: 1.15.8", content)
            self.assertIn("terraform_wrapper: false", content)
            self.assertIn('required_version = ">= 1.5.0"', content)
            self.assertIn(
                'rm -rf -- "$GITHUB_WORKSPACE/ORCH"',
                content,
            )

    def test_foundation_runner_bootstrap_is_reproducible(self):
        cloud_init = (
            COMPONENT / "docs/foundation-runner-cloud-init.yaml"
        ).read_text()
        runbook = (COMPONENT / "docs/new-tenancy.md").read_text()
        for value in (
            "ripgrep/releases/download/15.2.0",
            "go-jsonnet/releases/download/v0.22.0",
            "actions/runner/releases/download/v2.336.0",
            "python39-oci-cli",
        ):
            self.assertIn(value, cloud_init)
        readiness = (
            COMPONENT / ".github/workflows/oci-bootstrap-readiness.yaml"
        ).read_text()
        self.assertIn("git jq jsonnet oci rg", readiness)
        runner = json.loads(
            (
                COMPONENT
                / "op03_manage_platform_gitops/configuration/runner.json"
            ).read_text()
        )
        runner_script = runner["instances_configuration"]["instances"][
            "VM-LZ-SHARED-GITOPS-RUNNER-KEY"
        ]["cloud_init"]["heredoc_script"]
        self.assertIn("jq python3", runner_script)
        self.assertNotIn("nodejs", runner_script)
        self.assertIn("--versioning Enabled", runbook)
        self.assertIn('."cidr-block"', runbook)
        self.assertIn("--is-ipv6-enabled false", runbook)
        self.assertIn("GitHub Free does not enforce branch protection", runbook)

    def test_phase_projection_uses_pinned_oe_and_official_project_model(self):
        render = (COMPONENT / "config/render.libsonnet").read_text()
        generator = (COMPONENT / "scripts/generate_foundation.sh").read_text()
        op04 = (
            COMPONENT / ".github/workflows/oci-op04-terraform.yaml"
        ).read_text()
        self.assertIn("local lz = import 'landing_zone.libsonnet'", render)
        self.assertIn("without_retired_osms_statement", render)
        self.assertIn(
            "statement != retired_osms_statement",
            render,
        )
        self.assertIn("project_identity(environment, project)", render)
        self.assertIn("dg-mccp-platform-runner", render)
        self.assertNotIn("project_key[0:", render)
        self.assertNotIn("'-APP-KEY'", render)
        self.assertIn(OE_REVISION, generator)
        self.assertIn(OE_REVISION, op04)
        self.assertIn("config/projects.json", op04)
        self.assertEqual(
            list((COMPONENT / "op04_manage_project/templates").glob("*")),
            [],
        )

    def test_handoff_uses_protected_environment_evidence(self):
        data = build_handoff_data(
            "dev-payments",
            self.project_config(),
            self.op04_output(),
            self.environment_blueprint(),
        )
        handoff = build_machine_handoff(
            data,
            {
                "repository": "customer/oci-landing-zone",
                "workflow": "OCI Project Foundation Handoff",
                "run": "42",
                "commit": "c" * 40,
            },
            "op02_manage_environment/dev/terraform.tfstate",
            "op04_manage_project/dev/dev-payments/terraform.tfstate",
            "nonprod-payments",
            "environments/dev/environment_information.md",
        )
        self.assertEqual(handoff["repository_layout"], "shared-nonprod-v2")
        self.assertEqual(
            handoff["database_compartment"],
            "ocid1.compartment.oc1..project",
        )
        self.assertEqual(
            {
                handoff["app_compartment"],
                handoff["database_compartment"],
                handoff["infrastructure_compartment"],
            },
            {"ocid1.compartment.oc1..project"},
        )
        handoff_workflow = (
            COMPONENT / ".github/workflows/oci-project-handoff.yaml"
        ).read_text()
        self.assertIn("--environment-blueprint", handoff_workflow)
        self.assertNotIn("--op02-output", handoff_workflow)

    @unittest.skipIf(
        sys.version_info < (3, 10),
        "The packaged Project GitOps runtime requires Python 3.10+.",
    )
    def test_handoff_is_accepted_by_the_packaged_project_skill(self):
        validator_path = (
            ROOT.parent
            / "multi-cloud-control-plane/plugins/project-gitops"
            / "skills/project-gitops/scripts/validate-change.py"
        )
        spec = importlib.util.spec_from_file_location(
            "packaged_project_validator",
            validator_path,
        )
        validator = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = validator
        spec.loader.exec_module(validator)
        markdown = render_markdown(
            build_handoff_data(
                "dev-payments",
                self.project_config(),
                self.op04_output(),
                self.environment_blueprint(),
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            handoff = (
                Path(temporary)
                / "environments/dev/environment_information.md"
            )
            handoff.parent.mkdir(parents=True)
            handoff.write_text(markdown, encoding="utf-8")
            validator.validate_handoff(
                Path(temporary),
                "nonprod-payments",
                "dev",
            )
            handoff.write_text(
                markdown.replace(
                    "| DB compartment | "
                    "CMP-LZ-DEV-PAYMENTS-KEY | "
                    "ocid1.compartment.oc1..project |",
                    "| DB compartment | "
                    "CMP-LZ-DEV-PAYMENTS-DB-KEY | "
                    "ocid1.compartment.oc1..retired-child |",
                ),
                encoding="utf-8",
            )
            with self.assertRaises(validator.ValidationFailure):
                validator.validate_handoff(
                    Path(temporary),
                    "nonprod-payments",
                    "dev",
                )

    def test_no_stale_static_phase_files_remain(self):
        stale = [
            path
            for path in COMPONENT.rglob("*auto.tfvars.json*")
            if "/generated/" not in str(path)
        ]
        self.assertEqual(stale, [])
        self.assertEqual(
            list((COMPONENT / "bootstrap").glob("*")),
            [],
        )

    def test_documentation_links_and_bootstrap_model_are_current(self):
        link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        stale_phrases = (
            "Bootstrap creates the permanent runner",
            "bootstrap/terraform.tfstate",
            "two-pass operation",
        )
        for document in ROOT.rglob("*.md"):
            text = document.read_text(encoding="utf-8")
            for phrase in stale_phrases:
                self.assertNotIn(phrase, text, str(document))
            for raw_target in link_pattern.findall(text):
                target = raw_target.split("#", 1)[0]
                if (
                    not target
                    or "://" in target
                    or target.startswith(("mailto:", "<"))
                ):
                    continue
                resolved = (document.parent / target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"{document}: broken relative link {raw_target}",
                )

    def test_scripts_compile_without_repository_cache_files(self):
        with tempfile.TemporaryDirectory() as cache:
            environment = os.environ.copy()
            environment["PYTHONPYCACHEPREFIX"] = cache
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "py_compile",
                    *[str(path) for path in SCRIPTS.glob("*.py")],
                ],
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
