# ExaCS Day-2 inventory and CRQ manifests

## Purpose

Provide a reusable project-template contract for ExaCS Day-2 operations without
publishing OCI identifiers or using Terraform to manage DB Homes, CDBs, or PDBs.

## Boundaries

- `oci/<environment>/<region>/exadata/exadata.json` is Terraform desired
  configuration for Cloud Exadata Infrastructure and VM Cluster only.
- Terraform state is the inventory boundary for the adopted infrastructure and
  VM Cluster.
- `oci/<environment>/<region>/lifecycle_operations/crq-*.json` contains one
  immutable Day-2 request per CRQ. Adding one file invokes one Ansible operation.
- `inventory/oci/<environment>/<region>/exacs-databases.json` is a Git-tracked,
  observed inventory of DB Homes, CDBs, and PDBs. It is outside `oci/` so it is
  not a Terraform variable file and cannot trigger Terraform.

## Operation flow

1. A project team adds one CRQ manifest for one operation.
2. Ansible resolves the VM Cluster from Terraform state, then discovers the
   requested database resources through OCI by their logical names.
3. Ansible performs and verifies the operation.
4. Only after verification succeeds, it regenerates the observed inventory and
   updates its Git file.

The CRQ request remains unchanged for audit. Its workflow run records execution
status. A new change requires a new CRQ file.

## Safety rules

- A CRQ is never edited after execution.
- An OOP request must resolve one available database and one available target
  DB Home. Source and target DB Homes must be distinct.
- A failed operation does not update the observed inventory.
- The observed inventory is derived from OCI and is never used as an OCI-ID
  input to Terraform or Ansible.

## Template content

The project template supplies skeletons for DB Home creation, CDB creation, PDB
creation, and out-of-place patching. Values that are environment-specific use
the existing secret-placeholder convention; resource selection uses display
names only.
