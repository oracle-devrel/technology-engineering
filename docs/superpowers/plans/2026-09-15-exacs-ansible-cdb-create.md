# ExaCS Ansible CDB Creation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Certify, in isolated ExaCS integration branches, an MVP governed ExaCS operation: create one CDB in one existing DB Home, resolved from a Terraform-managed VM Cluster and operated through OCI Ansible Collection 5.5.0. Promote it to the certified MCCP sources only after the full certification gate succeeds.

**Architecture:** Terraform, using `oci-landing-zones/terraform-oci-modules-orchestrator@release-2.1.4`, owns the Exadata infrastructure and VM Cluster. The Ansible operation reads that project-region Terraform state once to resolve the requested VM Cluster by display name, resolves the DB Home and CDBs through OCI APIs, and writes only a temporary inventory. Project manifests use resource names and runtime-secret tokens; OCIDs are resolved inside Platform CI and appear only in protected execution evidence. Development runs in a dedicated Platform CI feature branch and a paired `nonprod-exacs-project01` feature branch; neither certified `main` nor generic project templates consume it before publication.

**Tech Stack:** GitHub Actions reusable workflows, Python 3.11 standard library, Ansible 9.0.1, `oracle.oci` 5.5.0, OCI Instance Principal, OCI Object Storage Terraform state, JSON manifests, `unittest`.

## Global Constraints

- OCI Terraform calls use `oci-landing-zones/terraform-oci-modules-orchestrator` at `release-2.1.4`; record its resolved revision `02560b0556129a44ae4b1376638cd0cb1f39e794` in certification evidence.
- The legacy `feature/exacs-workshop-playbooks` branch is a research input only: it contains the useful demo tasks but also the historical workarounds and drift that this plan removes. Do not extend or certify it as the product branch.
- Create a fresh special Platform CI branch, for example `feature/exacs-cdb-create`, from the current certified Platform CI `main`. Create the paired `feature/exacs-cdb-create` branch in `multicloud-control-plane/nonprod-exacs-project01` and pin only that project branch to the Platform CI feature commit SHA.
- The paired ExaCS repository is the sole cloud-certification consumer during development. Do not change Platform CI `main`, the certified generic project templates, the public catalog, or a production project reference until the publication gate in Task 7 has been accepted.
- The Platform CI feature branch must be pinned by immutable commit SHA in the ExaCS project workflow for each certification run; a mutable branch name is permitted only while preparing the project pull request, never as its executed dependency reference.
- `platform-ci@main` already provides the reusable `terraform-shared.yaml` and `ansible-shared.yaml` entrypoints. The legacy ExaCS project instead calls the obsolete workshop-only `*-project.yaml` workflows. The MVP migrates only the paired ExaCS feature branch to the shared entrypoints and an immutable Platform CI SHA; it does not copy the workshop deploy-key, PAR, API-key, proxy or patch/move machinery.
- Terraform owns only Exadata infrastructure and VM Clusters. Ansible owns DB Homes, CDBs, and PDBs; Terraform manifests must reject non-empty `cloud_db_homes_configuration`, `databases_configuration`, and `pluggable_databases_configuration` in `cloud_exadata_database_configuration`.
- The initial release accepts only VM Clusters allocated exclusively to one MCCP project repository. A shared VM Cluster needs a separately certified cross-repository lease service before it can be enabled.
- Project manifests never contain OCI IDs, private keys, state paths, PAR URLs, deploy keys, or secret values.
- A VM Cluster is identified by `display_name`; a DB Home by `display_name`; a CDB by `db_name` and `db_unique_name`; and a PDB by `pdb_name` within its CDB. The resolver rejects zero or multiple matching resources.
- Each MVP `exacs-cdb-create` request selects one OCI environment/region tuple, one VM Cluster, one DB Home, and exactly one CDB target.
- The target has one environment-qualified password token. Secrets resolve only into a JSON copy under the runner temporary directory, are masked before use, and never modify Git content or workflow output.
- PR mode performs reads, validation, and semantic reporting only. OCI creation occurs only in execute mode after merge.
- The runner uses Instance Principal. Its policy must read the selected state object and manage Database resources only in the handed-off project compartment and VM Cluster.
- The existing project-level GitHub Actions concurrency remains the release-one lock because the handoff requires exclusive VM Cluster allocation. Do not claim it serializes different repositories.
- This is an MVP: do not add generic reconciliation, bulk batching, custom retry orchestration, external locking, UI/plugin work, or 1,000-database scale claims. Measure and design those only in a later increment.

---

## Isolation, Branches, and Promotion Gates

