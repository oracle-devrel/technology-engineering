# Request lifecycle

These rules apply whether you use the GitHub interface, optional UI, or optional
Codex plugin.

## Before you begin

Confirm that you have write access to the handed-off `nonprod-<project>` or
`prod-<project>` repository and that
`environments/<environment>/environment_information.md` is complete for the
selected cloud. Blank handoff sections cannot be used. Azure and Google Cloud
requests require their reviewed foundation references in that file.

Check that the request appears in [Reference capabilities](../reference/support.md).

Record a change reference such as `CRQ1234` in the pull request before review.
This is a procedural convention for traceability: no workflow validates it. The
Codex plugin does require the `CRQ[0-9]{1,20}` form before it prepares a Git
change; the optional UI treats the field as optional and accepts any reference
your change process uses.

## Prepare the request

1. Choose a resource template from the installed
   [resource catalog](../../repository-sources/gitops-templates/resources-catalog/README.md)
   or a lifecycle template from the
   [operation catalog](../../repository-sources/gitops-templates/operations-catalog/README.md).
2. Change exactly one cloud, environment, and region in each pull request.
3. Copy compartments, networks, subnets, and other foundation references from
   the selected environment handoff. Do not invent or replace them.
4. Represent required secrets with environment-qualified placeholders. Each OCI
   ADB must have its own database-scoped administrator-password token, for
   example `__DEV_ORDERSADB_ADMIN_PASSWORD__`; never reuse that token for a
   second database. The Project Team adds and rotates the matching
   `DEV_ORDERSADB_ADMIN_PASSWORD` member in its selected environment secret
   bundle through the approved secret process; never put a secret value in Git.
5. For a resource request, merge the catalog entry into the existing regional
   file. Replace `{}` for the first entry; do not create another file for the
   same configuration group, because Terraform does not deep-merge repeated root
   values. [Manifest paths](#manifest-paths) lists the file for each request.
6. Validate the edited JSON before opening the pull request.

OCI project network security groups (NSGs) must exist before an OCI Compute
request refers to their names. The catalog provides separate ingress and egress
rule capabilities for an existing project NSG. State the source or destination,
its type, and destination-port range explicitly. The supplied capabilities are
TCP-only and set the catalog protocol value themselves. A public ingress source
(`0.0.0.0/0`) is allowed only when the request explicitly requires it; the
pull-request preview and review must identify that exposure.

## Review and execute

1. Create a focused branch and open a pull request.
2. Review the Terraform plan or Ansible check for only the intended change.
3. Obtain the required human approval.
4. Merge through the governed process.
5. Verify the post-merge workflow and cloud outcome.

Project Teams never receive deployment credentials. The trusted runner applies
the merged change with its managed cloud identity.

## What a reviewer checks

On the supplied GitHub Free profile the approval is procedural, so this review is
the governance boundary. Before approving, confirm that:

- the pull request changes exactly one cloud, environment, and region;
- every compartment, network, subnet, and project reference matches the
  environment handoff for that environment;
- every NSG rule uses the approved catalog shape and its source or destination,
  TCP port range are the intended ones; any `0.0.0.0/0` ingress is explicitly
  approved as public exposure;
- the diff contains no secret values, and each OCI ADB uses its own
  environment- and database-qualified password placeholder;
- the Terraform plan or Ansible check shows only the intended change, and it ran
  against the current head commit;
- the change reference is recorded, if your change process requires one; and
- you are not the author of the change.

Reject the request rather than approving conditionally. The runner applies what
was merged.

## Complete or remove a request

An operation file records one completed action; it is not desired state. After
verifying the result, clear it using the route that created the request:

- For the GitHub interface, including cleanup after an optional-UI request,
  delete the lifecycle file in a focused pull request. The workflow accepts the
  removal and does not execute another operation.
- For an OCI lifecycle request created with the Codex plugin, delete the
  selected lifecycle file in its focused pull request.

Neither cleanup method reverses the completed operation.

To remove a resource, delete only the selected entry. If it is the final entry,
replace the entire regional file with:

```json
{}
```

Confirm that the plan deletes only the intended resource. Never edit Terraform
state manually or retry with a personal cloud account.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Unresolved secret placeholder | Ask the Project Team to add and rotate the matching environment- and database-scoped key in the selected environment bundle through the approved secret process. Do not commit the value. |
| Incomplete handoff value | Ask Cloud Operations to correct the environment handoff. |
| Operation target not found | Use the exact resource display name recorded in Terraform state. |
| Mixed environment or region rejected | Keep one cloud/environment/region tuple in the pull request. |
| Missing runner label | Ask Cloud Operations to correct the runner configuration. |
| Deployment failure | Retain the logs, check the resource and state outcome, and submit a reviewed corrective change. |

## Manifest paths

| Request | Location |
| --- | --- |
| OCI project NSGs | `oci/{environment}/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{environment}/{region}/database/database.json` |
| OCI Compute | `oci/{environment}/{region}/compute/compute.json` |
| Azure private VM | `azure/{environment}/{region}/compute/compute.json` |
| Azure Autonomous Database | `azure/{environment}/{region}/database/database.json` |
| Google private VM | `gcp/{environment}/{region}/compute/compute.json` |
| Google Autonomous Database Serverless | `gcp/{environment}/{region}/workloads/adb.json` |
| OCI lifecycle operation | `oci/{environment}/{region}/lifecycle_operations/{operation}.json` |
