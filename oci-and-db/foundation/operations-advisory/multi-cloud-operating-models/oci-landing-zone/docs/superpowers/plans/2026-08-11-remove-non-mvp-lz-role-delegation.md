# Remove Non-MVP Landing Zone Role Delegation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the unsupported shared Network and Security human-delegation feature so OP01 does not apply a nonexistent tag while project TBAC remains intact.

**Architecture:** Keep pinned One-OE, Hub E, and OCI TBAC. Narrow the local Jsonnet projection: OP01 omits `tagns-lz-role` tags and their policies; OP00 omits the two corresponding empty groups. Certify OP01 before OP00.

**Tech Stack:** Jsonnet; OE `dab13856ba6701c45baafc163780bb76562c039a`; Orchestrator `fcf1d7f02c0b4faa1ff55f1776c396452dd51761`; Python `unittest`; GitHub Actions.

## Global Constraints

- Preserve One-OE, Hub E, official TBAC `tn-lzp-proj-role`, Instance Principal, and OP00/OP01/OP02/OP04 state boundaries.
- Do not create `tagns-lz-role`, compatibility aliases, migrations, or custom IAM policies.
- Do not run Terraform locally or publish the local source branch.

---

### Task 1: Define the regression boundary

**Files:**
- Modify: `validation/test_landing_zone_contract.py`
- Test: `LandingZoneContractTests.test_mvp_omits_non_mvp_landing_zone_role_delegation`

**Interfaces:**
- Consumes: `components/oci-landing-zone/config/render.libsonnet`.
- Produces: an automated prohibition on the two non-MVP group keys, two policy keys, and `tagns-lz-role.tag-lz-role`.

- [ ] **Step 1: Write the failing test**

```python
def test_mvp_omits_non_mvp_landing_zone_role_delegation(self):
    source = (COMPONENT / "config" / "render.libsonnet").read_text()
    for forbidden in (
        "PCY-LZ-NETWORK-ADMIN-KEY",
        "PCY-LZ-SECURITY-ADMIN-KEY",
        "GRP-LZ-NETWORK-ADMIN-KEY",
        "GRP-LZ-SECURITY-ADMIN-KEY",
        "tagns-lz-role.tag-lz-role",
    ):
        self.assertNotIn(forbidden, source)
```

- [ ] **Step 2: Prove RED**

Run `PYTHONPYCACHEPREFIX=/private/tmp/oci-lz-pycache python3 -m unittest validation.test_landing_zone_contract.LandingZoneContractTests.test_mvp_omits_non_mvp_landing_zone_role_delegation -v`.

Expected: FAIL because the current projection still contains all five strings.

### Task 2: Remove the complete non-MVP projection

**Files:**
- Modify: `components/oci-landing-zone/config/render.libsonnet`
- Modify: `validation/test_landing_zone_contract.py`

**Interfaces:**
- Consumes: official One-OE IAM object and official TBAC object.
- Produces: OP01 IAM without tag-conditioned policies/tags and OP00 IAM without the two empty groups.

- [ ] **Step 1: Delete the two policy keys and two group keys from their source lists**

Remove `PCY-LZ-NETWORK-ADMIN-KEY`, `PCY-LZ-SECURITY-ADMIN-KEY`, `GRP-LZ-NETWORK-ADMIN-KEY`, and `GRP-LZ-SECURITY-ADMIN-KEY` from `render.libsonnet`.

- [ ] **Step 2: Remove the tag projection helper and its OP02 calls**

Delete `unmanaged_lz_role_tag`, `without_unmanaged_lz_role_tag`, and `environment_without_unmanaged_lz_role_tags`. Make OP02 use `environment_compartment` directly. Make `op01_iam` emit only `compartments_configuration`.

- [ ] **Step 3: Prove GREEN**

Run the Task 1 test. Expected: PASS.

- [ ] **Step 4: Regenerate the exact affected inputs**

Run `./components/oci-landing-zone/scripts/generate_foundation.sh op01` and `./components/oci-landing-zone/scripts/generate_foundation.sh op00`.

- [ ] **Step 5: Verify generated contracts**

Run `jq .` on both generated IAM files, then search OP00/OP01/OP02 generated output for the five forbidden strings. Expected: JSON parses and search returns no matches. Confirm `tn-lzp-proj-role` remains in OP01 governance.

### Task 3: Validate and commit local source

**Files:**
- Verify: `components/oci-landing-zone/config/render.libsonnet`
- Verify: `validation/test_landing_zone_contract.py`
- Verify: OP00/OP01 generated IAM files and workflows.

- [ ] **Step 1: Run full validation**

Run `PYTHONPYCACHEPREFIX=/private/tmp/oci-lz-pycache python3 -m unittest discover -s validation -v`, `actionlint components/oci-landing-zone/.github/workflows/*.yaml`, and `git diff --check`.

- [ ] **Step 2: Inspect exact diffs**

Confirm OP01 removes only the two tags and two policies; confirm OP00 removes only the two empty groups; confirm no One-OE, Hub E, or TBAC project configuration changes.

- [ ] **Step 3: Commit only the source, test, and generated files**

Use commit message `refactor(mvp): remove landing zone role delegation`. Do not push `OperationsAdvisory-updates2`.

### Task 4: Certify in protected order

**Files:**
- Certification PR 1: `op01_manage_landing_zone_environment/generated/iam.json`
- Certification PR 2: `op00_manage_global_landing_zone/generated/iam.json`

- [ ] **Step 1: Obtain CRQ and explicit confirmation for OP01**

Present a plan showing the removal of the two policy resources and no resource creation. Create an OP01-only PR only after confirmation; wait for its protected workflow to succeed.

- [ ] **Step 2: Obtain explicit confirmation for OP00**

After OP01 succeeds, present a plan showing deletion of only the two verified-empty groups. Create an OP00-only PR only after confirmation; wait for its protected workflow to succeed.

- [ ] **Step 3: Verify final OCI state read-only**

Confirm the nonexistent namespace is still absent; the two policies and two groups are absent; TBAC project tags remain; and no OP04 configuration changes occurred.