| Ring | Repository and ref | Permitted work | Explicitly prohibited |
| --- | --- | --- | --- |
| Research | `platform-ci@feature/exacs-workshop-playbooks` and the prior ExaCS demo history | Read and extract behavior/tests worth preserving. | New implementation, certification claims, or new dependencies on its workarounds. |
| Integration | `platform-ci@feature/exacs-cdb-create`, freshly branched from current certified `main` | All implementation, unit tests, workflow checks and review commits. | Merge to `main`, generic-template edits consumed by existing projects, or a mutable workflow dependency. |
| Certification | `nonprod-exacs-project01@feature/exacs-cdb-create` | Pin a reviewed Platform CI commit SHA, carry the isolated operation request and handoff, and run approved non-production checks. | Changing any certified project, production resource, shared VM Cluster, or public catalog. |
| Publication | Platform CI and templates `main` | One reviewed promotion PR after every Task 7 gate is accepted. | Promotion with a failed/untested certification case or with the ExaCS project still using a branch name rather than the reviewed release ref. |

The implementation paths below describe their eventual repository locations. Until Task 7 succeeds, changes under `platform-ci/` land only on the Platform CI integration branch, and project/workflow/catalog changes land only in the paired ExaCS repository branch. A subsequent, separate promotion PR copies the reviewed capability into the certified sources; it is not part of the development certification run.

---

## File Structure

| Path | Responsibility |
| --- | --- |
| `repository-sources/platform-ci/scripts_python/validate_exacs_terraform_boundary.py` | Rejects Exadata Terraform manifests that try to manage DB Homes, CDBs, or PDBs. |
| `repository-sources/platform-ci/scripts_python/prepare_operation_manifest.py` | Materializes secret tokens into one temporary Ansible operation manifest. |
| `repository-sources/platform-ci/scripts_python/ansible_inventory.py` | Resolves a Terraform-managed ExaCS VM Cluster by display name and emits the CDB operation inventory. |
| `repository-sources/platform-ci/scripts_python/validate_operation_manifest.py` | Defines the closed manifest schema and field limits for `exacs-cdb-create`. |
| `repository-sources/platform-ci/ansible/playbooks/operations/exacs-cdb-create.yml` | Thin CDB creation orchestrator. |
| `repository-sources/platform-ci/ansible/playbooks/common/oci/exacs-cdb-create/{precheck,apply,verify}.yml` | OCI read, create and verification phases. |
| `repository-sources/platform-ci/actions/{terraform-execution,ansible-execution}/action.yml` | Applies the Terraform ownership boundary; resolves operation secrets; routes the allow-listed CDB playbook. |
| `repository-sources/platform-ci/.github/workflows/ansible-shared.yaml` | Receives the selected repository secret bundle safely. |
| `nonprod-exacs-project01/.github/workflows/{terraform,ansible}.yaml` | Isolated certification caller: pins the Orchestrator ref and immutable Platform CI commit. |
| `repository-sources/{nonprod,prod}-project-template/.github/workflows/{terraform,ansible}.yaml` | Publication-only targets after Task 7 acceptance. |
| `repository-sources/gitops-templates/operations-catalog/oci/exacs-cdb-create.json` | Publication-only approved request template. |
| `repository-sources/gitops-templates/operations-catalog/specs/oci/exacs-cdb-create.md` | Publication-only contract, precheck semantics, recovery behavior and request examples. |
| `repository-sources/platform-ci/tests/` | Unit tests for the boundary validator, secret preparation, manifest validation, inventory extraction, and routing contract. |
| `docs/reference/{support,architecture}.md` and `docs/usage/` | Published capability, ownership model, onboarding requirements, and operator walkthrough. |

## Task 0: Create the isolated two-repository integration surface

**Repositories and refs:**

- Create: `multicloud-control-plane/platform-ci@feature/exacs-cdb-create`, based on its current certified `main` commit.
- Create: `multicloud-control-plane/nonprod-exacs-project01@feature/exacs-cdb-create`, based on its current `main` commit.
- Read only: `platform-ci@feature/exacs-workshop-playbooks` as the legacy workshop reference.

**Interfaces:**

- Produces: a recorded Platform CI source commit and its immutable SHA, plus one paired ExaCS project pull request that consumes that exact SHA.
- Does not produce: a change to Platform CI `main`, templates consumed by other projects, any public catalogue, or a release tag.

- [ ] **Step 1: Record the three starting points**

Before creating either feature branch, record: Platform CI `main` SHA, the legacy workshop branch SHA, and `nonprod-exacs-project01` `main` SHA. Inspect the diffs from the workshop branch to identify reusable Ansible operation fragments, but make the current Platform CI `main` the code base for the new implementation.

- [ ] **Step 2: Create paired feature branches and protect the dependency**

Create the two `feature/exacs-cdb-create` branches. After the first reviewed Platform CI commit exists, update only the paired ExaCS project branch to call Platform CI at that exact commit SHA. The workflow must reject an empty, branch-shaped, or non-40-hex Platform CI reference during certification.

