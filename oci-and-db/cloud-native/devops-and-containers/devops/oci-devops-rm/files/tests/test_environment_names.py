import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def render_command_template(name, **values):
    source = (ROOT / "templates" / name).read_text()
    source = re.sub(r"(?<!\$)\$\{([a-z_]+)\}", lambda match: values[match[1]], source)
    return yaml.safe_load(source.replace("$${", "${"))


class EnvironmentNameTests(unittest.TestCase):
    def test_schema_outputs_resolve_to_terraform_outputs(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text())
        output_names = set()
        for source in ROOT.glob("*.tf"):
            output_names.update(re.findall(r'output "([^"]+)"', source.read_text()))
        self.assertTrue(set(schema["outputs"]).issubset(output_names))
        for group in schema["outputGroups"]:
            for reference in group["outputs"]:
                self.assertIn(reference.removeprefix("${").removesuffix("}"), schema["outputs"])

    def test_schema_names_have_safe_defaults_and_visibility(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text())
        self.assertNotIn("environment_names", schema["variables"])
        self.assertEqual(schema["outputs"]["environment_names"]["type"], "map")
        defaults = {
            "dev_environment_name": "dev", "staging_environment_name": "staging",
            "prod_environment_name": "prod", "noprod_cluster_name": "noprod",
            "prod_cluster_name": "prod",
        }
        for name, default in defaults.items():
            field = schema["variables"][name]
            self.assertEqual(field["default"], default)
            self.assertTrue(field["required"])
            for invalid in ("", "../live", "Production", "production/blue", "-live"):
                self.assertIsNone(re.fullmatch(field["pattern"], invalid))
        group = next(group for group in schema["variableGroups"] if group["title"] == "Application Environment Names")
        self.assertEqual(group["visible"], {"eq": ["${application_delivery_mode}", "oci_devops"]})
        self.assertIn("environment-names.tf", (ROOT / "release-files.txt").read_text().splitlines())

    def test_graphical_tools_input_is_an_optional_native_list(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text())
        field = schema["variables"]["cluster_administration"]
        self.assertEqual(field["type"], "list")
        self.assertIsInstance(json.loads(field["default"]), list)
        self.assertFalse(field["required"])

    def test_bootstrap_resolves_renamed_clusters(self):
        template = render_command_template(
            "application-bootstrap-command-spec.yaml.tpl",
            kube_endpoint="PRIVATE_ENDPOINT", noprod_oke_cluster_id="cluster-test",
            prod_oke_cluster_id="cluster-live", region="eu-milan-1", region_key="mil",
            noprod_cluster_name="sandbox", prod_cluster_name="production",
        )
        command = template["steps"][0]["command"]
        for name, expected in (("sandbox", "cluster-test"), ("production", "cluster-live"), ("prod", None)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                stage = {"data": {"freeform-tags": {"application": "shop", "cluster": name, "namespace": "shop"}}}
                env = {**os.environ, "OCI_STAGE_ID": "test-stage", "OCI_WORKSPACE_DIR": directory,
                       "STAGE_JSON": json.dumps(stage), "noprod_cluster_id": "cluster-test", "prod_cluster_id": "cluster-live"}
                result = subprocess.run(["bash", "-c", 'oci() { printf "%s" "$STAGE_JSON"; };\n' + command], env=env, capture_output=True, text=True)
                if expected:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"target_cluster_id={expected}", (Path(directory) / "bootstrap-context.env").read_text())
                else:
                    self.assertNotEqual(result.returncode, 0)

    def test_custom_deployment_commands_have_valid_shell_syntax(self):
        values = {
            "artifact_repository_id": "artifact", "chart_prefix": "charts", "kube_endpoint": "PRIVATE_ENDPOINT",
            "noprod_oke_cluster_id": "cluster-test", "prod_oke_cluster_id": "cluster-live",
            "region": "eu-milan-1", "registry": "mil.ocir.io", "repository_id": "repo",
            "tenancy_namespace": "test", "noprod_cluster_name": "sandbox", "prod_cluster_name": "production",
        }
        for filename in ("cluster-admin-deploy-command-spec.yaml.tpl", "cluster-admin-decommission-command-spec.yaml.tpl"):
            spec = render_command_template(filename, **values)
            for step in spec["steps"]:
                result = subprocess.run(["bash", "-n"], input=step["command"], text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, f"{filename}: {result.stderr}")

    def test_decommission_resolves_custom_target_from_stage_tags(self):
        spec = render_command_template(
            "cluster-admin-decommission-command-spec.yaml.tpl", kube_endpoint="PRIVATE_ENDPOINT",
            noprod_oke_cluster_id="cluster-test", prod_oke_cluster_id="cluster-live",
            region="eu-milan-1", repository_id="repo", noprod_cluster_name="sandbox",
            prod_cluster_name="production",
        )
        for name, expected in (("sandbox", "cluster-test"), ("production", "cluster-live"), ("prod", None)):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                env = {**os.environ, "OCI_STAGE_ID": "test-stage", "OCI_WORKSPACE_DIR": directory,
                       "STAGE_JSON": json.dumps({"data": {"freeform-tags": {"cluster": name}}}),
                       "namespace": "metrics", "tool_name": "metrics",
                       "noprod_cluster_id": "cluster-test", "prod_cluster_id": "cluster-live"}
                mock = 'oci() { [[ "$*" == "devops deploy-stage get --stage-id test-stage" ]] || return 2; printf "%s" "$STAGE_JSON"; };\n'
                result = subprocess.run(["bash", "-c", mock + spec["steps"][0]["command"]], env=env, capture_output=True, text=True)
                if expected:
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"cluster_id={expected}", (Path(directory) / "decommission-context.env").read_text())
                else:
                    self.assertNotEqual(result.returncode, 0)


