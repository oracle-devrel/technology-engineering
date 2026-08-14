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
   same configuration group.
6. Validate the edited JSON before opening the pull request.

OCI project network security groups (NSGs) must exist before an OCI Compute
request refers to their names.

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

## Review and execute

1. Create a focused branch and open a pull request.
2. Review the Terraform plan or Ansible check for only the intended change.
3. Obtain the required human approval.
4. Merge through the governed process.
5. Verify the post-merge workflow and cloud outcome.

Project Teams never receive deployment credentials. The trusted runner applies
the merged change with its managed cloud identity.

## Complete or remove a request

An operation file records one completed action; it is not desired state. Delete
it in a focused pull request after verifying the result. Deleting the file does
not reverse the operation.

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