- [ ] **Step 3: Prove the certified surface is unchanged**

Verify that Platform CI `main`, the generic non-production/production templates, and the public operations catalogue contain no `exacs-cdb-create` reference. Preserve this evidence with the certification record.

- [ ] **Step 4: Commit the integration wiring separately**

Commit the Platform CI implementation and the ExaCS project pin in separate repositories and separate pull requests. The ExaCS project PR must link the immutable Platform CI commit it certifies. Do not merge either PR to its certified default branch at this stage.

## Task 1: Establish the test harness and Terraform ownership boundary

**Files:**

- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/__init__.py`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_validate_exacs_terraform_boundary.py`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/validate_exacs_terraform_boundary.py`
- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/actions/terraform-execution/action.yml`
- Modify: `multicloud-control-plane/nonprod-exacs-project01/.github/workflows/terraform.yaml` on its paired feature branch only.

**Interfaces:**

- Consumes: a project tuple directory containing JSON Terraform input files.
- Produces: `validate_directory(config_dir: Path) -> None`, which raises `ValueError` with the offending relative path and top-level key.
- Produces: the paired ExaCS project passes `orchestrator_ref: release-2.1.4` for OCI. Generic templates are a publication-only target.

- [ ] **Step 1: Write the failing boundary tests**

```python
class ExacsTerraformBoundaryTests(unittest.TestCase):
    def test_allows_infrastructure_and_vm_cluster_only(self):
        validate_document({
            "cloud_exadata_database_configuration": {
                "cloud_exadata_infrastructures_configuration": {"infra": {}},
                "cloud_vm_clusters_configuration": {"cluster": {}},
            }
        }, Path("oci/dev/eu-frankfurt-1/exadata/platform.json"))

    def test_rejects_terraform_db_home_ownership(self):
        with self.assertRaisesRegex(ValueError, "cloud_db_homes_configuration"):
            validate_document({
                "cloud_exadata_database_configuration": {
                    "cloud_db_homes_configuration": {"home": {"display_name": "dbhome-a"}}
                }
            }, Path("oci/dev/eu-frankfurt-1/exadata/platform.json"))
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_validate_exacs_terraform_boundary -v
```

Expected: FAIL because `validate_exacs_terraform_boundary` does not exist.

- [ ] **Step 3: Implement a fail-closed JSON boundary validator**

Implement `validate_document` and `validate_directory`. For every `*.json` outside `lifecycle_operations`, parse JSON. When `cloud_exadata_database_configuration` exists, reject a present and non-empty `cloud_db_homes_configuration`, `databases_configuration`, or `pluggable_databases_configuration`. Allow absent, `null`, `{}`, and `[]` values. Error messages must name the source file and prohibited configuration family.

- [ ] **Step 4: Invoke the validator before Terraform variable preparation**

Insert a `Validate ExaCS ownership boundary` step in `terraform-execution/action.yml` after `Resolve config` and before `Prepare variables`:

```bash
python3 "${{ github.action_path }}/../../scripts_python/validate_exacs_terraform_boundary.py" \
  "${{ github.workspace }}/${{ steps.config.outputs.config_subpath }}"
```

Keep non-ExaCS resource manifests valid.

- [ ] **Step 5: Pin the paired ExaCS project's OCI Orchestrator ref**

Set only `nonprod-exacs-project01@feature/exacs-cdb-create` to `release-2.1.4`. Leave the certified generic templates and all non-OCI callers unchanged until publication.

- [ ] **Step 6: Run the focused tests and composite-action syntax checks**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_validate_exacs_terraform_boundary -v
jq -e . ../nonprod-exacs-project01/oci/dev/eu-frankfurt-1/compute/compute.json
ruby -e 'require "yaml"; YAML.load_file("actions/terraform-execution/action.yml")'
rg -n 'release-2\.1\.4' ../nonprod-exacs-project01/.github/workflows/terraform.yaml
```

Expected: tests pass, the composite action parses as YAML, and the isolated ExaCS OCI caller contains `release-2.1.4`.

- [ ] **Step 7: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/validate_exacs_terraform_boundary.py \
  oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests \
  oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/actions/terraform-execution/action.yml
git commit -m "feat: enforce ExaCS Terraform ownership boundary"
```

Commit the paired `nonprod-exacs-project01` workflow pin separately, after this Platform CI commit SHA exists.

### Task 2: Add the closed CDB request contract and secret materialization

**Files:**

- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/prepare_operation_manifest.py`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_manifest.py`
- Create: `multicloud-control-plane/nonprod-exacs-project01/operations/exacs-cdb-create.json` on the paired feature branch; the public catalog template is a promotion-only copy.
- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/validate_operation_manifest.py`
- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/actions/ansible-execution/action.yml`
- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/.github/workflows/ansible-shared.yaml`
- Modify: `multicloud-control-plane/nonprod-exacs-project01/.github/workflows/ansible.yaml` on the paired feature branch only.

**Interfaces:**

- Consumes: an `exacs-cdb-create` JSON manifest and `GITOPS_SECRET_VALUES` JSON from the selected environment secret.
- Produces: `validate(document: object) -> str` returning `exacs-cdb-create` only for valid documents.
- Produces: `prepare_file(source: Path, destination: Path, environment: str) -> None`; it writes a JSON copy with every runtime token resolved and no token remaining.
- Manifest shape:

```json
{
  "operation_type": "exacs-cdb-create",
  "vm_cluster_display_name": "project1-dev-vmcluster",
  "db_home_display_name": "project1-dbhome-23-26-3",
  "targets": [
    {
      "db_name": "orders",
      "db_unique_name": "orders_dev",
      "admin_password": "__DEV_ORDERS_CDB_ADMIN_PASSWORD__",
      "character_set": "AL32UTF8",
      "ncharacter_set": "AL16UTF16",
      "timeout_minutes": 240
    }
  ]
}
```

- [ ] **Step 1: Write failing manifest and secret-preparation tests**

```python
def test_accepts_a_valid_exacs_cdb_manifest(self):
    self.assertEqual(validate(VALID_MANIFEST), "exacs-cdb-create")

def test_rejects_a_raw_admin_password(self):
    document = copy.deepcopy(VALID_MANIFEST)
    document["targets"][0]["admin_password"] = "UnsafePassword_12"
    with self.assertRaises(SystemExit):
        validate(document)

def test_rejects_duplicate_cdb_or_password_token(self):
    document = copy.deepcopy(VALID_MANIFEST)
    document["targets"].append(copy.deepcopy(document["targets"][0]))
    with self.assertRaises(SystemExit):
        validate(document)

def test_materializes_only_environment_qualified_tokens(self):
    os.environ["GITOPS_SECRET_VALUES"] = '{"DEV_ORDERS_CDB_ADMIN_PASSWORD":"masked"}'
    prepare_file(source, destination, "dev")
    self.assertEqual(json.loads(destination.read_text())["targets"][0]["admin_password"], "masked")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_exacs_cdb_manifest -v
```

Expected: FAIL because the operation is absent from the validator and no operation materializer exists.

- [ ] **Step 3: Add the schema to `validate_operation_manifest.py`**

Add `exacs-cdb-create` to the closed top-level and target-key maps. Require non-empty `vm_cluster_display_name` and `db_home_display_name`; exactly one target; ASCII identifiers for `db_name` and `db_unique_name`; and `timeout_minutes` as an integer between 1 and 480. Require `admin_password` to match exactly `__[A-Z0-9_]+__`; reject all raw password values and every unknown field.

- [ ] **Step 4: Implement temporary operation-manifest preparation**

Reuse the placeholder grammar, environment check, `load_secret_values`, masking and recursive replacement functions from `prepare_var_files.py`. The new script accepts `<source> <destination> <environment>`, parses exactly one JSON object, resolves every token, rejects missing, cross-environment and unresolved tokens, then writes the destination under `$RUNNER_TEMP`. Do not print the JSON, replacement values or destination contents.

- [ ] **Step 5: Wire secrets only through the shared workflow and paired project**

Add required `repository_secret_values` to `ansible-shared.yaml` secrets. Add it to the composite action as a string input, set it only as `GITOPS_SECRET_VALUES` for the preparation step, and pass the selected environment secret only from the paired `nonprod-exacs-project01` caller. Prepare `$WORK_TEMP/operation.json` after raw validation; all subsequent discovery, inventory and Ansible invocations use that temporary path. Do not modify generic non-production or production template callers in this increment.

- [ ] **Step 6: Add the isolated request fixture**

Create `exacs-cdb-create.json` in the paired ExaCS project with the exact manifest shape above and placeholders only. Do not put a real OCID, actual database name, password or customer value in the request fixture. The public catalog copy is deferred to promotion.

- [ ] **Step 7: Run focused tests**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_exacs_cdb_manifest -v
python3 scripts_python/validate_operation_manifest.py ../nonprod-exacs-project01/operations/exacs-cdb-create.json
```

Expected: tests pass and the isolated request fixture is accepted without resolving its placeholders.

