# Resource catalog

Terraform variable templates consumed by MCCP. Project Teams render these
catalog files into project repository manifests; `platform-ci` passes the
reviewed manifests to the selected orchestrator as Terraform `-var-file`
inputs.

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
    compute/              — Google Cloud virtual machines
    databases/            — Oracle ADB-S on Google Cloud
```

## Templates

### OCI — network

**`project_nsgs_template.auto.tfvars.json`**
Defines exactly one generic project NSG under `network_configuration.inject_into_existing_vcns`. Render `__NSG_KEY__`, `__NSG_DISPLAY_NAME__`, `__NSG_COMPARTMENT_OCID__`, and `__NSG_TIER__`, then merge only that entry into `oci/<environment>/<region>/network/project-nsgs.json`. `__NSG_COMPARTMENT_OCID__` is the project compartment OCID from the selected environment handoff; it is not the shared network compartment. Add ingress or egress rules only from explicit approved intent. Workloads reference the rendered NSG key, not an OCID.

### OCI — compute

**`project_compute_template.auto.tfvars.json`**
Provisions exactly one generic OCI VM. Render `__VM_KEY__`, `__VM_NAME__`, `__VM_SUBNET_OCID__`, and `__VM_NSG_KEY__`; the NSG key must already exist in the regional project NSG manifest. `__PROJ_APP_CMP_OCID__` comes from the completed handoff. The SSH public-key path is platform-owned and must remain `/home/github-runner/.ssh/oci_vm_key.pub`. The Frankfurt template pins the certified `Oracle-Linux-9.8-aarch64-2026.07.20-0` image, compatible with `VM.Standard.A1.Flex`; confirm the image choice manually before approval and retain it unless the request explicitly supplies another regional image OCID. No OCI CLI lookup is required. Use a separately validated regional template outside Frankfurt.

### OCI — databases

**`project_database_template.auto.tfvars.json`**
Provisions OCI Autonomous Database Serverless through the current OCI Landing Zones Autonomous Database contract. Use `__PROJ_DB_SUBNET_OCID__` for the private DB subnet and `__NSG_DB_KEY__` for the DB-tier NSG. Render the catalog's `__ADB_ADMIN_PASSWORD__` as an environment-qualified runtime token, such as `__DEV_ADB_ADMIN_PASSWORD__`, and add the corresponding key to that environment's project-repository secret bundle. Use one mapping key per ADB when deploying multiple databases. If an ADB needs a dedicated NSG, define that NSG in `oci/<environment>/<region>/network/project-nsgs.json` and reference its key in `networking.network_security_groups`. The catalog intentionally sets `is_dedicated` to `false`; ADB Dedicated requires an existing Autonomous Container Database and is not a project self-service request in this release.

### Azure — compute

**`project_compute_template.auto.tfvars.json`**
Provisions exactly one private Ubuntu 22.04 LTS Gen2 VM using handed-off resource-group, subnet, and NSG references. Public-IP fields are not part of the contract.

### Azure — databases

**`project_oracle_adb_template.auto.tfvars.json`**
Provisions exactly one Oracle ADB@Azure instance using handed-off resource-group, VNet, and delegated-subnet references. Render `__AZURE_ADB_ADMIN_PASSWORD__` as an environment-qualified runtime placeholder.

### Google — compute

**`project_compute_template.auto.tfvars.json`**
Provisions exactly one private Debian 12 VM using handed-off project, zone, subnetwork, and service-account references. Public-IP fields are not part of the contract.

### Google — databases

**`project_google_adbs_template.auto.tfvars.json`**
Provisions Oracle Autonomous Database Serverless on Google Cloud through `terraform-oci-multicloud-google`. The project repo must already have handoff values for the Google project, ODB Network, and client ODB Subnet. The template uses `properties.secret_id` for the admin password source; do not add literal passwords to Git.

## Placeholders

All placeholders follow the `__UPPER_SNAKE_CASE__` pattern. Committed runtime
secret placeholders must additionally begin with the selected environment,
such as `__DEV_`, `__TEST_`, `__UAT_`, or `__PROD_`.

Cross-template dependency: NSG/security-group placeholders in workload templates are string references, not OCIDs. Render them with a key that already exists in the corresponding project network manifest.

## Reference specifications

The JSON Schemas under [`schemas/`](schemas/README.md) are human-readable reference
contracts for the supported resource manifest shapes:

- [`adb.schema.json`](schemas/oci/adb.schema.json)
- [`compute.schema.json`](schemas/oci/compute.schema.json)
- [`nsg.schema.json`](schemas/oci/nsg.schema.json)
- [`azure/adb.schema.json`](schemas/azure/adb.schema.json)
- [`azure/compute.schema.json`](schemas/azure/compute.schema.json)
- [`gcp/adb.schema.json`](schemas/gcp/adb.schema.json)
- [`gcp/compute.schema.json`](schemas/gcp/compute.schema.json)

They are intentionally **reference-only** in the supplied release. They are not
loaded by GitHub Actions, `platform-ci`, or Terraform, so adding or updating
them does not change deployment behaviour. The authoritative runtime validation
remains the protected control-plane code and the pinned Terraform module
contracts. Use the schemas for human review, offline manifest checking, and as
the starting contract when designing a qualified extension; do not treat a
schema change as a deployment change.

## Security notes

- Don't commit real passwords. The `admin_password` fields are environment-qualified double-underscore placeholders resolved by `platform-ci` from exactly one explicitly selected project-repository secret bundle.
- Copy foundation references from the approved
  `environments/<environment>/environment_information.md` handoff; do not use
  them as Terraform credentials.

## Warranty disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND.
