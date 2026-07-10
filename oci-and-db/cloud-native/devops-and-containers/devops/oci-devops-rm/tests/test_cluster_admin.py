import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import yaml


ROOT = Path(__file__).resolve().parents[1]


def load_script(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "repos/cluster-admin/script" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_config = load_script("validate_config", "validate-config.py")
dispatch = load_script("publish_and_dispatch", "publish-and-dispatch.py")
mirror = load_script("mirror_charts", "mirror-charts.py")
cluster_deploy = load_script("deploy_cluster", "deploy-cluster.py")


class ClusterAdminValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        self.write("catalog/tools.yaml", """
tools:
  cert-manager:
    repository: https://charts.example.test
    chart: cert-manager
    version: 1.0.0
  traefik:
    repository: https://charts.example.test
    chart: traefik-controller
    version: 2.0.0
""")
        for cluster in ("noprod", "prod"):
            self.write(f"clusters/{cluster}/baseline/README.md", "baseline\n")
        self.write("clusters/noprod/tools/cert-manager/tool.yaml", """
name: cert-manager
namespace: cert-manager
depends_on: []
""")
        self.write("clusters/noprod/tools/cert-manager/values.yaml", "replicas: 1\n")
        self.write("clusters/noprod/tools/traefik/tool.yaml", """
name: traefik
namespace: traefik
depends_on:
  - cert-manager
""")
        self.write("clusters/noprod/tools/traefik/values.yaml", "replicas: 1\n")
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.commit("Initial configuration")

    def tearDown(self):
        self.temp.cleanup()

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.strip() + "\n", encoding="utf-8")

    def git(self, *arguments):
        return subprocess.check_output(["git", "-C", str(self.repo), *arguments], text=True).strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)
        return self.git("rev-parse", "HEAD")

    def targets(self, commit):
        result = validate_config.validate(self.repo, commit, "changed")
        return {(target["kind"], target.get("tool")): target for target in result["targets"]}

    def test_values_change_selects_helm_only(self):
        self.write("clusters/noprod/tools/traefik/values.yaml", "replicas: 2\n")
        targets = self.targets(self.commit("Change Traefik values"))
        self.assertEqual(targets[("tool", "traefik")]["actions"], ["helm"])
        self.assertEqual(len(targets), 1)

    def test_prerequisite_change_selects_downstream_tool(self):
        self.write("clusters/noprod/tools/cert-manager/values.yaml", "replicas: 2\n")
        targets = self.targets(self.commit("Change cert-manager values"))
        self.assertEqual(targets[("tool", "cert-manager")]["actions"], ["helm"])
        self.assertEqual(targets[("tool", "traefik")]["actions"], ["helm", "resources"])

    def test_resource_change_selects_resources_only(self):
        self.write(
            "clusters/noprod/tools/traefik/resources/configmap.yaml",
            "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test\n",
        )
        targets = self.targets(self.commit("Add Traefik resource"))
        self.assertEqual(targets[("tool", "traefik")]["actions"], ["resources"])

    def test_dependency_cycle_is_rejected(self):
        self.write("clusters/noprod/tools/cert-manager/tool.yaml", """
name: cert-manager
namespace: cert-manager
depends_on:
  - traefik
""")
        commit = self.commit("Create dependency cycle")
        with self.assertRaisesRegex(ValueError, "dependency cycle"):
            validate_config.validate(self.repo, commit, "changed")

    def test_logical_tool_name_can_differ_from_upstream_chart(self):
        result = validate_config.validate(self.repo, self.git("rev-parse", "HEAD"), "all")
        traefik = next(
            target for target in result["targets"]
            if target.get("tool") == "traefik"
        )
        self.assertEqual(traefik["chart_version"], "2.0.0")
        self.assertEqual(traefik["chart"], "traefik-controller")

    def test_oci_chart_repository_is_valid(self):
        self.write("catalog/tools.yaml", """
tools:
  cert-manager:
    repository: https://charts.example.test
    chart: cert-manager
    version: 1.0.0
  traefik:
    repository: https://charts.example.test
    chart: traefik-controller
    version: 2.0.0
  external-dns:
    repository: oci://registry-1.docker.io/bitnamicharts
    chart: external-dns
    version: 9.0.3
""")
        self.write("clusters/noprod/tools/external-dns/tool.yaml", """
name: external-dns
namespace: external-dns
depends_on: []
""")
        self.write("clusters/noprod/tools/external-dns/values.yaml", "provider: oci\n")
        commit = self.commit("Add OCI chart source")

        result = validate_config.validate(self.repo, commit, "all")
        external_dns = next(
            target for target in result["targets"]
            if target.get("tool") == "external-dns"
        )
        self.assertEqual(external_dns["chart_version"], "9.0.3")