- [ ] **Step 8: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
git commit -m "feat: add governed ExaCS CDB request contract"
```

Commit `operations/exacs-cdb-create.json` and the paired project Ansible workflow pin separately in `nonprod-exacs-project01`.

### Task 3: Resolve the VM Cluster from state and CDB parents from OCI

**Files:**

- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/ansible_inventory.py`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_inventory.py`

**Interfaces:**

- Consumes: Terraform state containing `oci_database_cloud_vm_cluster` instances and a resolved CDB operation manifest.
- Produces: `parse_exacs_vm_clusters(state_data: dict) -> dict[str, dict]` and `build_exacs_cdb_inventory(manifest: dict, clusters: dict[str, dict]) -> dict`.
- Produces this temporary inventory shape:

```json
{
  "all": {"children": {"exacs_cdb_targets": {}}},
  "exacs_cdb_targets": {
    "vars": {
      "exacs_vm_cluster_id": "resolved-internal-id",
      "exacs_compartment_id": "resolved-internal-id",
      "exacs_db_home_display_name": "project1-dbhome-23-26-3"
    },
    "hosts": {
      "orders_dev": {
        "ansible_connection": "local",
        "exacs_db_name": "orders",
        "exacs_db_unique_name": "orders_dev",
        "exacs_admin_password": "resolved-secret",
        "exacs_character_set": "AL32UTF8",
        "exacs_ncharacter_set": "AL16UTF16",
        "exacs_timeout_minutes": 240
      }
    }
  }
}
```

- [ ] **Step 1: Write failing state-resolution tests**

```python
def test_resolves_one_vm_cluster_by_display_name(self):
    inventory = build_exacs_cdb_inventory(MANIFEST, parse_exacs_vm_clusters(STATE))
    group = inventory["exacs_cdb_targets"]
    self.assertEqual(group["vars"]["exacs_vm_cluster_id"], "ocid.vmcluster.a")
    self.assertIn("orders_dev", group["hosts"])

def test_rejects_absent_or_duplicate_vm_cluster_display_names(self):
    with self.assertRaises(SystemExit):
        build_exacs_cdb_inventory(MANIFEST, {})
    with self.assertRaises(SystemExit):
        build_exacs_cdb_inventory(MANIFEST, {"project1-dev-vmcluster": [{}, {}]})
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_exacs_cdb_inventory -v
```

Expected: FAIL because ExaCS inventory functions do not exist.

- [ ] **Step 3: Implement state parsing without database-resource ownership**

Index only `oci_database_cloud_vm_cluster` state instances. Require non-empty `id`, `compartment_id`, and `display_name`; retain a list for duplicate display names so the resolver can fail instead of silently overwriting one. Do not read `oci_database_db_home`, `oci_database_database` or `oci_database_pluggable_database` resources from state.

- [ ] **Step 4: Route `exacs-cdb-create` into the inventory builder**

After the one existing state download, route `exacs-cdb-create` to `parse_exacs_vm_clusters` and `build_exacs_cdb_inventory`. The generated inventory carries only the resolved VM Cluster and compartment IDs, requested DB Home display name, target names and temporary password values. Do not list DB Homes or CDBs in this Python script; OCI facts in the playbook own that live discovery.

- [ ] **Step 5: Run the focused tests**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest tests.test_exacs_cdb_inventory -v
```

Expected: absent, duplicate and malformed state records fail; one valid state entry produces the documented inventory.

- [ ] **Step 6: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/scripts_python/ansible_inventory.py \
  oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_inventory.py
git commit -m "feat: resolve ExaCS VM clusters from Terraform state"
```

### Task 4: Implement the explicit precheck, create and verify playbooks

**Files:**

- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/ansible/playbooks/operations/exacs-cdb-create.yml`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/ansible/playbooks/common/oci/exacs-cdb-create/precheck.yml`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/ansible/playbooks/common/oci/exacs-cdb-create/apply.yml`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/ansible/playbooks/common/oci/exacs-cdb-create/verify.yml`
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_playbook_contract.py`

**Interfaces:**

- Consumes: `exacs_cdb_targets` inventory from Task 3 and `operation_execution_mode` equal to `precheck` or `execute`.
- Produces: per-target facts `exacs_db_home`, `exacs_existing_databases`, `exacs_create_required`, and execution evidence with resolved IDs, name, final lifecycle state and DB Home ID.

- [ ] **Step 1: Write failing static playbook-contract tests**

```python
def test_operation_playbook_has_precheck_apply_verify_in_that_order(self):
    text = OPERATION.read_text()
    self.assertLess(text.index("Precheck CDB creation"), text.index("Apply CDB creation"))
    self.assertLess(text.index("Apply CDB creation"), text.index("Verify CDB creation"))

def test_apply_tasks_are_execute_gated_and_password_is_no_log(self):
    text = APPLY.read_text()
    self.assertIn("operation_execution_mode == 'execute'", text)
    self.assertIn("no_log: true", text)

def test_precheck_uses_vm_cluster_and_db_home_display_name(self):
    text = PRECHECK.read_text()
    self.assertIn("vm_cluster_id: \"{{ exacs_vm_cluster_id }}\"", text)
    self.assertIn("display_name: \"{{ exacs_db_home_display_name }}\"", text)
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
python3 -m unittest tests.test_exacs_cdb_playbook_contract -v
```

