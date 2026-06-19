# Module: dbm-opsi-enablement

Declarative, modular enablement of OCI **Database Management** and **Operations
Insights** for already-provisioned OCI-native databases (DBCS CDB/PDB). Designed
for Resource Manager (ORM) and CI so a POC/demo stack comes up end-to-end.

Each capability is independently toggled and driven by `for_each` over a
`targets` map — adding a target or turning a feature off is a no-destroy change
to the others. New capabilities are added as new, independently-gated blocks.

## What it creates

| Resource | Purpose | Toggle |
|---|---|---|
| `oci_database_management_database_dbm_features_management` | DBM (DIAGNOSTICS_AND_MANAGEMENT, ADVANCED) over the DBM PE | `enable_database_management` |
| `oci_database_management_named_credential` | Vault-backed RESOURCE_PRINCIPAL credential for advanced diagnostics | `set_preferred_credentials` |
| `null_resource.preferred_credential` (oci CLI) | Wire `PC_READ`/`PC_WRITE` to the named credential (no TF resource exists for this) | `set_preferred_credentials` |
| `oci_opsi_database_insight` | OPSI PE co-managed Database Insight | `enable_ops_insights` |
| `oci_data_safe_target_database` | Data Safe target registration over the Data Safe PE (security pillar) | `enable_data_safe` |

Data Safe needs `data_safe_private_endpoint_id`, each target's `db_system_id`, and
`data_safe_password` (plaintext — the API takes a password, not a Vault secret, so
it lands in state; pass via `TF_VAR_data_safe_password` and keep state restricted).

## Usage

```hcl
module "observability" {
  source = "../../modules/dbm-opsi-enablement"

  compartment_id           = var.compartment_id
  dbm_private_endpoint_id  = var.dbm_private_endpoint_id
  opsi_private_endpoint_id = var.opsi_private_endpoint_id
  password_secret_id       = var.dbsnmp_secret_id
  monitoring_user          = "DBSNMP"

  targets = {
    cdb = {
      database_id            = var.cdb_ocid
      database_role          = "CDB"
      database_resource_type = "database"
      service_name           = "<db_unique_name>.<db_domain>" # REAL listener service, not the bare DB name
      host_ip                = var.db_node_private_ip
    }
    pdb1 = {
      database_id            = var.pdb_ocid
      database_role          = "PDB"
      database_resource_type = "pluggabledatabase"
      service_name           = "<pdb_name>.<db_domain>"
      host_ip                = var.db_node_private_ip
    }
  }
}
```

## Prerequisites (must exist before this module)

- DBM + OPSI private endpoints, reachable from the DB subnet on 1521.
- The monitoring user (DBSNMP) **unlocked, on a non-locking profile**, with a
  password that matches the Vault secret (see the CLI `enable` / KB for the
  `C##DBSNMP_MON` profile and credential-sync steps). Rotating DBSNMP without this
  causes an ORA-28000 lock loop.
- `service_name` set to the real listener service (`lsnrctl status`), not the bare
  DB/PDB name (ORA-12514 otherwise).
- The `oci` CLI on the apply runner (Cloud Shell / ORM) authenticated to the same
  tenancy — used for the preferred-credential step.
- IAM: `Allow any-user to read secret-family in compartment <C> where ALL
  {target.secret.id='<secret>', request.principal.type='dbmgmtmanageddatabase'}`.

## Status & verification

`terraform validate` passes (resource types and arguments are schema-correct
against the `oracle/oci` provider). **Apply-test in a scratch tenancy before
production** — enum values (`deployment_type`, `database_resource_type`) and the
OPSI connection shape should be confirmed against your DB. The verified,
self-healing path today is the `dbman-opsi` CLI (`enable --apply`, which reconciles
DBM, skips already-ACTIVE OPSI insights, and sets preferred credentials); this
module mirrors that for teams that prefer pure Terraform/ORM.
