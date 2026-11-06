import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile


SCRIPT = Path(__file__).resolve().parents[1] / "package-agent-skills.py"
SPEC = importlib.util.spec_from_file_location("package_agent_skills", SCRIPT)
packaging = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packaging)


class SkillPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = Path("skills/example")
        self.skill = self.root / self.source
        self.skill.mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.skill / "SKILL.md").write_text("---\nname: example\n---\n")
        (self.skill / "references").mkdir()
        (self.skill / "references/guide.md").write_text("Skill reference\n")
        (self.skill / "scripts").mkdir()
        script = self.skill / "scripts/run.sh"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o755)
        self.git("add", ".")
        self.output = self.root / "output"

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def package(self):
        return packaging.package_skill(self.root, self.source, self.output)

    def test_portable_root_contents_and_executable_mode(self):
        with zipfile.ZipFile(self.package()) as archive:
            self.assertEqual(set(archive.namelist()), {
                "example/SKILL.md", "example/references/guide.md", "example/scripts/run.sh",
            })
            self.assertEqual(archive.read("example/references/guide.md"), b"Skill reference\n")
            self.assertEqual(archive.getinfo("example/scripts/run.sh").external_attr >> 16, 0o100755)

    def test_untracked_files_are_never_distributed(self):
        (self.skill / ".env").write_text("private")
        (self.skill / ".DS_Store").write_text("local")
        with zipfile.ZipFile(self.package()) as archive:
            self.assertEqual(len(archive.namelist()), 3)

    def test_archive_is_reproducible(self):
        first = self.package().read_bytes()
        self.assertEqual(first, self.package().read_bytes())

    def test_missing_skill_fails(self):
        self.git("rm", "-f", "skills/example/SKILL.md")
        with self.assertRaisesRegex(ValueError, "Missing tracked SKILL.md"):
            self.package()

    def test_tracked_symlink_fails(self):
        (self.skill / "link").symlink_to("SKILL.md")
        self.git("add", ".")
        with self.assertRaisesRegex(ValueError, "regular"):
            self.package()

    def test_worktree_symlink_fails(self):
        path = self.skill / "references/guide.md"
        path.unlink()
        path.symlink_to("../SKILL.md")
        with self.assertRaisesRegex(ValueError, "symlinks"):
            self.package()

    def test_release_selection(self):
        self.assertEqual(packaging.asset_for_tag("oci-devops-rm-1.3.0"), "devops")
        self.assertEqual(packaging.asset_for_tag("oke-gitops-2.2.0"), "gitops")
        self.assertEqual(len(packaging.SKILLS["devops"]), 1)
        self.assertEqual(len(packaging.SKILLS["gitops"]), 2)
        for tag in ("oke-rm-1.5.1", "other", "oke-gitops-"):
            with self.assertRaises(ValueError):
                packaging.asset_for_tag(tag)


if __name__ == "__main__":
    unittest.main()