Expected: FAIL because the playbook files do not exist.

- [ ] **Step 3: Implement read-only precheck**

Use `oracle.oci.oci_database_db_home_facts` with the resolved compartment, VM Cluster ID and requested DB Home display name. Assert exactly one returned DB Home, `AVAILABLE`, and matching `vm_cluster_id`. Then use `oracle.oci.oci_database_database_facts` once for that resolved DB Home and construct an in-memory index keyed by `db_name`. For each target:

- no matching CDB means creation is required;
- one CDB whose `db_unique_name`, `db_home_id`, lifecycle state and requested immutable attributes match is a no-op;
- any mismatch, duplicate, or transitional lifecycle state fails the precheck.

All fact tasks use `check_mode: false`; none creates, patches, moves, restarts or deletes a resource in PR mode.

- [ ] **Step 4: Implement execute-only creation**

For targets marked creation-required, call `oracle.oci.oci_database_database` with the resolved DB Home ID, project compartment, target `db_name`, `db_unique_name`, character sets and administrator password. Use `auth_type: instance_principal`, `wait: true`, and `wait_timeout: timeout_minutes * 60`. Mark the task and all secret-carrying debug/register output `no_log: true`. Existing matching targets remain no-ops.

- [ ] **Step 5: Implement post-create verification**

For every target, call `oci_database_database_facts` by resolved DB Home. Assert exactly one CDB with the requested `db_name`, `db_unique_name`, resolved DB Home ID and `AVAILABLE` state. Report only display/name identifiers, resolved CDB/DB Home IDs and lifecycle state; do not print secrets or connection strings.

- [ ] **Step 6: Create the thin operation orchestrator**

Require a valid execution mode, import `precheck.yml`, import `apply.yml` only for execute mode, and import `verify.yml` only for execute mode. The wrapper has no OCI module calls of its own.

- [ ] **Step 7: Run the focused contract tests and syntax check**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
python3 -m unittest tests.test_exacs_cdb_playbook_contract -v
ansible-playbook --syntax-check ansible/playbooks/operations/exacs-cdb-create.yml
```

Expected: static contract tests and Ansible syntax check pass.

- [ ] **Step 8: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/ansible \
  oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_playbook_contract.py
git commit -m "feat: add governed ExaCS CDB creation playbook"
```

### Task 5: Route the allow-listed operation and enforce the handoff boundary

**Files:**

- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/actions/ansible-execution/action.yml`
- Modify: the Cloud Operations handoff in `multicloud-control-plane/nonprod-exacs-project01` on its paired feature branch.
- Create: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_routing_contract.py`

**Interfaces:**

- Consumes: validated `operation_type=exacs-cdb-create` and a handoff whose OCI section names an exclusive VM Cluster and project Database compartment.
- Produces: the hard-coded `playbooks/operations/exacs-cdb-create.yml` selection. No project field selects a file, command, tag or runner label.

- [ ] **Step 1: Write failing routing and handoff tests**

```python
def test_action_has_an_explicit_exacs_cdb_playbook_mapping(self):
    text = ACTION.read_text()
    self.assertIn("exacs-cdb-create)", text)
    self.assertIn('OPERATION_PLAYBOOK="playbooks/operations/exacs-cdb-create.yml"', text)

def test_action_does_not_accept_a_project_playbook_path(self):
    text = ACTION.read_text()
    self.assertNotIn('OPERATION_PLAYBOOK="${{', text)

def test_handoff_documents_exclusive_vm_cluster_allocation(self):
    self.assertIn("ExaCS VM Cluster display name", DEV_HANDOFF.read_text())
    self.assertIn("exclusive to this project repository", DEV_HANDOFF.read_text())
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
python3 -m unittest tests.test_exacs_cdb_routing_contract -v
```

Expected: FAIL because the mapping and handoff fields do not exist.

- [ ] **Step 3: Add the explicit dispatch mapping**

Add this branch to the existing shell `case` in `Resolve operation playbook`:

```bash
exacs-cdb-create)
  OPERATION_PLAYBOOK="playbooks/operations/exacs-cdb-create.yml"
  ;;
```

Keep the default rejection. Do not add generic operation paths, tags or arbitrary Ansible arguments.

- [ ] **Step 4: Publish the minimum ExaCS handoff fields**

Add an OCI section to the paired ExaCS project handoff containing Cloud Operations-owned rows for `ExaCS VM Cluster display name`, `Database compartment ID`, `ExaCS runner boundary`, and `Allocation`. Define `Allocation` as `exclusive to this project repository` for the first release. State that a shared VM Cluster is not eligible until cross-repository coordination is published. Do not add these fields to generic templates before the publication gate.

