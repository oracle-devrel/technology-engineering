# Day-to-day operations

Every infrastructure request follows the same governed process:

1. Choose an approved catalog entry.
2. Update the project's regional JSON manifest on a focused branch.
3. Open a pull request.
4. Review the Terraform plan or Ansible check for the current change.
5. Obtain human approval and merge; enforce independent approval on paid plans.
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
Currently supported operations are OCI Autonomous Database start/stop, the OCI
Compute `deploy-agent` example, and the non-production OCI ExaCS regular
database out-of-place patch operation.

## ExaCS regular database out-of-place patch

`exacs-database-out-of-place-patch` moves one regular Oracle Database on
Exadata Database Service on Cloud@Customer to one approved, already-patched
Database Home through the OCI Database API. It is not an Autonomous Database
operation and it does not use SSH, `dbaascli`, or OCI CLI.

The platform team registers externally deployed ExaCS databases during handoff
in `environments/{environment}/exacs-databases.json`. The registry is
platform-owned and records the database identity, compartment, VM cluster, and
approved target Database Homes. Project teams must not edit it. A request is
rejected unless its display name and target Database Home/version match that
registry. This lets the operation support databases that were not deployed by
Terraform without accepting an arbitrary database OCID in a project request.

The platform team adds an entry only after verifying the resource boundary:

```json
{
  "schema_version": 1,
  "databases": [
    {
      "display_name": "orders-cdb",
      "database_id": "ocid1.database.oc1.eu-frankfurt-1.example",
      "compartment_id": "ocid1.compartment.oc1..example",
      "vm_cluster_id": "ocid1.vmcluster.oc1.eu-frankfurt-1.example",
      "approved_target_db_homes": [
        {
          "id": "ocid1.dbhome.oc1.eu-frankfurt-1.example",
          "db_version": "19.28.0.0.0"
        }
      ]
    }
  ]
}
```

The registry must be an independent, platform-approved change before a project
team can request the move. It must not be changed in the operation pull request.

The pull-request workflow calls OCI `precheck`; merge calls OCI `upgrade` with
`DB_HOME` as the source, which moves the database to the approved target home.
The operation is deliberately limited to one database per request. A failed
move is not rolled back automatically; the platform team must assess the OCI
work request and current state before using the supported OCI recovery process.

Troubleshooting: unresolved runtime placeholders mean the selected repository
secret bundle is missing a matching key. A placeholder that does not start with
the selected uppercase environment is rejected before Terraform. Missing
catalog-rendering values instead indicate incomplete handoff data. State-backed
Day 2 targets must use the exact display name recorded in Terraform state; the
ExaCS patch operation uses the platform-owned ExaCS registry instead. Keep one
region per pull request; the shared
resolver rejects a mixed environment or region request. Paths outside this table
are rejected. Missing runner labels are a platform configuration issue, and
missing handoff data must be corrected by the platform team before a request is
prepared.

Never commit passwords or credentials. If a deployment fails, retain the logs,
confirm the state of the resource and Terraform state, and submit a reviewed
corrective change. Do not edit state manually or retry with a personal cloud
account.
