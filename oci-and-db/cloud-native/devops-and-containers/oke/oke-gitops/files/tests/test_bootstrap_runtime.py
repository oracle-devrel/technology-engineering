import os
from pathlib import Path
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BootstrapRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.template = (ROOT / "templates/gitops-bootstrap-prepare.yaml.tpl").read_text()

    def normalize(self, apps, fleet):
        start = self.template.index('      if [ "$${gitops_applications_enabled}"')
        end = self.template.index('      cluster_repo_prefix=', start)
        script = self.template[start:end].replace("$${", "${")
        script += '\nprintf "%s|%s" "$apps_config_repo_url" "$fleet_config_repo_url"\n'
        env = dict(os.environ, gitops_applications_enabled=str(apps).lower(),
                   gitops_fleet_enabled=str(fleet).lower(),
                   apps_config_repo_url="apps-url", fleet_config_repo_url="fleet-url")
        return subprocess.check_output(["bash", "-eu", "-c", script], env=env, text=True)

    def test_disabled_optional_sources_are_cleared(self):
        self.assertEqual(self.normalize(False, False), "|")
        self.assertEqual(self.normalize(True, False), "apps-url|")
        self.assertEqual(self.normalize(False, True), "|fleet-url")

    def test_enabled_sources_are_preserved(self):
        self.assertEqual(self.normalize(True, True), "apps-url|fleet-url")

    def test_credentials_stay_outside_workspace_snapshots(self):
        self.assertIn("mktemp -d /tmp/gitops-credentials.XXXXXX", self.template)
        self.assertNotIn('OCI_WORKSPACE_DIR}/gitops-credentials', self.template)
        self.assertIn("trap 'rm -rf --", self.template)


if __name__ == "__main__":
    unittest.main()
