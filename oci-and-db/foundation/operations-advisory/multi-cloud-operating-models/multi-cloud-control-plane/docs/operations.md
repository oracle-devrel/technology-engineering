# Day-to-day operations

Every infrastructure request follows the same governed process:

1. Choose an approved catalog entry.
2. Update the project's regional JSON manifest on a focused branch.
3. Open a pull request.
4. Review the Terraform plan or Ansible check for the current change.
5. Obtain independent approval and merge.
6. Verify the workflow result and cloud outcome.

## Manifest paths

Use these standard locations (this is the canonical path table):

| Request | Location |
|---|---|
| OCI project NSGs | `oci/{environment}/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{environment}/{region}/database/database.json` |
| OCI Compute | `oci/{environment}/{region}/compute/compute.json` |
| Google ADB-S | `gcp/{environment}/{region}/workloads/adb.json` |
| Lifecycle operation | `{cloud}/{environment}/{region}/lifecycle_operations/{operation}.json` |

Keep one file for each Terraform configuration group in a project and region.
Splitting the same group across files can cause values to be ignored because
Terraform does not deep-merge variable files.

Lifecycle requests identify the operation and target resource by display name.
Currently supported operations are OCI Autonomous Database start/stop and the
OCI Compute `deploy-agent` example.

Troubleshooting: unresolved `__PLACEHOLDER__` values mean the mapped secret or
handoff suggestion is missing. A Day 2 target must use the exact display name
recorded in Terraform state. Keep one region per pull request; the shared
resolver rejects a mixed environment or region request. Paths outside this table
are rejected. Missing runner labels are a platform configuration issue, and
missing handoff data must be corrected by the platform team before a request is
prepared.

Never commit passwords or credentials. If a deployment fails, retain the logs,
confirm the state of the resource and Terraform state, and submit a reviewed
corrective change. Do not edit state manually or retry with a personal cloud
account.
