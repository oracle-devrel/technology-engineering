import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = (ROOT / "release-files.txt").read_text().splitlines()
        for name in self.manifest:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, target)

    def package(self, mode="false"):
        return subprocess.run(
            ["bash", "update.sh"], cwd=self.root, capture_output=True, text=True,
            env={**os.environ, "STACK_DEVELOPMENT_MODE": mode,
                 "STACK_ZIP_PATH": "result.zip"},
        )

    def test_release_contains_only_manifest_and_fresh_checksum(self):
        for name in (".env", "secret.tfvars.json", "terraform.tfstate",
                     "AGENT.md", "script/custom-deploy.sh", "templates/private.env",
                     "repos/application-source/.env", "repos/pipelines/script/local.sh"):
            (self.root / name).write_text("not for distribution")
        result = self.package()
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.root / "result.zip") as archive:
            files = {name for name in archive.namelist() if not name.endswith("/")}
            self.assertEqual(files, set(self.manifest))
            self.assertIn(b"ignore_changes = all", archive.read("modules/devops/cluster_admin_deploy_pipelines.tf"))
        checksum = hashlib.sha256((self.root / "result.zip").read_bytes()).hexdigest()
        self.assertEqual((self.root / "result.zip.sha256").read_text(),
                         f"{checksum}  result.zip\n")

    def test_development_mode_only_changes_staged_configuration(self):
        original = (self.root / "modules/devops/cluster_admin_deploy_pipelines.tf").read_bytes()
        result = self.package("true")
        self.assertEqual(result.returncode, 0, result.stderr)
        with zipfile.ZipFile(self.root / "result.zip") as archive:
            self.assertEqual(archive.read("development.auto.tfvars"), b"development_mode = true\n")
            self.assertNotIn(b"ignore_changes = all", archive.read("modules/devops/cluster_admin_deploy_pipelines.tf"))
        self.assertEqual((self.root / "modules/devops/cluster_admin_deploy_pipelines.tf").read_bytes(), original)

    def test_missing_input_fails(self):
        (self.root / "schema.yaml").unlink()
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing release file: schema.yaml", result.stderr)

    def test_symlink_input_fails(self):
        (self.root / "schema.yaml").unlink()
        (self.root / "schema.yaml").symlink_to(ROOT / "schema.yaml")
        result = self.package()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("must not contain symlinks", result.stderr)

    def test_invalid_mode_fails(self):
        self.assertNotEqual(self.package("invalid").returncode, 0)


if __name__ == "__main__":
    unittest.main()
