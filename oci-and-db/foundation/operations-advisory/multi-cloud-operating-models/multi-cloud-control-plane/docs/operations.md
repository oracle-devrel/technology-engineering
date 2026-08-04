# Day-to-day operations

Every infrastructure request follows the same governed process:

1. Choose an approved catalog entry.
2. Update the project's regional JSON manifest on a focused branch.
3. Open a pull request.
4. Review the Terraform plan or Ansible check for the current change.
5. Obtain human approval and merge; enforce independent approval on paid plans.
6. Verify the workflow result and cloud outcome.

## Manifest paths

Use these canonical locations for the supplied baseline:

| Request | Location |
|---|---|
| OCI project NSGs | `oci/{environment}/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{environment}/{region}/database/database.json` |
| OCI Compute | `oci/{environment}/{region}/compute/compute.json` |
| Azure private VM | `azure/{environment}/{region}/compute/compute.json` |
| Azure Autonomous Database | `azure/{environment}/{region}/database/database.json` |
| Google private VM | `gcp/{environment}/{region}/compute/compute.json` |
| Google ADB-S | `gcp/{environment}/{region}/workloads/adb.json` |
| OCI lifecycle operation | `oci/{environment}/{region}/lifecycle_operations/{operation}.json` |

Project Teams use only installed catalog entries and approved paths. A customer
extension must add its reviewed path and validation before use; the required
implementation layers are defined in the
[architecture extension model](architecture.md#extension-model).

Azure and Google manifests contain only workload declarations and direct
handed-off references. Their adapters never create foundation resources, and
VM manifests have no public-IP fields.

Keep one file for each Terraform configuration group in a project and region.
Splitting the same group across files can cause values to be ignored because
Terraform does not deep-merge variable files.

Lifecycle requests identify the operation and target resource by display name.
The supplied, currently implemented reference examples are OCI Autonomous
Database start/stop and OCI Compute `deploy-agent`. Azure and Google Day 2
operations are not included in the supplied baseline.

A lifecycle manifest records one completed request; it is not desired state.
After verifying the operation, delete that manifest in a focused pull request.
The workflow validates that the deleted path was one existing lifecycle
manifest and skips Ansible on both the pull request and merge. Deleting the
manifest does not reverse the completed cloud operation.

Troubleshooting: unresolved runtime placeholders mean the selected repository
secret bundle is missing a matching key. A placeholder that does not start with
the selected uppercase environment is rejected before Terraform. Missing
catalog-rendering values instead indicate incomplete handoff data. Day 2
targets must use the exact display name recorded in Terraform state. Keep one
region per pull request; the shared resolver rejects a mixed environment or
region request. Paths outside this table are rejected unless they belong to an
installed, qualified extension. Missing runner labels are a platform
configuration issue, and missing handoff data must be corrected by the platform
team before a request is prepared.

Never commit passwords or credentials. If a deployment fails, retain the logs,
confirm the state of the resource and Terraform state, and submit a reviewed
corrective change. Do not edit state manually or retry with a personal cloud
account.
