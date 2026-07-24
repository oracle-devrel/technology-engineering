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
PLUGIN_SCRIPTS = (
    ROOT
    / "plugins/cloud-operator-gitops/skills/cloud-operator-gitops/scripts"
)
PROJECT_TEMPLATES = (
    ROOT.parent / "multi-cloud-control-plane/components"
)
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
        self.assertEqual(
            contract["project_state_bucket"],
            "__PROJECT_STATE_BUCKET__",
        )
        initialization = contract["project_repository_initialization"]
        self.assertEqual(
            set(initialization),
            {"shared-nonprod-v2", "production-v1"},
        )
        self.assertEqual(
            initialization["shared-nonprod-v2"]["security_profile"],
            "__NONPROD_SECURITY_PROFILE__",
        )
        self.assertEqual(
            set(
                initialization["shared-nonprod-v2"]["codeowners"]
            ),
            {"platform", "dev", "test", "uat"},
        )
        self.assertEqual(
            initialization["production-v1"]["security_profile"],
            "__PROD_SECURITY_PROFILE__",
        )

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
        op03 = (
            workflows / "oci-op03-platform-gitops-terraform.yaml"
        ).read_text()
        self.assertIn(
            "PROJECT_STATE_BUCKET: ${{ vars.PROJECT_STATE_BUCKET }}",
            op03,
        )
        self.assertIn(
            'test "$PROJECT_STATE_BUCKET" != "$STATE_BUCKET"',
            op03,
        )
        self.assertIn(
            "target.bucket.name = '$PROJECT_STATE_BUCKET'",
            op03,
        )
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
        for phase in (
            "oci-op00-terraform.yaml",
            "oci-op01-terraform.yaml",
            "oci-op02-terraform.yaml",
            "oci-op03-platform-gitops-terraform.yaml",
            "oci-op04-terraform.yaml",
        ):
            content = (workflows / phase).read_text()
            self.assertEqual(
                content.count(
                    '"Oracle-Tags.CreatedBy",'
                ),
                3,
            )
            self.assertEqual(
                content.count(
                    '"Oracle-Tags.CreatedOn",'
                ),
                3,
            )
            self.assertEqual(content.count("ignore_defined_tags = ["), 3)
        for workflow in workflows.glob("*.yaml"):
            content = workflow.read_text()
            self.assertNotIn(
                'terraform { backend "oci" {} }',
                content,
                workflow.name,
            )
            self.assertIsNone(
                re.search(
                    r'-var=["\']?[a-z_]+_dependency=',
                    content,
                ),
                workflow.name,
            )
        for workflow, dependency_file in {
            "oci-op01-terraform.yaml":
                "op01-dependencies.tfvars.json",
            "oci-op02-terraform.yaml":
                "op02-dependencies.tfvars.json",
            "oci-op03-platform-gitops-terraform.yaml":
                "op03-dependencies.tfvars.json",
            "oci-op04-terraform.yaml":
                "op04-dependencies.tfvars.json",
        }.items():
            content = (workflows / workflow).read_text()
            self.assertGreaterEqual(
                content.count(dependency_file),
                2,
                workflow,
            )
            self.assertIn("terraform.tfstate.json", content, workflow)
            self.assertIn("state pull", content, workflow)
            self.assertIn(
                ".instances[]?.attributes.content",
                content,
                workflow,
            )
            self.assertIn(
                "Expected exactly one Orchestrator dependency artifact",
                content,
                workflow,
            )
        for workflow, artifacts in {
            "oci-op01-terraform.yaml": ("compartments_output",),
            "oci-op02-terraform.yaml": (
                "compartments_output",
                "network_output",
                "tags_output",
            ),
            "oci-op03-platform-gitops-terraform.yaml": (
                "compartments_output",
                "network_output",
            ),
            "oci-op04-terraform.yaml": (
                "identity_domains_output",
                "compartments_output",
            ),
        }.items():
            content = (workflows / workflow).read_text()
            for artifact in artifacts:
                self.assertIn(artifact, content, workflow)

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
        self.assertIn("dnf install -y curl git", runner_script)
        self.assertIn("python3.11 python3.11-pip", runner_script)
        self.assertIn(
            "ripgrep/releases/download/15.2.0",
            runner_script,
        )
        self.assertIn(
            "a740b91c82eaf9914cfedd353572f2791cbe0162c84101ee0951058f4dcbc90d",
            runner_script,
        )
        self.assertIn("jq python3", runner_script)
        self.assertNotIn("nodejs", runner_script)
        self.assertIn("--versioning Enabled", runbook)
        self.assertIn(
            "export PROJECT_STATE_BUCKET=mccp-project-tfstate",
            runbook,
        )
        self.assertIn('."cidr-block"', runbook)
        self.assertIn("--is-ipv6-enabled false", runbook)
        self.assertIn("GitHub Free does not enforce branch protection", runbook)
        self.assertIn(
            "On GitHub Free, leave it unregistered until the\n"
            "    project repository exists",
            runbook,
        )
        self.assertIn(
            "GitHub Free private\nrepositories must use repository-scoped "
            "registration after OP04",
            runbook,
        )
        self.assertIn("STATE_NAMESPACE=<object-storage-namespace>", runbook)
        self.assertIn("OCI_CLI_AUTH=instance_principal", runbook)
        self.assertIn(
            "/home/github-runner/.local/bin:/usr/local/bin:/usr/local/sbin:"
            "/usr/bin:/usr/sbin:/bin:/sbin",
            runbook,
        )

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
        self.assertIn(
            "drg_route_statement_key(distribution_key)",
            render,
        )
        self.assertIn(
            "without_shared_network_security_zone(active_render.security_cis1)",
            render,
        )
        self.assertIn(
            "with_platform_bastion_endpoint(",
            render,
        )
        self.assertIn(
            "platform_bastion_private_endpoint_cidr must be null or an IPv4 /32",
            render,
        )
        self.assertIn(
            "if key != shared_network_zone_key",
            render,
        )
        self.assertIn(
            "active_render.security_cis1_pre",
            render,
        )
        self.assertNotIn("'ROUTE-ALL-VCNS-KEY'", render)
        self.assertIn("project_identity(environment, project)", render)
        self.assertIn("dg-mccp-platform-runner", render)
        self.assertIn(
            "manage network-security-groups in compartment cmp-lz-%s-%s",
            render,
        )
        self.assertIn(
            "manage vcns in compartment cmp-lz-%s-network where any "
            "{request.operation = 'CreateNetworkSecurityGroup', "
            "request.operation = 'DeleteNetworkSecurityGroup'}",
            render,
        )
        self.assertIn(
            "if suffix == 'project' then project_container_key",
            render,
        )
        self.assertIn("else environment_key", render)
        self.assertNotIn(
            "manage network-security-groups in compartment cmp-lz-%s-network",
            render,
        )
        self.assertNotIn("project_key[0:", render)
        self.assertNotIn("'-APP-KEY'", render)
        self.assertIn(OE_REVISION, generator)
        self.assertIn(OE_REVISION, op04)
        self.assertIn("config/projects.json", op04)
        self.assertIn(
            "one generated IAM maintenance update or one two-file project addition",
            op04,
        )
        self.assertIn(
            'git diff --quiet "$BASE_SHA" "$HEAD_SHA" --',
            op04,
        )
        self.assertIn(
            '.[$environment] | index($project) != null',
            op04,
        )
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

    def test_cloud_operator_initializes_project_repositories_fail_closed(self):
        initializer_source = (
            PLUGIN_SCRIPTS / "render-project-repository.py"
        ).read_text()
        validator_source = (
            PLUGIN_SCRIPTS / "validate-project-repository.py"
        ).read_text()
        self.assertIn(
            "validate_template_placeholders(repo, initialization)",
            initializer_source,
        )
        self.assertIn(
            'git(repo, "rev-parse", "HEAD^{commit}").strip() != base',
            validator_source,
        )
        self.assertIn(
            "validate_no_placeholders(repo)",
            validator_source,
        )
        for environment, layout, template_name, profile in (
            (
                "dev",
                "shared-nonprod-v2",
                "nonprod-project-template",
                "repository-secrets",
            ),
            (
                "prod",
                "production-v1",
                "prod-project-template",
                "github-environments",
            ),
        ):
            with self.subTest(environment=environment):
                project = f"{environment}-payments"
                target = (
                    "prod-payments"
                    if environment == "prod"
                    else "nonprod-payments"
                )
                with tempfile.TemporaryDirectory() as temporary:
                    temporary_path = Path(temporary)
                    repo = temporary_path / "repo"
                    (repo / ".github").mkdir(parents=True)
                    handoff_path = (
                        repo
                        / f"environments/{environment}/"
                        "environment_information.md"
                    )
                    handoff_path.parent.mkdir(parents=True)
                    template = PROJECT_TEMPLATES / template_name
                    (repo / "control-plane.json").write_bytes(
                        (template / "control-plane.json").read_bytes()
                    )
                    (repo / ".github/CODEOWNERS.template").write_bytes(
                        (
                            template / ".github/CODEOWNERS.template"
                        ).read_bytes()
                    )
                    handoff_path.write_text(
                        "# Pending project handoff\n",
                        encoding="utf-8",
                    )
                    subprocess.run(
                        ["git", "init", "-b", "main"],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["git", "add", "-A"],
                        cwd=repo,
                        check=True,
                    )
                    subprocess.run(
                        [
                            "git",
                            "-c",
                            "user.name=Test",
                            "-c",
                            "user.email=test@example.invalid",
                            "commit",
                            "-m",
                            "template",
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    base = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        cwd=repo,
                        check=True,
                        text=True,
                        capture_output=True,
                    ).stdout.strip()
                    subprocess.run(
                        [
                            "git",
                            "remote",
                            "add",
                            "origin",
                            f"https://github.com/customer/{target}.git",
                        ],
                        cwd=repo,
                        check=True,
                    )
                    subprocess.run(
                        [
                            "git",
                            "checkout",
                            "-b",
                            f"agent/project-handoff-{project}-{base[:12]}",
                        ],
                        cwd=repo,
                        check=True,
                        capture_output=True,
                    )
                    data = build_handoff_data(
                        project,
                        self.project_config(environment),
                        self.op04_output(environment),
                        self.environment_blueprint(environment),
                    )
                    markdown_path = temporary_path / "handoff.md"
                    markdown_path.write_text(
                        render_markdown(data),
                        encoding="utf-8",
                    )
                    machine_path = temporary_path / "handoff.json"
                    machine_path.write_text(
                        json.dumps(
                            build_machine_handoff(
                                data,
                                {
                                    "repository":
                                        "customer/oci-landing-zone",
                                    "workflow":
                                        "OCI Project Foundation Handoff",
                                    "run": "42",
                                    "commit": "c" * 40,
                                },
                                "op02_manage_environment/"
                                f"{environment}/terraform.tfstate",
                                "op04_manage_project/"
                                f"{environment}/{project}/terraform.tfstate",
                                target,
                                "environments/"
                                f"{environment}/"
                                "environment_information.md",
                            ),
                            indent=2,
                        )
                        + "\n",
                        encoding="utf-8",
                    )
                    contract = json.loads(
                        (
                            ROOT
                            / "contracts/"
                            "deployment-contract.template.json"
                        ).read_text()
                    )
                    contract.update(
                        {
                            "customer_org": "customer",
                            "foundation_repository":
                                "customer/oci-landing-zone",
                            "foundation_ref": "a" * 40,
                            "project_state_bucket":
                                "customer-project-state",
                            "environments": [
                                {
                                    "name": environment,
                                    "region": "eu-frankfurt-1",
                                }
                            ],
                        }
                    )
                    contract["project_templates"][
                        "shared-nonprod-v2"
                    ]["repository"] = (
                        "customer/nonprod-project-template"
                    )
                    contract["project_templates"][
                        "shared-nonprod-v2"
                    ]["revision"] = "b" * 40
                    contract["project_templates"][
                        "production-v1"
                    ]["repository"] = "customer/prod-project-template"
                    contract["project_templates"][
                        "production-v1"
                    ]["revision"] = "d" * 40
                    contract["project_repository_initialization"] = {
                        "shared-nonprod-v2": {
                            "security_profile": "repository-secrets",
                            "codeowners": {
                                "platform":
                                    ["@customer/platform-team"],
                                "dev": ["@customer/dev-approvers"],
                                "test": ["@customer/test-approvers"],
                                "uat": ["@customer/uat-approvers"],
                            },
                        },
                        "production-v1": {
                            "security_profile": "github-environments",
                            "codeowners": {
                                "platform":
                                    ["@customer/platform-team"],
                                "prod": ["@customer/prod-approvers"],
                            },
                        },
                    }
                    contract_path = temporary_path / "deployment-contract.json"
                    contract_path.write_text(
                        json.dumps(contract, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    common = [
                        "--repo",
                        str(repo),
                        "--deployment-contract",
                        str(contract_path),
                        "--handoff-json",
                        str(machine_path),
                        "--handoff-markdown",
                        str(markdown_path),
                        "--project",
                        project,
                    ]
                    rendered = subprocess.run(
                        [
                            sys.executable,
                            str(
                                PLUGIN_SCRIPTS
                                / "render-project-repository.py"
                            ),
                            *common,
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        rendered.returncode,
                        0,
                        rendered.stdout + rendered.stderr,
                    )
                    validated = subprocess.run(
                        [
                            sys.executable,
                            str(
                                PLUGIN_SCRIPTS
                                / "validate-project-repository.py"
                            ),
                            *common,
                            "--base-ref",
                            "main",
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(
                        validated.returncode,
                        0,
                        validated.stdout + validated.stderr,
                    )
                    result = json.loads(validated.stdout)
                    self.assertEqual(
                        result["summary"]["repository_layout"],
                        layout,
                    )
                    self.assertEqual(
                        result["summary"]["security_profile"],
                        profile,
                    )
                    control_plane = json.loads(
                        (repo / "control-plane.json").read_text()
                    )
                    self.assertEqual(
                        control_plane["target_repository"],
                        target,
                    )
                    self.assertEqual(
                        control_plane["security_profile"],
                        profile,
                    )
                    self.assertFalse(
                        (repo / ".github/CODEOWNERS.template").exists()
                    )
                    self.assertTrue(
                        (repo / ".github/CODEOWNERS").is_file()
                    )
                    control_plane["target_repository"] = "nonprod-wrong"
                    (repo / "control-plane.json").write_text(
                        json.dumps(control_plane, indent=2) + "\n"
                    )
                    rejected = subprocess.run(
                        [
                            sys.executable,
                            str(
                                PLUGIN_SCRIPTS
                                / "validate-project-repository.py"
                            ),
                            *common,
                            "--base-ref",
                            "main",
                        ],
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(rejected.returncode, 2)
                    self.assertIn(
                        "initialized control-plane contract is invalid",
                        rejected.stdout,
                    )

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

    def test_repeatability_exception_is_narrowly_documented(self):
        for document in (
            ROOT / "docs/operations.md",
            COMPONENT / "docs/operations.md",
        ):
            text = document.read_text(encoding="utf-8")
            self.assertIn(
                "terraform-oci-modules-observability/issues/17",
                text,
            )
            self.assertIn("target.compartment_id", text)
            self.assertIn(
                "no other OCI changes, replacements, or destroys",
                text,
            )
            self.assertIn(
                "Do not patch the downloaded official module",
                text,
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
                    *[
                        str(path)
                        for path in PLUGIN_SCRIPTS.glob("*.py")
                    ],
                ],
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