- [ ] **Step 5: Run focused tests and workflow syntax validation**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
python3 -m unittest tests.test_exacs_cdb_routing_contract -v
actionlint actions/ansible-execution/action.yml ../nonprod-exacs-project01/.github/workflows/ansible.yaml
```

Expected: tests pass and Actionlint accepts all workflow YAML.

- [ ] **Step 6: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/actions/ansible-execution/action.yml \
  oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/tests/test_exacs_cdb_routing_contract.py
git commit -m "feat: route governed ExaCS CDB creation"
```

Commit the ExaCS handoff change in `nonprod-exacs-project01` separately.

### Task 6: Prepare unpublished catalog and operational documentation

**Files:**

- Create: `multicloud-control-plane/nonprod-exacs-project01/docs/exacs-cdb-create.md` on the paired feature branch.
- Modify: `oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/README.md`
- Do not modify: public catalog, `support.md`, reference architecture, generic templates, or public walkthrough before Task 7 accepts certification.

**Interfaces:**

- Consumes: the exact JSON template and validator from Task 2 and the execution behavior from Tasks 3–5.
- Produces: a private review guide that describes precheck, execution, retries, request cleanup, name resolution and limitations without showing a real customer ID or secret.

- [ ] **Step 1: Add the operation specification**

Document the exact manifest schema, target limit, identifier meanings, secret-token format, required handoff rows, precheck behavior, execute behavior and evidence fields. State that an existing matching CDB is a no-op; an existing CDB with a conflicting unique name, DB Home or immutable value is rejected; and a completed request is removed in a focused pull request without reversing the CDB creation.

- [ ] **Step 2: Update the Platform CI feature-branch capability table only**

Explain in the feature-branch Platform CI README that it resolves VM Cluster identity from Terraform state and DB Home/CDB identity from OCI. Keep the operation absent from the public catalog field reference and certified current-operations table until promotion.

- [ ] **Step 3: Record the candidate architecture and support scope privately**

Document this ownership boundary in the paired ExaCS review guide: Terraform and Orchestrator own Exadata infrastructure and VM Clusters; Ansible owns DB Homes, CDBs and PDBs. Mark the operation as certification-only, and Optional UI and Codex plugin unavailable until they render the catalog contract correctly.

- [ ] **Step 4: Create a safe walkthrough**

Show one CDB request with placeholder names and `__DEV_...__` password token. Include required secret-bundle member key, the expected PR precheck, merge behavior, and how to read the operation evidence. Do not include a password, OCID, state location or runner implementation detail. Keep this guide in the paired private project until release.

