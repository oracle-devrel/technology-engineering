# Day-to-day operations

Use one focused pull request for each foundation change. The pull request should
show the configuration change and its Terraform plan before approval.

Cloud Operators are responsible for:

- Maintaining tenancy IAM, shared networking, environments, and platform
  foundations.
- Creating each official OE project compartment, group, and policies through
  OP04.
- Reviewing plans for unexpected replacement, deletion, or privilege changes.
- Confirming state and OCI agree after each deployment.
- Providing the validated project handoff after OP04.

Project Teams must not modify foundation or OP04 configuration. They manage
project NSGs, workloads, and supported lifecycle operations in their project
repository.

If a plan or apply fails, retain the workflow logs and determine whether
Terraform state matches OCI before submitting a corrective pull request. Do not
edit state manually or bypass review with a local apply.

For a merged project change that failed only because a foundation dependency
was missing or ineffective, fix that dependency through a separately reviewed
foundation pull request. After confirming that project state contains no
partially created OCI resource, a human operator may rerun the exact failed
merge-commit job. Do not manufacture a no-op project commit or rerun a
different revision.

OCI automatically adds `Oracle-Tags.CreatedBy` and `Oracle-Tags.CreatedOn` to
new resources. The protected phase workflows ignore exactly those two
provider-managed keys during planning, preserving the tags and preventing
unchanged configurations from proposing their removal. Treat either removal
as a failed idempotency check and stop before merge.

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

The workflow publishes `environment_information.md` for people and
`project-foundation-handoff.json` for automated processing. Keep the Markdown
file at the machine contract's exact `handoff_path` in the target project
repository.
