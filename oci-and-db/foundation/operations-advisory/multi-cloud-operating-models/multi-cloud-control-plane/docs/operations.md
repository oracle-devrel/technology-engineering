# Day-to-day operations

Every infrastructure request follows the same governed process:

1. Choose an approved catalog entry.
2. Update the project's regional JSON manifest on a focused branch.
3. Open a pull request.
4. Review the Terraform plan or Ansible check for the current change.
5. Obtain independent approval and merge.
6. Verify the workflow result and cloud outcome.

Use these standard locations:

| Request | Location |
|---|---|
| OCI project NSGs | `oci/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{region}/database/database.json` |
| OCI Compute | `oci/{region}/compute/compute.json` |
| Google ADB-S | `gcp/{region}/workloads/adb.json` |
| Lifecycle operation | `{cloud}/{region}/lifecycle_operations/{operation}.json` |

Keep one file for each Terraform configuration group in a project and region.
Splitting the same group across files can cause values to be ignored because
Terraform does not deep-merge variable files.

Lifecycle requests identify the operation and target resource by display name.
Currently supported operations are OCI Autonomous Database start/stop and the
OCI Compute `deploy-agent` example.

Never commit passwords or credentials. If a deployment fails, retain the logs,
confirm the state of the resource and Terraform state, and submit a reviewed
corrective change. Do not edit state manually or retry with a personal cloud
account.