- [ ] **Step 5: Validate documentation links and JSON**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane
jq -e . ../nonprod-exacs-project01/operations/exacs-cdb-create.json
rg -n 'exacs-cdb-create|release-2\.1\.4' repository-sources/platform-ci ../nonprod-exacs-project01
git diff --check
```

Expected: the isolated request fixture parses, every integration-branch operation reference is intentional, and Git finds no whitespace errors.

- [ ] **Step 6: Commit**

```bash
git add oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci/README.md
git commit -m "docs: document ExaCS CDB certification candidate"
```

Commit the paired ExaCS guide separately. This task creates no public publication commit.

### Task 7: Certify the complete delivery chain in the isolated ExaCS project

**Files:**

- Create: `multicloud-control-plane/nonprod-exacs-project01/docs/exacs-cdb-certification.md` on the paired feature branch.
- Do not modify: the certified `support.md` before the publication gate.

**Interfaces:**

- Consumes: a dedicated non-production VM Cluster, complete Cloud Operations handoff, runner identity, state access, database compartment access, and one environment secret token.
- Produces: reviewable certification evidence for manifest validation, PR precheck, post-merge creation, idempotent repeat, invalid-name rejection and interruption recovery observation.

- [ ] **Step 1: Define the certification matrix before any live request**

Create a table with these cases and expected outcomes: valid CDB creation; valid rerun with no CDB mutation; unknown VM Cluster; duplicate VM Cluster display name in state; unknown DB Home; duplicate DB Home match; cross-environment password token; missing password secret member; existing CDB with conflicting `db_unique_name`; and denied runner permission. Include whether each case runs locally, as a PR check or as an approved non-production execution.

- [ ] **Step 2: Run offline validation**

Run:

```bash
cd oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/repository-sources/platform-ci
PYTHONPATH=scripts_python python3 -m unittest discover -s tests -v
ansible-playbook --syntax-check ansible/playbooks/operations/exacs-cdb-create.yml
actionlint actions/ansible-execution/action.yml .github/workflows/ansible-shared.yaml
```

Expected: all unit, syntax and workflow checks pass before a cloud request is prepared.

- [ ] **Step 3: Perform a non-production PR precheck**

Use the catalog template in a disposable project repository with placeholder-only committed secret token. Verify the PR checks read the VM Cluster from state, find the requested DB Home, report the planned CDB name, and make no OCI mutation.

- [ ] **Step 4: Perform the approved non-production creation and idempotent rerun**

After the independent approval and merge, verify one CDB reaches `AVAILABLE` in the requested DB Home. Submit the same request again and verify it reports no mutation. Record the workflow URLs, commit IDs, resolved Orchestrator revision, operation evidence and Cloud Operations acceptance record; never record secret values.

- [ ] **Step 5: Exercise failure and recovery cases**

Run the invalid-name, missing-secret and duplicate-name requests as rejected PR checks. For interruption recovery, terminate only a disposable workflow after OCI accepted a test creation request, then rerun the same manifest and verify the precheck discovers the existing resource rather than requesting a duplicate creation.

- [ ] **Step 6: Accept or reject publication eligibility**

Require every certification case to pass and Cloud Operations to accept the runner and handoff policy. Otherwise keep the feature branch certification-only and record the failed case in the private certification document. This step creates no change to the certified support status.

- [ ] **Step 7: Commit the certification contract**

```bash
git add docs/exacs-cdb-certification.md
git commit -m "docs: record ExaCS CDB certification"
```

### Task 8: Promote the reviewed capability only after certification acceptance

**Files:**

- Create or modify: the public catalog template and specification, Platform CI and generic project template workflows, handoff templates, reference architecture, support matrix and walkthrough listed in Tasks 1–6.

**Interfaces:**

- Consumes: accepted Task 7 evidence, the exact reviewed Platform CI integration commit, Cloud Operations acceptance, and a release decision.
- Produces: one explicitly reviewed promotion PR per certified repository, with the immutable source commit recorded. The promotion changes the supported references only after its own CI passes.

- [ ] **Step 1: Rebase/port once from current certified sources**

Start promotion from then-current Platform CI `main`, not from the legacy workshop branch. Apply only the reviewed implementation commits, resolve drift deliberately, and rerun Tasks 1–6 offline validation against the promotion branch.

- [ ] **Step 2: Publish the public contract and templates**

Copy the reviewed request fixture into `gitops-templates/operations-catalog/oci/exacs-cdb-create.json`; add its specification, generic handoff rows, supported-operation entry, architecture and safe walkthrough. Update generic project templates only in this promotion PR. Change `support.md` to supported only when the Task 7 evidence is attached.

- [ ] **Step 3: Use immutable references in release consumers**

Replace the paired ExaCS project feature SHA with the reviewed Platform CI release tag or immutable release commit. Do not leave a workflow that depends on `feature/exacs-cdb-create` or any other mutable branch.

- [ ] **Step 4: Run promotion checks and merge by normal governance**

Require unit tests, Ansible syntax, Actionlint, catalog JSON validation, template contract checks and review of the certification evidence. Merge each promotion PR only through the normal protected-branch process; no direct push and no deployment is implied by publication.

## Deferred Follow-on Increments

Do not combine these with CDB creation. Each has a distinct recovery model and needs its own catalog, validation, playbook, permissions, tests and certification:

1. `exacs-db-home-create`: create one DB Home through Ansible, validate its version/image and wait for `AVAILABLE`.
2. `exacs-pdb-create`: resolve its CDB by `db_name` and `db_unique_name`, then create PDBs by `pdb_name`.
3. `exacs-db-home-patch`: explicit precheck, patch operation, impact evaluation for every CDB using the DB Home and verification.
4. `exacs-cdb-move-db-home`: explicit source DB Home, target DB Home and final CDB association verification.
5. Shared VM Cluster support: a Cloud Operations-owned cross-repository lease service, expiry/recovery semantics and dedicated certification. Until then, handoff allocation remains exclusive.

## Plan Self-Review

- Isolation: Task 0 keeps investigation, implementation, cloud certification and publication in separate branch/repository rings. The legacy workshop branch is read-only evidence; Platform CI `main`, generic templates and the public catalogue are untouched until Task 8.
- Coverage: Tasks 1–5 implement the ownership boundary, pinned orchestrator reference, state resolution, names, runtime secrets, an explicit one-CDB operation, idempotence and exclusive-cluster concurrency limit. Task 6 prepares private operational material. Task 7 certifies recovery behavior; scale is deliberately deferred. Task 8 is the separately gated publication.
- Scope: the plan delivers only CDB creation. DB Homes, PDBs, movement, patching and shared-cluster locking remain separate operations because their safety and rollback characteristics differ.
- Ambiguity: the catalog uses OCI's actual CDB identifiers `db_name` and `db_unique_name`, rather than an invented CDB `display_name`; DB Home and VM Cluster retain their OCI `display_name` fields.
- Validation levels: this plan defines unit, syntax, workflow and non-production certification checks. It does not claim a Terraform plan or OCI execution has already passed, and no production operation follows automatically from the plan.