class DependencyWaveTests(unittest.TestCase):
    def test_cluster_admin_feature_is_opt_in_and_gates_resource_maps(self):
        root_variables = (ROOT / "variables.tf").read_text(encoding="utf-8")
        module_locals = (ROOT / "modules/devops/locals.tf").read_text(encoding="utf-8")
        schema = (ROOT / "schema.yaml").read_text(encoding="utf-8")

        self.assertRegex(
            root_variables,
            r'variable "enable_cluster_admin" \{[^}]*default\s*=\s*false',
        )
        self.assertIn(
            'cluster_admin_singleton = var.enable_cluster_admin ? { enabled = true } : {}',
            module_locals,
        )
        self.assertIn('cluster_admin_clusters = var.enable_cluster_admin ? {', module_locals)
        self.assertIn('visible: ${enable_cluster_admin}', schema)
        self.assertRegex(schema, r'development_mode:\n(?:.*\n){0,6}\s+visible: false')
        self.assertIn('"name": "keda"', schema)
        self.assertIn('"name": "kube-prometheus"', schema)
        self.assertIn('"repository": "https://kedacore.github.io/charts"', schema)
        self.assertIn('"chart": "kube-prometheus-stack"', schema)
        self.assertIn('"version": "87.10.1"', schema)
        self.assertIn('"name": "sample-api"', schema)
        self.assertIn('"name": "sample-worker"', schema)

    def test_cluster_admin_schema_default_is_pretty_printed_json(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text(encoding="utf-8"))
        default = schema["variables"]["cluster_administration"]["default"]

        self.assertGreater(len(default.splitlines()), 10)
        self.assertIn('\n      "repository": "https://kedacore.github.io/charts",', default)
        self.assertEqual(json.loads(default)["tools"][1]["chart"], "kube-prometheus-stack")

    def test_cluster_admin_artifact_repository_name_is_configurable(self):
        root_variables = (ROOT / "variables.tf").read_text(encoding="utf-8")
        root_main = (ROOT / "main.tf").read_text(encoding="utf-8")
        module_repositories = (
            ROOT / "modules/devops/cluster_admin_repositories.tf"
        ).read_text(encoding="utf-8")
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text(encoding="utf-8"))

        self.assertIn('variable "cluster_admin_artifact_repository_name"', root_variables)
        self.assertIn(
            "cluster_admin_artifact_repository_name = var.cluster_admin_artifact_repository_name",
            root_main,
        )
        self.assertIn('"${local.project_repo_prefix}-cluster-admin-values"', module_repositories)
        field = schema["variables"]["cluster_admin_artifact_repository_name"]
        self.assertEqual(field["default"], "")
        self.assertEqual(field["visible"], "${enable_cluster_admin}")
        self.assertEqual(field["maxLength"], 255)
        self.assertRegex("operations-artifacts_1", field["pattern"])
        self.assertRegex("", field["pattern"])
        self.assertNotRegex(" invalid", field["pattern"])
        self.assertNotRegex("invalid/child", field["pattern"])

    def test_cluster_admin_is_the_last_resource_manager_section(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text(encoding="utf-8"))
        self.assertEqual(
            schema["variableGroups"][-1]["title"],
            "Cluster Administration (Optional)",
        )

    def test_resource_manager_surfaces_terraform_input_constraints(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text(encoding="utf-8"))
        fields = schema["variables"]

        project = fields["devops_project_name"]
        self.assertEqual(project["minLength"], 1)
        self.assertEqual(project["maxLength"], 100)
        self.assertRegex("oke-devops-starter", project["pattern"])
        self.assertNotRegex("   ", project["pattern"])

        secret = fields["namespace_init_secret_name"]
        self.assertEqual(secret["minLength"], 1)
        self.assertEqual(secret["maxLength"], 63)
        self.assertRegex("ocirsecret", secret["pattern"])
        self.assertNotRegex("OCISecret", secret["pattern"])

        applications = fields["applications"]
        self.assertRegex('[\n  {"name": "app", "components": []}\n]', applications["pattern"])
        self.assertNotRegex('{"tools": []}', applications["pattern"])
        self.assertEqual(applications["maxLength"], 8192)

        cluster_admin = fields["cluster_administration"]
        self.assertRegex('{\n  "tools": []\n}', cluster_admin["pattern"])
        self.assertNotRegex('[]', cluster_admin["pattern"])
        self.assertEqual(cluster_admin["maxLength"], 8192)

    def test_cluster_wide_resources_are_dispatched_after_tools(self):
        source = (ROOT / "repos/cluster-admin/script/deploy-cluster.py").read_text(
            encoding="utf-8"
        )
        tool_dispatch = source.index("for number, wave in enumerate")
        baseline_dispatch = source.index(
            'if any(target["kind"] == "baseline" for target in targets)'
        )
        self.assertLess(tool_dispatch, baseline_dispatch)

    def test_cluster_deploy_supports_managed_runner_python(self):
        source = (ROOT / "repos/cluster-admin/script/deploy-cluster.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("text=True", source)
        self.assertIn("universal_newlines=True", source)

    def test_both_clusters_use_the_shared_orchestrator(self):
        source = (ROOT / "modules/devops/cluster_admin_deploy_pipelines.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn('resource "oci_devops_deploy_stage" "cluster_admin_orchestrator"', source)
        self.assertIn("for_each = local.cluster_admin_clusters", source)
        self.assertNotIn("cluster_admin_dag_tool_helm", source)
        self.assertNotIn("cluster_admin_dag_tool_resources", source)
        self.assertNotIn("cluster_admin_baseline", source)

    def test_prod_uses_one_approved_orchestration_pipeline(self):
        source = (ROOT / "modules/devops/cluster_admin_deploy_pipelines.tf").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('resource "oci_devops_deploy_pipeline" "cluster_admin_approval"', source)
        self.assertIn('resource "oci_devops_deploy_stage" "cluster_admin_approval"', source)
        self.assertIn('resource "oci_devops_deploy_stage" "cluster_admin_orchestrator"', source)
        self.assertIn(
            "id = oci_devops_deploy_stage.cluster_admin_approval[each.key].id",
            source,
        )
        self.assertIn(
            "id = oci_devops_deploy_pipeline.cluster_admin[each.key].id",
            source,
        )

    def test_decommission_is_explicit_and_prod_requires_approval(self):
        source = (ROOT / "modules/devops/cluster_admin_deploy_pipelines.tf").read_text(
            encoding="utf-8"
        )
        self.assertIn('display_name = "cluster-admin-${each.key}-decommission"', source)
        self.assertIn(
            "oci_devops_deploy_stage.cluster_admin_decommission_approval[each.key].id",
            source,
        )

        command_spec = (
            ROOT / "templates/cluster-admin-decommission-command-spec.yaml.tpl"
        ).read_text(encoding="utf-8")
        self.assertNotIn("confirmation", source)
        self.assertNotIn("confirmation", command_spec)
        self.assertIn("oci devops deploy-stage get", command_spec)
        self.assertIn('helm uninstall "$${tool_name}"', command_spec)
        self.assertIn("Namespace $${namespace} was retained", command_spec)

    def test_operations_tags_are_consistent(self):
        expected = {
            "cluster": "noprod",
            "owner": "cluster-administrators",
            "purpose": "cluster-administration",
            "role": "helm",
            "scope": "operations",
            "tool": "traefik",
        }
        dimensions = {"cluster": "noprod", "role": "helm", "tool": "traefik"}
        self.assertEqual(dispatch.operation_tags(**dimensions), expected)
        self.assertEqual(mirror.operation_tags(**dimensions), expected)

    def test_mirror_source_reference_supports_http_and_oci(self):
        self.assertEqual(
            mirror.source_reference("https://charts.example.test", "traefik", "mirror-traefik"),
            "mirror-traefik/traefik",
        )
        self.assertEqual(
            mirror.source_reference(
                "oci://registry-1.docker.io/bitnamicharts/",
                "/external-dns",
                "unused",
            ),
            "oci://registry-1.docker.io/bitnamicharts/external-dns",
        )
        self.assertEqual(
            mirror.target_chart_name("prometheus-community/kube-prometheus-stack"),
            "kube-prometheus-stack",
        )

    def test_clusters_run_as_pipeline_deployments(self):
        calls = []
        original = dispatch.oci
        dispatch.oci = lambda arguments: calls.append(arguments) or {
            "data": {"lifecycle-state": "SUCCEEDED"}
        }
        try:
            for cluster in ("noprod", "prod"):
                dispatch.run_pipeline(
                    f"{cluster}-pipeline",
                    cluster,
                    "a" * 40,
                    {"cluster_name": cluster, "config_commit": "a" * 40},
                    "external-dns[helm], traefik[helm+resources]",
                )
        finally:
            dispatch.oci = original

        self.assertEqual(len(calls), 2)
        for cluster, command in zip(("noprod", "prod"), calls):
            self.assertIn("create-pipeline-deployment", command)
            self.assertNotIn("create-single-stage-deployment", command)
            arguments = json.loads(command[command.index("--deployment-arguments") + 1])["items"]
            self.assertIn({"name": "cluster_name", "value": cluster}, arguments)
            tags = json.loads(command[command.index("--freeform-tags") + 1])
            self.assertEqual(tags["cluster"], cluster)
            self.assertEqual(tags["role"], "cluster-deployment")

    def test_empty_pipeline_defaults_use_nonempty_sentinel(self):
        original = dispatch.oci
        dispatch.oci = lambda arguments: {
            "data": {
                "deploy-pipeline-parameters": {
                    "items": [
                        {"name": "config_commit", "default-value": ""},
                        {"name": "cluster_id", "default-value": "cluster"},
                        {"name": "cluster_name", "default-value": "noprod"},
                    ]
                }
            }
        }
        try:
            arguments = dispatch.pipeline_arguments("pipeline", "a" * 40)
        finally:
            dispatch.oci = original
        self.assertEqual(arguments["config_commit"], "a" * 40)
        self.assertEqual(arguments["cluster_id"], "cluster")
        self.assertEqual(arguments["cluster_name"], "noprod")

    def test_independent_tools_share_a_wave(self):
        targets = [
            {"tool": "cert-manager", "depends_on": []},
            {"tool": "metrics-server", "depends_on": []},
            {"tool": "traefik", "depends_on": ["cert-manager"]},
        ]
        waves = [[target["tool"] for target in wave] for wave in dispatch.dependency_waves(targets)]
        self.assertEqual(waves, [["cert-manager", "metrics-server"], ["traefik"]])
        orchestrator_waves = [
            [target["tool"] for target in wave]
            for wave in cluster_deploy.dependency_waves(targets)
        ]
        self.assertEqual(orchestrator_waves, waves)

    def test_execution_plan_lists_waves_actions_and_baseline_last(self):
        targets = [
            {
                "actions": ["helm"],
                "chart_version": "1.0.0",
                "cluster": "prod",
                "depends_on": [],
                "kind": "tool",
                "namespace": "external-dns",
                "tool": "external-dns",
            },
            {
                "actions": ["helm", "resources"],
                "chart_version": "2.0.0",
                "cluster": "prod",
                "depends_on": ["external-dns"],
                "kind": "tool",
                "namespace": "traefik",
                "tool": "traefik",
            },
            {"cluster": "prod", "kind": "baseline"},
        ]
        plan = dispatch.cluster_plan("prod", targets, "a" * 40)
        self.assertIn("Wave 1:\n  - external-dns: helm", plan)
        self.assertIn("Wave 2:\n  - traefik: helm + resources", plan)
        self.assertLess(plan.index("Wave 2"), plan.index("Final:"))
        self.assertIn("values=" + "a" * 40, plan)

    def test_cluster_orchestrator_uses_immutable_values_and_atomic_helm(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            resources = root / "clusters/prod/tools/traefik/resources"
            resources.mkdir(parents=True)
            (resources / "configmap.yaml").write_text(
                "apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: test\n",
                encoding="utf-8",
            )
            args = SimpleNamespace(
                artifact_repository_id="artifact-repository",
                chart_prefix="project/charts/cluster-tools",
                cluster="prod",
                commit="a" * 40,
                registry="fra.ocir.io",
                repo=root,
                tenancy_namespace="namespace",
            )
            target = {
                "actions": ["helm", "resources"],
                "chart": "traefik",
                "chart_version": "1.2.3",
                "depends_on": [],
                "namespace": "traefik",
                "tool": "traefik",
            }
            calls = []
            original = cluster_deploy.run
            cluster_deploy.run = lambda command, **kwargs: calls.append(command)
            try:
                cluster_deploy.deploy_tool(
                    args,
                    target,
                    root,
                )
            finally:
                cluster_deploy.run = original

            download, helm, resources_apply, status = calls
            self.assertIn("cluster-admin/prod/tools/traefik/values.yaml", download)
            self.assertIn("a" * 40, download)
            self.assertIn("oci://fra.ocir.io/namespace/project/charts/cluster-tools/traefik", helm)
            self.assertIn("--atomic", helm)
            self.assertIn("--version", helm)
            self.assertEqual(helm[helm.index("--version") + 1], "1.2.3")
            self.assertEqual(resources_apply[0:2], ["kubectl", "apply"])
            self.assertEqual(status[0:2], ["helm", "status"])

    def test_cluster_command_consumes_immutable_plan_and_applies_baseline_last(self):
        command_spec = (
            ROOT / "templates/cluster-admin-deploy-command-spec.yaml.tpl"
        ).read_text(encoding="utf-8")
        deploy_script = (
            ROOT / "repos/cluster-admin/script/deploy-cluster.py"
        ).read_text(encoding="utf-8")

        self.assertIn("cluster-admin/deployment-plan.json", command_spec)
        self.assertNotIn("--mode all", command_spec)
        self.assertNotIn("pip install", command_spec)
        self.assertNotIn("import yaml", deploy_script)
        self.assertLess(
            deploy_script.index("for number, wave in enumerate"),
            deploy_script.index('if any(target["kind"] == "baseline"'),
        )


if __name__ == "__main__":
    unittest.main()
