import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SPECS = (
    "repos/argocd/pipelines/mirror_argocd.yaml",
    "repos/fluxcd/pipelines/mirror_flux_operator.yaml",
)


class ChartVersionTests(unittest.TestCase):
    def specs(self):
        for path in SPECS:
            yield path, yaml.safe_load((ROOT / path).read_text())

    def resolve(self, spec, version, lookup_fails=False):
        command = next(step["command"] for step in spec["steps"] if step["name"].startswith("Resolve "))
        environment = os.environ.copy()
        environment.pop("chart_version", None)
        environment.pop("resolved_chart_version", None)
        if version is not None:
            environment["chart_version"] = version
        environment.update({key: str(value) for key, value in spec["env"]["variables"].items()})
        # OCI initializes same-named exported variables empty, masking run inputs.
        environment.update({key: "" for key in spec["env"]["exportedVariables"]})
        environment["MOCK_LOOKUP_FAILS"] = "1" if lookup_fails else "0"
        # Replace registry clients so running the actual Resolve command stays local.
        clients = """
set -euo pipefail
helm() {
    echo 'MOCK_HELM_CALL' >&2
    [ "$MOCK_LOOKUP_FAILS" = 0 ] || return 1
    if [ "$1" = show ]; then printf 'version: 99.1.2\\n'; fi
    return 0
}
docker() {
    echo 'MOCK_DOCKER_CALL' >&2
    [ "$MOCK_LOOKUP_FAILS" = 0 ] || return 1
    if [ "$1" = run ]; then printf '{"Tags":["v99.1.2"]}\\n'; fi
    return 0
}
"""
        return subprocess.run(
            # OCI captures exports after the step body; an early exit skips capture.
            ["bash", "-c", clients + command + '\nprintenv resolved_chart_version\n'],
            env=environment, text=True, capture_output=True, check=True, timeout=10,
        )

    def test_specs_keep_input_and_export_names_distinct(self):
        for path, spec in self.specs():
            with self.subTest(spec=path):
                self.assertNotIn("chart_version", spec["env"]["variables"])
                self.assertNotIn("chart_version", spec["env"]["exportedVariables"])
                self.assertEqual(spec["env"]["exportedVariables"].count("resolved_chart_version"), 1)

    def test_pinned_version_skips_latest_lookup_and_is_exported(self):
        for path, spec in self.specs():
            with self.subTest(spec=path):
                result = self.resolve(spec, "9.8.7")
                self.assertIn("Using requested chart_version=9.8.7", result.stdout)
                self.assertNotIn("Resolving LATEST", result.stdout)
                self.assertNotIn("MOCK_", result.stderr)
                self.assertEqual(result.stdout.splitlines()[-1], "9.8.7")

    def test_resolved_version_reaches_every_mirror_command(self):
        for path, spec in self.specs():
            for requested in ("9.8.7", "LATEST"):
                with self.subTest(spec=path, requested=requested), tempfile.TemporaryDirectory() as directory:
                    version = self.resolve(spec, requested).stdout.splitlines()[-1]
                    root = Path(directory)
                    scripts = root / "script"
                    scripts.mkdir()
                    # Exercise the real build-spec commands without writing to OCIR.
                    for name in ("mirror-helm.sh", "mirror-helm-image.sh", "mirror-flux.sh"):
                        script = scripts / name
                        script.write_text(
                            '#!/bin/bash\nset -eu\n'
                            'while getopts c:k:v:n:p:r:t: flag; do\n'
                            '  if [ "$flag" = v ]; then printf "%s\\n" "$OPTARG" >> versions; fi\n'
                            'done\n'
                        )
                        script.chmod(0o700)
                    environment = dict(os.environ, chart_version=requested, resolved_chart_version=version, region="test-region",
                                       repo_compartment_id="test", region_key="test", repo_prefix="test",
                                       chart_name="test", chart_repo="test", tenancy_namespace="test")
                    mirrors = [step for step in spec["steps"] if step["name"].startswith("Mirror ")]
                    self.assertTrue(mirrors)
                    for step in mirrors:
                        subprocess.run(["bash", "-eu", "-c", step["command"]], cwd=root,
                                       env=environment, check=True, capture_output=True, timeout=10)
                    expected = "v" + version if "fluxcd" in path else version
                    self.assertEqual((root / "versions").read_text().splitlines(), [expected] * len(mirrors))

    def test_unset_empty_and_latest_resolve_and_export(self):
        for path, spec in self.specs():
            for version in (None, "", "LATEST"):
                with self.subTest(spec=path, version=version):
                    result = self.resolve(spec, version)
                    self.assertIn("Resolving LATEST", result.stdout)
                    self.assertNotIn("Using requested", result.stdout)
                    self.assertEqual(result.stdout.splitlines()[-1], "99.1.2")

    def test_failed_latest_lookup_stops_resolution(self):
        for path, spec in self.specs():
            with self.subTest(spec=path):
                with self.assertRaises(subprocess.CalledProcessError):
                    self.resolve(spec, "LATEST", lookup_fails=True)

    def test_installer_and_chart_artifacts_use_resolved_export(self):
        artifacts = (ROOT / "modules/devops/artifact.tf").read_text()
        installer = (ROOT / "modules/devops/deployment.tf").read_text()
        pipelines = (ROOT / "modules/devops/build_pipeline.tf").read_text()
        self.assertEqual(artifacts.count('deploy_artifact_version     = "$${resolved_chart_version}"'), 2)
        self.assertNotIn('"$${chart_version}"', artifacts)
        self.assertIn('name          = "resolved_chart_version"', installer)
        self.assertIn('is_pass_all_parameters_enabled = true', pipelines)

    def test_both_pipeline_parameter_defaults_remain_latest(self):
        pipelines = (ROOT / "modules/devops/build_pipeline.tf").read_text()
        defaults = re.findall(r'name\s*=\s*"chart_version"\s+default_value\s*=\s*"([^"]+)"', pipelines)
        self.assertEqual(defaults, ["LATEST", "LATEST"])


if __name__ == "__main__":
    unittest.main()
