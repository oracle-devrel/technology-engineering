import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]


def script(filename):
    spec = importlib.util.spec_from_file_location(filename, ROOT / "repos/cluster-admin/script" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


images = script("mirror-images.py")
dispatch = script("publish-and-dispatch.py")
validation = script("validate-config.py")


class ImageReferenceTests(unittest.TestCase):
    def test_short_names_digest_and_registry_port(self):
        self.assertEqual(images.image_reference("busybox:1.36")["reference"], "docker.io/library/busybox:1.36")
        self.assertEqual(images.image_reference("team/api")["reference"], "docker.io/team/api:latest")
        self.assertEqual(images.image_reference("index.docker.io/team/api:v1")["registry"], "docker.io")
        self.assertEqual(images.image_reference("registry.example:5000/team/api:v1")["root"], "registry.example:5000/team/api")
        digest = "sha256:" + "a" * 64
        self.assertEqual(images.image_reference("ghcr.io/team/api:v1@" + digest)["reference"], "ghcr.io/team/api@" + digest)

    def test_invalid_references_are_rejected(self):
        for value in ("", "--help", "https://ghcr.io/team/api:v1", "user:pass@registry.test/app", "image with spaces", "app@sha256:123", "registry.test:99999/app", "../app", 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                images.image_reference(value)

    def test_standard_pod_specs_hooks_and_lists(self):
        pod = {"containers": [{"image": "app:v1"}], "initContainers": [{"image": "init:v1"}]}
        documents = [
            {"kind": "Deployment", "spec": {"template": {"spec": pod}}},
            {"kind": "Job", "metadata": {"annotations": {"helm.sh/hook": "pre-install"}}, "spec": {"template": {"spec": pod}}},
            {"kind": "CronJob", "spec": {"jobTemplate": {"spec": {"template": {"spec": pod}}}}},
            {"kind": "Pod", "spec": pod},
        ]
        self.assertEqual(images.pod_images({"kind": "List", "items": documents}), {"app:v1", "init:v1"})
        self.assertEqual(images.pod_images({"kind": "ConfigMap", "data": {"image": "not-an-image"}}), set())


class RegistryCopyTests(unittest.TestCase):
    def client(self):
        client = images.RegistryMirror.__new__(images.RegistryMirror)
        client.registry = "ams.ocir.io"
        client.namespace = "namespace"
        client.prefix = "project/images/cluster-tools"
        client.copies = {}
        client.repositories = set()
        client.compartment = "test-compartment"
        return client

    def test_multiplatform_copy_uses_digest_and_preserves_index(self):
        client = self.client()
        raw = json.dumps({"schemaVersion": 2, "mediaType": "application/vnd.oci.image.index.v1+json", "manifests": [
            {"platform": {"os": "linux", "architecture": "amd64"}},
            {"platform": {"os": "linux", "architecture": "arm64"}},
        ]}).encode()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        calls, repositories = [], []
        def skopeo(command):
            calls.append(command)
            if command[0] == "inspect" and "ams.ocir.io" in command[-1] and len([c for c in calls if c[0] == "copy"]) == 0:
                raise subprocess.CalledProcessError(1, command)
            return raw
        client.skopeo = skopeo
        client.ensure_repository = repositories.append
        result = client.mirror("ghcr.io/team/api:v1")
        copied = next(command for command in calls if command[0] == "copy")
        self.assertIn("--all", copied)
        self.assertIn("--preserve-digests", copied)
        self.assertIn("docker://ghcr.io/team/api@" + digest, copied)
        self.assertEqual(result["source_digest"], result["destination_digest"])
        self.assertTrue(result["destination"].endswith(":sha256-" + digest.split(":")[1]))
        self.assertEqual(repositories, ["project/images/cluster-tools/ghcr.io/team/api"])
        client.mirror("ghcr.io/team/api:v1")
        self.assertEqual(len([c for c in calls if c[0] == "copy"]), 1)

    def test_existing_image_is_not_copied(self):
        client = self.client()
        client.digest = lambda reference: "sha256:" + "a" * 64
        client.ensure_repository = lambda path: None
        client.skopeo = lambda command: self.fail("Existing image was copied")
        self.assertEqual(client.mirror("ghcr.io/team/api:v1")["status"], "exists")

    def test_target_ocir_images_are_not_mirrored_recursively(self):
        client = self.client()
        client.digest = lambda reference: "sha256:" + "a" * 64
        client.ensure_repository = lambda path: self.fail("Unexpected target repository")
        result = client.mirror("ams.ocir.io/namespace/project/images/cluster-tools/ghcr.io/team/api:v1")
        self.assertEqual(result["status"], "already-in-target-ocir")

    def test_digest_mismatch_stops_build(self):
        client = self.client()
        source, destination = "sha256:" + "a" * 64, "sha256:" + "b" * 64
        results = iter((source, destination, destination))
        client.digest = lambda ref: next(results)
        client.ensure_repository = lambda path: None
        client.skopeo = lambda command: b""
        with self.assertRaisesRegex(ValueError, "Destination digest"):
            client.mirror("ghcr.io/team/api:v1")

    def test_authentication_uses_private_file_and_stdin(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(images.RegistryMirror, "oci", return_value={"data": {"token": "secret-token"}}), patch.object(images.subprocess, "run") as run, patch.dict(os.environ, {}, clear=True):
                client = images.RegistryMirror("ams.ocir.io", "namespace", "project/images", "compartment", Path(directory))
                self.assertEqual(client.auth_file.stat().st_mode & 0o777, 0o600)
                self.assertNotIn("secret-token", str(run.call_args.args))
                self.assertEqual(run.call_args.kwargs["input"], "secret-token")


class DiscoveryIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        self.repo.mkdir()
        self.write("catalog/tools.yaml", yaml.safe_dump({"tools": {"metrics": {"chart": "metrics", "version": "1.0.0", "repository": "https://charts.example.test", "mirror_images": True, "additional_images": ["ghcr.io/team/operator:v1"]}}}))
        for cluster, enabled in (("noprod", False), ("prod", True)):
            self.write(f"clusters/{cluster}/tools/metrics/values.yaml", yaml.safe_dump({"extra": enabled}))
        self.git("init", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        self.commit = self.git("rev-parse", "HEAD")
        self.selection = {"commit": self.commit, "targets": [{"kind": "tool", "cluster": cluster, "tool": "metrics", "namespace": "metrics", "chart": "metrics", "chart_version": "1.0.0", "actions": ["helm"]} for cluster in ("noprod", "prod")]}

    def write(self, path, data):
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args], text=True).strip()

    def prepare(self):
        return images.prepare_images(self.repo, self.selection, "ams.ocir.io", "namespace", "project/images", "project/charts", "compartment", Path(self.temp.name) / "reports")

    def test_disabled_requires_no_registry_or_helm_access(self):
        catalog = yaml.safe_load(images.snapshot(self.repo, self.commit, "catalog/tools.yaml"))
        catalog["tools"]["metrics"]["mirror_images"] = False
        with patch.object(images, "snapshot", return_value=yaml.safe_dump(catalog).encode()), patch.object(images, "RegistryMirror", side_effect=AssertionError("Registry accessed")):
            self.assertEqual(self.prepare(), [])

    @unittest.skipUnless(shutil.which("helm"), "Helm is required for actual chart rendering")
    def test_actual_helm_per_target_values_hooks_and_exact_commit(self):
        chart = Path(self.temp.name) / "chart"
        (chart / "templates").mkdir(parents=True)
        (chart / "Chart.yaml").write_text("apiVersion: v2\nname: metrics\nversion: 1.0.0\n")
        (chart / "templates/deployment.yaml").write_text('''apiVersion: apps/v1
kind: Deployment
metadata:
  name: metrics
spec:
  template:
    spec:
      initContainers:
        - name: init
          image: busybox:1.36
      containers:
        - name: main
          image: ghcr.io/team/main:v1
{{- if .Values.extra }}
        - name: extra
          image: ghcr.io/team/extra:v2
{{- end }}
---
apiVersion: batch/v1
kind: Job
metadata:
  name: hook
  annotations:
    helm.sh/hook: pre-install,pre-upgrade
spec:
  template:
    spec:
      containers:
        - name: hook
          image: ghcr.io/team/{{ if .Release.IsUpgrade }}upgrade{{ else }}install{{ end }}:v1
''')
        self.write("clusters/noprod/tools/metrics/values.yaml", "extra: true\n")
        actual_output = subprocess.check_output
        copied = set()
        rendered_commands = []
        class FakeMirror:
            helm_env = dict(os.environ)
            def __init__(self, *args):
                pass
            def mirror(self, image):
                copied.add(image)
                return {"source": image, "destination": "ocir/" + image}
        def command(argv, **kwargs):
            if argv[:2] == ["helm", "template"]:
                rendered_commands.append(argv)
                argv = list(argv)
                argv[3] = str(chart)
            return actual_output(argv, **kwargs)
        with patch.object(images, "RegistryMirror", FakeMirror), patch.object(images.subprocess, "check_output", side_effect=command):
            index = self.prepare()
        reports = {item["cluster"]: json.loads(Path(item["path"]).read_text()) for item in index}
        source_images = lambda cluster: {item["source"] for item in reports[cluster]["images"]}
        self.assertNotIn("ghcr.io/team/extra:v2", source_images("noprod"))
        self.assertIn("ghcr.io/team/extra:v2", source_images("prod"))
        for cluster in ("noprod", "prod"):
            self.assertTrue({"busybox:1.36", "ghcr.io/team/operator:v1", "ghcr.io/team/install:v1", "ghcr.io/team/upgrade:v1"}.issubset(source_images(cluster)))
            self.assertEqual(reports[cluster]["commit"], self.commit)
        self.assertEqual(len(rendered_commands), 4)
        self.assertIn("ghcr.io/team/extra:v2", copied)

    def test_values_only_and_catalog_changes_select_helm(self):
        for cluster in ("noprod", "prod"):
            self.write(f"clusters/{cluster}/baseline/README.md", "baseline\n")
            self.write(f"clusters/{cluster}/tools/metrics/tool.yaml", "name: metrics\nnamespace: metrics\ndepends_on: []\n")
        self.git("add", ".")
        self.git("commit", "-m", "metadata")
        self.write("clusters/prod/tools/metrics/values.yaml", "extra: false\n")
        self.git("add", ".")
        self.git("commit", "-m", "values only")
        selection = validation.validate(self.repo, self.git("rev-parse", "HEAD"), "changed")
        self.assertEqual([(t["cluster"], t["actions"]) for t in selection["targets"]], [("prod", ["helm"])])
        catalog = yaml.safe_load((self.repo / "catalog/tools.yaml").read_text())
        catalog["tools"]["metrics"]["additional_images"].append("ghcr.io/team/new:v1")
        self.write("catalog/tools.yaml", yaml.safe_dump(catalog))
        self.git("add", ".")
        self.git("commit", "-m", "additional images")
        selection = validation.validate(self.repo, self.git("rev-parse", "HEAD"), "changed")
        self.assertEqual({t["cluster"] for t in selection["targets"]}, {"noprod", "prod"})
        self.assertTrue(all(t["actions"] == ["helm"] for t in selection["targets"]))


class WiringTests(unittest.TestCase):
    def test_chart_mirror_build_is_pinned_to_selected_commit(self):
        with patch.object(dispatch, "oci", return_value={"data": {"lifecycle-state": "SUCCEEDED"}}) as oci:
            dispatch.ensure_mirrors("pipeline", "a" * 40, "https://example.test/repo")
        args = oci.call_args.args[0]
        self.assertEqual(json.loads(args[args.index("--commit-info") + 1])["commitHash"], "a" * 40)
        self.assertEqual(json.loads(args[args.index("--build-run-arguments") + 1])["items"][0]["value"], "a" * 40)

    def test_reports_are_immutable_per_target_artifacts(self):
        args = SimpleNamespace(targets="targets.json", registry="ams.ocir.io", tenancy_namespace="ns", image_prefix="project/images", chart_prefix="project/charts", compartment_id="compartment", artifact_repository_id="artifacts")
        def run(argv, **kwargs):
            directory = Path(argv[argv.index("--output-dir") + 1])
            report = directory / "images.json"
            report.write_text("{}")
            (directory / "index.json").write_text(json.dumps([{"cluster": "prod", "tool": "metrics", "path": str(report)}]))
        with patch.object(dispatch.subprocess, "run", side_effect=run), patch.object(dispatch, "upload_artifact") as upload:
            dispatch.mirror_selected_images(args, Path("repo"), {"commit": "a" * 40})
        self.assertEqual(upload.call_args.args[2:4], ("cluster-admin/prod/tools/metrics/images.json", "a" * 40))

    def test_published_values_use_the_selected_commit(self):
        args = SimpleNamespace(artifact_repository_id="artifacts", compartment_id="compartment")
        content = b"feature:\n  enabled: true\n"
        def upload(repository, compartment, path, commit, source, label):
            self.assertEqual(source.read_bytes(), content)
            self.assertEqual((path, commit), ("cluster-admin/prod/tools/metrics/values.yaml", "a" * 40))
        with patch.object(dispatch.subprocess, "check_output", return_value=content) as git, patch.object(dispatch, "upload_artifact", side_effect=upload):
            dispatch.publish_values(args, Path("repo"), {"cluster": "prod", "tool": "metrics"}, "a" * 40)
        self.assertEqual(git.call_args.args[0][-1], "a" * 40 + ":clusters/prod/tools/metrics/values.yaml")

    def test_disabled_default_and_catalog_sync(self):
        schema = yaml.safe_load((ROOT / "schema.yaml").read_text())
        self.assertFalse(schema["variables"]["tool_mirror_images"]["default"])
        self.assertEqual(schema["variables"]["tool_additional_images"]["type"], "list")
        source = (ROOT / "modules/devops/cluster_admin_repositories.tf").read_text()
        self.assertIn('catalog_hash = sha256(local_file.cluster_admin_catalog[each.key].content)', source)
        catalog = (ROOT / "templates/cluster-admin-tools.yaml.tpl").read_text()
        self.assertIn("tool.mirror_images", catalog)
        self.assertIn("tool.additional_images", catalog)
        self.assertIn("repos/cluster-admin/script/mirror-images.py", (ROOT / "release-files.txt").read_text())
        deploy = (ROOT / "repos/cluster-admin/script/deploy-cluster.py").read_text()
        self.assertNotIn("mirror-images", deploy)


if __name__ == "__main__":
    unittest.main()