@unittest.skipUnless(shutil.which("helm"), "Helm is required for rendered chart checks")
class EnvironmentChartTests(unittest.TestCase):
    def test_sample_templates_match_generated_templates(self):
        for name in ("deployment", "service", "serviceaccount"):
            source = (ROOT / f"templates/component-chart-{name}.yaml.tpl").read_text()
            sample = (ROOT / f"repos/application-chart/sample-app/charts/sample-component/templates/{name}.yaml").read_text()
            self.assertEqual(source, sample)

    def render(self, name, role):
        chart = ROOT / "repos/application-chart/sample-app/charts/sample-component"
        result = subprocess.run([
            "helm", "template", "test-release", str(chart),
            "--set-string", f"environment={name}", "--set-string", f"environmentRole={role}",
            "--set-string", "image.repository=example.test/shop/api", "--set-string", "image.tag=1.2.3-rc.4",
        ], capture_output=True, text=True, check=True)
        return {item["kind"]: item for item in yaml.safe_load_all(result.stdout) if item}

    def test_custom_production_name_keeps_final_image_and_unsuffixed_resources(self):
        objects = self.render("live", "prod")
        deployment = objects["Deployment"]
        self.assertEqual(deployment["metadata"]["name"], "sample-component")
        self.assertEqual(deployment["metadata"]["labels"]["env"], "live")
        self.assertEqual(deployment["spec"]["template"]["spec"]["containers"][0]["image"], "example.test/shop/api:1.2.3")
        self.assertEqual(objects["Service"]["spec"]["selector"], deployment["spec"]["selector"]["matchLabels"])

    def test_nonproduction_named_prod_does_not_gain_production_behavior(self):
        objects = self.render("prod", "dev")
        deployment = objects["Deployment"]
        self.assertEqual(deployment["metadata"]["name"], "sample-component-prod")
        self.assertEqual(deployment["spec"]["template"]["spec"]["containers"][0]["image"], "example.test/shop/api:1.2.3-rc.4")

    def test_staging_keeps_rc_and_custom_suffix(self):
        objects = self.render("uat", "staging")
        self.assertEqual(objects["Deployment"]["metadata"]["name"], "sample-component-uat")
        self.assertEqual(objects["ServiceAccount"]["metadata"]["name"], "sample-component-uat")

    def test_legacy_production_values_remain_compatible(self):
        objects = self.render("prod", "")
        deployment = objects["Deployment"]
        self.assertEqual(deployment["metadata"]["name"], "sample-component")
        self.assertEqual(deployment["spec"]["template"]["spec"]["containers"][0]["image"], "example.test/shop/api:1.2.3")


if __name__ == "__main__":
    unittest.main()
