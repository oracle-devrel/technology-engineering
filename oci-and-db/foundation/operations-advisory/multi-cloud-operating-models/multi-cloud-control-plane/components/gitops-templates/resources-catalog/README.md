# Resources Catalog (Day 0 / Day 1)

Terraform variable templates consumed by the GitOps control plane. The Project Admin UI or a project operator renders these catalog files into project repository manifests; `platform-ci` then passes those manifests to the selected orchestrator as Terraform `-var-file` inputs.

## Directory layout

```
resources-catalog/
  oci/
    network/              — OCI project NSGs for existing handoff VCNs
    compute/              — OCI compute instances
    databases/            — OCI Autonomous Database
  azure/
    compute/              — Azure virtual machines
    databases/            — Oracle ADB@Azure
  gcp/
    databases/            — Oracle ADB-S on Google Cloud
```

## Templates

### OCI — network

**`project_nsgs_template.auto.tfvars.json`**
Defines exactly one generic project NSG under `network_configuration.inject_into_existing_vcns`. Render `__NSG_KEY__`, `__NSG_DISPLAY_NAME__`, `__NSG_COMPARTMENT_OCID__`, and `__NSG_TIER__`, then merge only that entry into `oci/<region>/network/project-nsgs.json`. Add ingress or egress rules only from explicit approved intent. Workloads reference the rendered NSG key, not an OCID.

### OCI — compute

**`project_compute_template.auto.tfvars.json`**
Provisions exactly one generic OCI VM. Render `__VM_KEY__`, `__VM_NAME__`, `__VM_SUBNET_OCID__`, and `__VM_NSG_KEY__`; the NSG key must already exist in the regional project NSG manifest. `__PROJ_APP_CMP_OCID__` and `__DEFAULT_SSH_KEY__` come from the completed handoff. The `platform_image.ocid` is region-specific — use this template only for its approved Frankfurt image or publish a separately validated regional template.

### OCI — databases

**`project_database_template.auto.tfvars.json`**
Provisions OCI Autonomous Databases. Use `__PROJ_DB_SUBNET_OCID__` for the private DB subnet and `__NSG_DB_KEY__` for the DB-tier NSG. `admin_password` must be a runtime placeholder such as `__ADB_ADMIN_PASSWORD__`; create the matching project-repository GitHub Actions secret as `ADB_ADMIN_PASSWORD`. Use one secret per ADB when deploying multiple databases. If an ADB needs a dedicated NSG, define that NSG in `oci/<region>/network/project-nsgs.json` and reference its key in `nsg_ids`.

### Azure — compute

**`project_compute_template.auto.tfvars.json`**
Provisions exactly one generic Azure VM. References resources by key (`resource_group_key`, `network_key`, `subnet_key`, `security_group_key`) and defaults to no public IP. If a public IP is explicitly enabled, the template uses the supported `Standard` SKU.

### Azure — databases

**`project_oracle_adb_template.auto.tfvars.json`**
Provisions exactly one generic Oracle ADB@Azure instance with the smallest catalog defaults, private networking, and Bring Your Own License. The `subnet_key` must point to a delegated subnet (`Oracle.Database/networkAttachments`). Replace `__ADMIN_PASSWORD__` and `__DBA_EMAIL__` at runtime.

### Google — databases

**`project_google_adbs_template.auto.tfvars.json`**
Provisions Oracle Autonomous Database Serverless on Google Cloud through `terraform-oci-multicloud-google`. The project repo must already have handoff values for the Google project, ODB Network, and client ODB Subnet. The template uses `properties.secret_id` for the admin password source; do not add literal passwords to Git.

## Placeholders

All placeholders follow the `__UPPER_SNAKE_CASE__` pattern.

Cross-template dependency: NSG/security-group placeholders in workload templates are string references, not OCIDs. Render them with a key that already exists in the corresponding project network manifest.

## Security notes

- Don't commit real passwords. The `admin_password` fields are double-underscore placeholders resolved by `platform-ci` from inherited GitHub Actions secrets or runner environment variables.
- Store OP04 handoff references in `enviroment_information.md`, not as Terraform credentials.

## Warranty disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND.
