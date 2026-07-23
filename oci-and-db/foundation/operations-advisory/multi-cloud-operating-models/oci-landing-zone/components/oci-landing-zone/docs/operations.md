# Phase operations

Use this page to find the configuration and success condition for each phase.

| Phase | Configuration | Successful outcome |
|---|---|---|
| Bootstrap readiness | `.github/workflows/oci-bootstrap-readiness.yaml` | Private foundation runner identity, required tools, and read-only state access are verified |
| OP00 | `op00_manage_global_landing_zone/` | Approved tenancy-wide groups and policies exist |
| OP01 | `op01_manage_landing_zone_environment/` | Shared compartments, network, governance, and security match the plan |
| OP02 | `op02_manage_environment/{environment}/` | Environment resources exist and `project-onboarding-environment.json` is validated |
| OP03 | `op03_manage_platform_gitops/` | Required platform IAM, network, and compute exist |
| OP04 | `op04_manage_project/{environment}/{project}/` | Official OE project compartment, group, policies, and both handoff files exist |

OP03 is optional when the platform is hosted elsewhere. OP02 repeats per
environment. OP04 accepts one project target per run and remains a Cloud
Operator operation.

## Standard change procedure

1. Confirm the earlier phase outputs and state are healthy.
2. Edit the protected source configuration and generate only the selected
   phase with `scripts/generate_foundation.sh`.
3. Open a pull request and review the exact Terraform plan.
4. Check replacements, deletions, IAM scope, routes, CIDRs, and state key.
5. Obtain independent approval, merge, and verify the workflow result in OCI.

If a plan or apply fails, retain its logs and reconcile OCI with Terraform state
before retrying. Never repair the failure with an unreviewed local apply or a
manual state edit.

An unchanged configuration should not propose updates that remove
`Oracle-Tags.CreatedBy` or `Oracle-Tags.CreatedOn`. OCI adds those automatic
default tags after resource creation. The phase workflows use the OCI
provider's `ignore_defined_tags` setting for exactly those two keys so a later
apply preserves them and remains idempotent. If either tag appears as a
removal in a plan, stop before merge and verify that the protected workflow
still contains that provider setting.

After OP04, use `project-foundation-handoff.json` for machine processing and
`environment_information.md` for people. The workflow does not create or write to
a project repository. The three workload-role compartment values intentionally
contain the same official OE project compartment OCID.
