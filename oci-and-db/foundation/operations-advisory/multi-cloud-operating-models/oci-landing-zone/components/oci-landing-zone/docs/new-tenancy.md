# New tenancy setup

This checklist takes a new OCI tenancy from initial administrative access to the
first project handoff.

## 1. Prepare the bootstrap boundary

The first Bootstrap apply cannot run on the runner it creates. Before starting,
an OCI administrator must provide:

- A temporary repository-scoped Linux GitHub Actions runner with Git and
  outbound HTTPS access.
- A temporary dynamic group and Instance Principal policy for that runner, with
  permission to create the Bootstrap compartment, network, compute instance,
  dynamic group, root policy, and state objects.
- An OCI Object Storage bucket for Terraform state.
- A private GitHub repository containing this prepared configuration.

Use an OCI API-key profile only to create and verify this temporary boundary.
Before creating any resource, verify it returns the intended tenancy:

```bash
export OCI_CLI_PROFILE=cloudopstenancy
export TARGET_TENANCY_OCID='<target-tenancy-ocid>'
oci iam tenancy get --profile "$OCI_CLI_PROFILE" \
  --tenancy-id "$TARGET_TENANCY_OCID" \
  --query 'data.{name:name,id:id,home_region_key:"home-region-key"}' \
  --output table
```

Stop on `401 NotAuthenticated`; repair the API-key profile before proceeding.
Never copy the API key into GitHub Actions secrets or runner configuration. The
workflow itself uses the temporary runner's Instance Principal identity. A
short-lived GitHub runner registration token registers the runner only; it is
not OCI authentication.

Review `bootstrap/` and replace every example value. In particular, confirm the
target region, image OCID, CIDRs, SSH public key, names, and the scope of
`pcy-bootstrap`. The supplied policy is broad enough to establish the Landing
Zone; narrow it when your operating model permits. The GitHub workflow installs
its pinned Terraform 1.12.1 release; a local Terraform installation is needed
only if the temporary host will perform an approved local verification.

Run the Bootstrap configuration through the reviewed GitHub workflow on the
temporary runner, using the OCI orchestrator commit pinned by this installation.
Save the reviewed plan before apply. Retain the temporary runner and state until
state is safely stored in the OCI bucket and recovery has been tested.

Bootstrap is deliberately a two-pass operation:

1. The first reviewed Bootstrap PR creates the Bootstrap compartment, network,
   and permanent runner. The dynamic-group and policy file remains disabled.
2. Obtain the newly created Bootstrap compartment OCID from the reviewed state
   output. Rename
   `oci_open_lz_one-oe_bootstrap_runner_iam.auto.tfvars.json.disabled` to end
   in `.json`, replace `__BOOTSTRAP_COMPARTMENT_OCID__`, and open a second
   reviewed Bootstrap PR. It adds the permanent runner's dynamic group and
   policy without recreating the first-pass resources.

The OCI dynamic-group API requires a literal compartment OCID in its matching
rule, so this sequence is required; do not substitute a guessed value or enable
the second file during the first pass.

## 2. Activate the permanent runner

After Bootstrap succeeds:

1. Complete the GitHub Actions runner registration on the new VM.
2. Install Git, Terraform 1.12.1, and the tools required by your workflows.
3. Confirm the instance matches the Bootstrap dynamic group.
4. Confirm Instance Principal can read and write only the required state and
   perform the next phase's OCI operations. Allow IAM propagation after the
   second Bootstrap pass before running this test.
5. Configure `OCI_TF_STATE_BUCKET`, `OCI_TF_STATE_NAMESPACE`, `REGION`, and
   `OCI_TENANCY_OCID` as repository variables.
6. Run a non-destructive state access test before removing temporary bootstrap
   access.

## 3. Deploy the foundation

For OP00, OP01, OP02, OP03, and OP04, use the same control loop:

1. Change only the target phase.
2. Open a pull request and review its Terraform plan.
3. Obtain independent approval.
4. Merge and verify the workflow and OCI outcome.

Run the phases in order. OP03 is required only when the GitOps platform is
hosted in this tenancy. Repeat OP02 for each approved environment and OP04 for
each project.

OP02 is complete when `project-onboarding-environment.json` identifies the
expected environment, VCN, and role-based subnets. OP04 is complete when its
workflow produces both handoff files with the expected project and provenance.

## 4. Hand off the project

Provide `project-foundation-handoff.json` to the Control Plane administrator and
`environment_information.md` to the project team. Do not add credentials or
secrets. Keep the files with the approved onboarding record.

If any phase fails, stop. Compare OCI with Terraform state before submitting a
corrective pull request; do not edit state manually or bypass the review gate.
