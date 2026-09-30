# ExaCS Day-2 inventory implementation plan

> **For implementation:** execute each task in order and keep all live database
> operations on the dedicated ExaCS runner. Terraform remains plan-only for the
> adopted infrastructure and VM Cluster.

**Goal:** Provide reusable, append-only CRQ manifests for ExaCS DB Home, CDB,
PDB, and out-of-place patch operations, then record the verified OCI-observed
database topology in a Git-tracked inventory without making OCI IDs user input.

**Architecture:** The project repository keeps a desired Terraform boundary for
Cloud Exadata Infrastructure and VM Cluster, immutable operation requests under
`oci/.../lifecycle_operations`, and a separate observed database inventory under
`inventory/oci/...`. The shared Ansible action resolves its execution boundary
from Terraform state, runs an allow-listed operation, verifies it, derives the
observed inventory from OCI facts, and writes it only after success. The project
workflow grants write access solely to the main-branch post-verification path.

**Scope:** `platform-ci` special ExaCS branch, the ExaCS lab project, and this
template branch. Do not change `platform-ci/main`; do not apply Terraform; do
not create Cloud Exadata Infrastructure or VM Clusters.

**Technology:** GitHub Actions reusable workflows and composite actions, Python
3 state/manifest processing, Ansible OCI facts/modules, JSON project manifests.

---

## Task 1: Add reusable CRQ and observed-inventory templates

**Files:**

- Add: `repository-sources/nonprod-project-template/templates/exacs-day2/crq-dbhome-create.json`
- Add: `repository-sources/nonprod-project-template/templates/exacs-day2/crq-cdb-create.json`
- Add: `repository-sources/nonprod-project-template/templates/exacs-day2/crq-pdb-create.json`
- Add: `repository-sources/nonprod-project-template/templates/exacs-day2/crq-oop-patch.json`
- Add: `repository-sources/nonprod-project-template/templates/exacs-day2/exacs-databases.json`
- Modify: `repository-sources/nonprod-project-template/README.md`

**Step 1: Define one template for each allowed operation.**

Place templates outside `oci/` so copying a project template never invokes a
workflow. Use the operation schema accepted by
`scripts_python/validate_operation_manifest.py`; use logical display names,
secret placeholders, and an explicit `crq-<number>-...json` destination. Do not
include OCIDs or a mutable execution-status field.

**Step 2: Define the empty observed inventory contract.**

Use `inventory/oci/<environment>/<region>/exacs-databases.json` as the target
destination. The skeleton must carry a stable schema/version and empty DB Home,
CDB, and PDB collections, while explaining that values are OCI-observed only.

**Step 3: Document the copy-and-run flow.**

Document: copy exactly one CRQ template to
`oci/<environment>/<region>/lifecycle_operations/crq-<number>-<operation>.json`,
replace placeholders, commit once, and never edit it after execution. State
that the workflow creates or refreshes the observed inventory only after
verification and that inventory is not an input to Terraform or Ansible.

**Step 4: Validate template JSON.**

Run: `jq empty` over all five JSON templates.

**Step 5: Commit the template-only change.**

```bash
git add repository-sources/nonprod-project-template
git commit -m "feat: add ExaCS day-2 request templates"
```

## Task 2: Derive a normalized observed ExaCS database inventory

**Files:**

- Add: `platform-ci/scripts_python/exacs_database_inventory.py`
- Modify: `platform-ci/actions/exacs-ansible-execution/action.yml`
- Add: `platform-ci/tests/test_exacs_database_inventory.py`

**Step 1: Implement a side-effect-free inventory renderer.**

Accept normalized OCI facts for the selected VM Cluster and compartment, then
write deterministic JSON containing DB Home display name/version/lifecycle
state, CDB name/unique name/home display name/lifecycle state, and PDB name/CDB
unique name/lifecycle state. Exclude resource identifiers from the committed
file. Sort all collections by their logical keys.

**Step 2: Collect facts only after Ansible verification.**

