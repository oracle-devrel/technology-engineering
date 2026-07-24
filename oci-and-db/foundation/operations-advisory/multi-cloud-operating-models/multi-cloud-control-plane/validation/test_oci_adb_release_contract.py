import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CATALOG = (
    ROOT
    / "components"
    / "gitops-templates"
    / "resources-catalog"
    / "oci"
    / "databases"
    / "project_database_template.auto.tfvars.json"
)
VALIDATOR = (
    ROOT
    / "plugins"
    / "project-gitops"
    / "skills"
    / "project-gitops"
    / "scripts"
    / "validate-change.py"
)

spec = importlib.util.spec_from_file_location("validate_change", VALIDATOR)
validate_change = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = validate_change
spec.loader.exec_module(validate_change)


class OciAdbReleaseContractTests(unittest.TestCase):
    @staticmethod
    def _run_git(repository: Path, *arguments: str) -> None:
        subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _create_project_repository(self, root: Path) -> Path:
        repository = root / "nonprod-project1"
        repository.mkdir()
        self._run_git(repository, "init", "--initial-branch=main")
        self._run_git(repository, "config", "user.name", "Contract Test")
        self._run_git(repository, "config", "user.email", "contract@example.invalid")
        self._run_git(
            repository,
            "remote",
            "add",
            "origin",
            "https://github.com/__CUSTOMER_ORG__/nonprod-project1.git",
        )

        handoff = repository / "environments/dev/environment_information.md"
        handoff.parent.mkdir(parents=True)
        handoff.write_text(
            """# Project Environment Information

| Reference | Value |
|---|---|
| Project | project1 |
| Environment | dev |
| OCI region | eu-frankfurt-1 |

| Role | Logical key | OCID |
|---|---|---|
| App compartment | CMP-PROJECT1 | ocid1.compartment.oc1..project1 |
| DB compartment | CMP-PROJECT1 | ocid1.compartment.oc1..project1 |
| Infra compartment | CMP-PROJECT1 | ocid1.compartment.oc1..project1 |

| Role | Logical key | Name | CIDR | OCID |
|---|---|---|---|---|
| Projects VCN | VCN-PROJECT1 | vcn-project1 | 10.0.0.0/16 | ocid1.vcn.oc1.eu-frankfurt-1.project1 |
| Web subnet | WEB-PROJECT1 | web-project1 | 10.0.0.0/24 | ocid1.subnet.oc1.eu-frankfurt-1.web |
| App subnet | APP-PROJECT1 | app-project1 | 10.0.1.0/24 | ocid1.subnet.oc1.eu-frankfurt-1.app |
| DB subnet | DB-PROJECT1 | db-project1 | 10.0.2.0/24 | ocid1.subnet.oc1.eu-frankfurt-1.db |
| Infra subnet | INFRA-PROJECT1 | infra-project1 | 10.0.3.0/24 | ocid1.subnet.oc1.eu-frankfurt-1.infra |
""",
            encoding="utf-8",
        )
        database = repository / "oci/dev/eu-frankfurt-1/database/database.json"
        database.parent.mkdir(parents=True)
        database.write_text(
            json.dumps(
                {
                    "autonomous_databases_configuration": {
                        "databases": {
                            "ADB-PROJECT1": {
                                "display_name": "adb-dev-project1"
                            }
                        }
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self._run_git(repository, "add", ".")
        self._run_git(repository, "commit", "-m", "Initialize project")
        return repository

    def test_catalog_and_project_validator_use_release_1_2_0_adb_shape(self):
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        configuration = catalog["autonomous_databases_configuration"]
        self.assertEqual(set(configuration), {"default_compartment_id", "databases"})
        entry = configuration["databases"]["__ADB_KEY__"]
        self.assertFalse(entry["is_dedicated"])
        self.assertTrue(entry["networking"]["enable_private_endpoint"])
        self.assertEqual(
            entry["networking"]["network_security_groups"], ["__NSG_DB_KEY__"]
        )
        self.assertNotIn("autonomous_databases", configuration)

        rendered = json.loads(json.dumps(entry))
        rendered.update(
            {
                "db_name": "PROJ1ADB",
                "display_name": "adb-dev-project1",
                "admin_password": "__DEV_ADB_PROJ1_ADMIN_PASSWORD__",
            }
        )
        rendered["networking"]["subnet_id"] = (
            "ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase"
        )
        rendered["networking"]["network_security_groups"] = ["NSG-DB-PROJECT1"]
        validate_change.validate_adb_declaration(
            "ADB-PROJ1-KEY",
            rendered,
            project="nonprod-project1",
            environment="dev",
            region="eu-frankfurt-1",
        )

    def test_first_lifecycle_request_may_add_canonical_manifest(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary_directory:
            repository = self._create_project_repository(
                Path(temporary_directory)
            )
            self._run_git(
                repository,
                "switch",
                "--create",
                "agent/adb-stop-adb-dev-project1",
            )
            lifecycle = (
                repository
                / "oci/dev/eu-frankfurt-1/lifecycle_operations/adb-lifecycle.json"
            )
            lifecycle.parent.mkdir(parents=True)
            lifecycle.write_text(
                json.dumps(
                    {
                        "operation_type": "adb-lifecycle",
                        "targets": [
                            {
                                "display_name": "adb-dev-project1",
                                "action": "stop",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

            change = validate_change.collect_change(repository, "main")
            self.assertEqual(change.path, lifecycle.relative_to(repository).as_posix())
            self.assertEqual(change.base_content, b"")
            finalized = validate_change._finalize_change(change)
            self.assertIn('"action": "stop"', finalized.diff)

    def test_new_day_one_aggregate_remains_rejected(self):
        with tempfile.TemporaryDirectory(dir="/private/tmp") as temporary_directory:
            repository = self._create_project_repository(
                Path(temporary_directory)
            )
            self._run_git(
                repository,
                "switch",
                "--create",
                "agent/vm-create-vm-dev-project1",
            )
            compute = repository / "oci/dev/eu-frankfurt-1/compute/compute.json"
            compute.parent.mkdir(parents=True)
            compute.write_text(
                '{"instances_configuration":{"instances":{}}}\n',
                encoding="utf-8",
            )

            with self.assertRaises(validate_change.ValidationFailure) as context:
                validate_change.collect_change(repository, "main")
            self.assertEqual(context.exception.code, "INVALID_CHANGE")


if __name__ == "__main__":
    unittest.main()
