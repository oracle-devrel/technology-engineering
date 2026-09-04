# Request lifecycle

These rules apply whether you use the GitHub interface, optional UI, or optional
Codex plugin.

## Before you begin

Confirm that you have write access to the handed-off `nonprod-<project>` or
`prod-<project>` repository and that
`environments/<environment>/environment_information.md` is complete for the
selected cloud. Blank handoff sections cannot be used. Azure and Google Cloud
requests require their reviewed foundation references in that file.

Check that the request appears in [what MCCP supports](../reference/support.md).

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
4. Represent required secrets with an environment-qualified placeholder such
   as `__DEV_ADB_ADMIN_PASSWORD__`. Never put a secret value in Git.
5. For a resource request, merge the catalog entry into the existing regional
   file. Replace `{}` for the first entry; do not create another file for the
   same configuration group, because Terraform does not deep-merge repeated root
   values. [Manifest paths](#manifest-paths) lists the file for each request.
6. Validate the edited JSON before opening the pull request.

OCI project network security groups (NSGs) must exist before an OCI Compute
request refers to their names.

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
- the diff contains no secret values, only environment-qualified placeholders
  such as `__DEV_ADB_ADMIN_PASSWORD__`;
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
- For an OCI Autonomous Database lifecycle request created with the Codex
  plugin, replace the canonical lifecycle file with `{}`. The Codex plugin does
  not support the OCI Compute `deploy-agent` operation.

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
| Unresolved secret placeholder | Ask Cloud Operations to add the matching key to the selected environment bundle. Do not commit the value. |
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

Keep one file for each configuration group in a project and region. Terraform
does not deep-merge repeated root values across multiple files.
