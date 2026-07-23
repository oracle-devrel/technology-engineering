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

The generated OP01 final security configuration intentionally omits the
OE `v3.1.0` `SZ-TGT-LZ-SHARED-NETWORK-KEY` child target. OCI requires a Compute
instance and its subnet to belong to the same Security Zone. The shared network
and platform hierarchies instead inherit the common parent CIS zone. Do not
restore a child-specific network zone unless the upstream template has been
fixed or every dependent platform resource is placed under that same zone.

The Hub management security list must allow SSH only from the platform
Bastion's current private endpoint `/32`. Retrieve that address from OCI,
record it in `config/customer.jsonnet` as
`platform_bastion_private_endpoint_cidr`, regenerate OP01, and review the
focused network plan. A `null` value removes OE's non-authoritative example
rule and fails closed. Recreate this focused change whenever the Bastion
endpoint is replaced.

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

An idempotency plan can recreate `local_file.*_output` resources because the
runner workspace is temporary. Those files are the Orchestrator's dependency
JSON artifacts, not OCI resources.

The official Observability module has one known normalization exception for an
Object Storage Service Connector target. OCI does not return
`target.compartment_id`, while the module supplies it again on every plan. The
same behavior is recorded in upstream
[issue 17](https://github.com/oci-landing-zones/terraform-oci-modules-observability/issues/17),
which was closed as not planned and is still present in the module used by
Orchestrator release 2.1.4.

For an unchanged OP01 final configuration, accept repeatability evidence only
when the complete plan contains:

- ephemeral `local_file.*_output` creates;
- at most the single in-place
  `oci_sch_service_connector` update that adds only
  `target.compartment_id`; and
- no other OCI changes, replacements, or destroys.

Close an idempotency-only pull request without merging it. If the connector
diff changes any other field, or any other OCI resource changes, stop and
investigate. Do not patch the downloaded official module or suppress broader
changes with `ignore_changes`.

After OP04, use `project-foundation-handoff.json` for machine processing and
`environment_information.md` for people. The workflow does not create or write to
a project repository. The three workload-role compartment values intentionally
contain the same official OE project compartment OCID.