In the ExaCS Ansible composite action, invoke the renderer only after the
allow-listed playbook exits successfully. Reuse the state-derived VM Cluster and
compartment values; query OCI through the runner profile. Failure to collect or
validate facts fails the operation rather than publishing a partial inventory.

**Step 3: Expose a safe artifact/output for publication.**

Write the rendered JSON to the action work directory and expose its path and
the intended project-relative inventory path as action outputs. Do not print
the file contents or OCI identifiers to logs.

**Step 4: Write focused renderer tests.**

Cover deterministic sorting, absence of identifier fields, empty topology, and
the DB Home/CDB/PDB relationship rendering. Run:

```bash
python3 -m unittest tests/test_exacs_database_inventory.py
```

**Step 5: Commit the shared action and renderer.**

```bash
git add scripts_python/exacs_database_inventory.py actions/exacs-ansible-execution/action.yml tests/test_exacs_database_inventory.py
git commit -m "feat: publish verified ExaCS database inventory"
```

## Task 3: Publish inventory to the project only after success

**Files:**

- Modify: `platform-ci/.github/workflows/exacs-ansible-shared.yaml`
- Modify: `nonprod-exacs-project01/.github/workflows/ansible.yaml`
- Add: `nonprod-exacs-project01/inventory/oci/dev/uk-london-1/exacs-databases.json`

**Step 1: Gate publication to trusted execution.**

The shared workflow must publish only when the invocation is a push to the
default branch and the operation job succeeded. Pull requests may validate the
manifest, but cannot write the observed inventory. Keep the dedicated
`exacs-database-operations` runner label.

**Step 2: Make publication atomic and loop-safe.**

Update only the target inventory file if the generated content differs. Commit
with a neutral automation identity and a fixed message that contains no
personal attribution. Use a path-scoped commit and push; an inventory-only
commit must not match lifecycle-operation triggers.

**Step 3: Grant the least workflow permission.**

Set `contents: write` only in the project workflow that invokes the shared
Ansible operation. Retain read-only permissions for Terraform and all unrelated
workflows. Explicitly confirm that repository Actions settings allow the
workflow token to create commits.

**Step 4: Add the empty lab inventory skeleton.**

Create the empty, schema-valid inventory at the exact project path. It must
contain no cloud identifiers and it must not sit under `oci/`.

**Step 5: Validate the execution gates.**

Run syntax checks for both workflow files and focused contract tests asserting:

- an inventory write requires a successful main-branch push;
- pull-request execution cannot write;
- an inventory-only commit cannot re-run an immutable CRQ;
- no Terraform workflow gains write permission or apply capability.

**Step 6: Commit separately in each authorized repository.**

```bash
# platform-ci special branch
git add .github/workflows/exacs-ansible-shared.yaml
git commit -m "feat: publish verified ExaCS inventory"

# ExaCS lab project main
git add .github/workflows/ansible.yaml inventory/oci/dev/uk-london-1/exacs-databases.json
git commit -m "feat: initialize ExaCS database inventory"
```

## Task 4: Demonstrate safely and hand off

**Files:**

- Modify: `nonprod-exacs-project01/oci/dev/uk-london-1/lifecycle_operations/` only by adding a new CRQ file when a real demo request is ready.

**Step 1: Preflight the runner read-only.**

Before a live Day-2 request, verify on the dedicated runner that the Terraform
state can resolve exactly the adopted VM Cluster and that OCI facts can list its
database topology. Do not run Terraform apply or create infrastructure.

**Step 2: Execute a single immutable CRQ.**

Add one CRQ file, observe its Ansible run, and confirm its verify phase before
checking the inventory commit. Do not modify the request file after its first
execution.

**Step 3: Verify the resulting Git state.**

Confirm exactly one inventory file changed, no identifiers were committed, and
the inventory describes the observed DB Home/CDB/PDB topology including OOP
target placement.

**Step 4: Run final regression checks.**

Run the focused Python/unit/contract checks, `actionlint` for altered workflows,
`jq empty` for all new JSON, and `git diff --check` in all three repositories.

**Step 5: Push only approved branches.**

Push the special `platform-ci` branch, the template feature branch, and the
lab project `main`. Never push or change `platform-ci/main`.
