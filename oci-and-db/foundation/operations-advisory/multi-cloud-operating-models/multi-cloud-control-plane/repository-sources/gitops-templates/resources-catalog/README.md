# Resource catalog

Terraform variable templates consumed by MCCP. Project Teams render these catalog files into project repository manifests; `platform-ci` passes the reviewed manifests to the selected orchestrator as Terraform `-var-file` inputs.

Each template is an exact structural contract. Replace only documented placeholders and preserve literal keys, values, types, and collections. Populate a collection only when the template supplies an entry shape for it; an empty collection with no entry template authorizes zero entries. A requested field or rule absent from the template is not self-service and requires a reviewed catalog extension.

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

**`project_nsgs_template.json`** Defines exactly one generic project NSG under `network_configuration.inject_into_existing_vcns`. Render `__NSG_KEY__`, `__NSG_DISPLAY_NAME__`, `__NSG_COMPARTMENT_OCID__`, and `__NSG_TIER__`, then merge only that entry into `oci/<environment>/<region>/network/project-nsgs.json`. `__NSG_COMPARTMENT_OCID__` is the project compartment OCID from the selected environment handoff; it is not the shared network compartment. It contains one reusable TCP ingress-rule pattern and one reusable TCP egress-rule pattern inside the NSG entry. They are optional child fragments, not rules that every NSG must create: render zero or more only when requested. A later rule request uses the same child pattern and merges it into the selected existing project NSG. Within one regional manifest, each VCN key must occur once; merge into its existing category rather than adding a second VCN block. Workloads reference the rendered NSG key, not an OCID.

The approved rule inputs are rule key, description, source or destination and its type, and a destination-port range. `protocol` is the literal catalog value `TCP`; Project Teams never provide a provider number such as `6`. For ingress, use `src` and `src_type`; for egress, use `dst` and `dst_type`. The port fields are directly `dst_port_min` and `dst_port_max`, not nested `tcp_options`. Provide a complete integer port range. The template deliberately does not expose provider blocks, Terraform expressions, lifecycle settings, or any foundation network resource. Typical types are `CIDR_BLOCK`, `NETWORK_SECURITY_GROUP`, or `SERVICE_CIDR_BLOCK`, where supported by the selected OCI Landing Zone contract. `0.0.0.0/0` is permitted only when the request explicitly asks for public exposure; it must never be inferred. The request preview must state that exposure plainly.

### OCI — compute

**`project_compute_small_template.json`**, **`project_compute_medium_template.json`**, and **`project_compute_large_template.json`** Provisions exactly one approved OCI VM profile. The profiles use the same private Frankfurt image, `VM.Standard.A1.Flex`, 50 GB boot volume, CIS level, and platform-owned SSH public-key path. They differ only in their fixed capacity: Small is 1 OCPU / 6 GB, Medium is 2 OCPUs / 12 GB, and Large is 4 OCPUs / 24 GB. Render `__VM_KEY__`, `__VM_NAME__`, `__VM_SUBNET_OCID__`, and `__VM_NSG_KEY__`; the NSG key must already exist in the regional project NSG manifest. `__PROJ_APP_CMP_OCID__` comes from the completed handoff. Do not override a profile's shape, capacity, image, boot volume, or SSH key path. Use a separately validated regional profile outside Frankfurt.

### OCI — databases

**`adb-small-byol.json`**, **`adb-medium-byol.json`**, and **`adb-large-byol.json`** Provision OCI Autonomous Database Serverless through the current OCI Landing Zones Autonomous Database contract. The fixed BYOL profiles are Small (2 ECPUs / 32 GB), Medium (4 ECPUs / 64 GB), and Large (8 ECPUs / 128 GB). They retain private endpoints and disabled compute and storage auto-scaling. Use `__PROJ_DB_SUBNET_OCID__` for the private DB subnet and `__NSG_DB_KEY__` for the DB-tier NSG. Render `__ADB_ADMIN_PASSWORD_SECRET_OCID__` as an existing OCI Vault secret OCID in `admin_password_secret_id`. Use a distinct secret for each database in the selected project/environment and deployment region; the official module reads its current version with Instance Principal. Never put a password or runtime password token in this field. If an ADB needs a dedicated NSG, define that NSG in `oci/<environment>/<region>/network/project-nsgs.json` and reference its key in `networking.network_security_groups`. The catalog intentionally fixes `is_dedicated` to `false`; ADB Dedicated, different license models, and unlisted capacities are not project self-service requests in this release.

### Azure — compute

**`project_compute_template.json`** Provisions exactly one private Ubuntu 22.04 LTS Gen2 VM using existing approved resource-group, subnet and NSG references supplied in the request or relevant resource JSON. Azure Markdown is optional context; subscription and authentication stay on the runner. Public-IP fields are not part of the contract.

### Azure — databases

**`adb-small-byol.json`**, **`adb-medium-byol.json`**, and **`adb-large-byol.json`** provision the private Oracle ADB@Azure profiles. Their public mTLS variants use the same names with `-public-mtls` before `-byol`. All profiles use OLTP, Oracle Database 19c, and BYOL. Capacity is fixed by the selected template:

| Size | Base ECPUs | Storage | Private template | Public mTLS template |
| --- | --- | --- | --- | --- |
| Small | 2 | 1 TB | `adb-small-byol.json` | `adb-small-public-mtls-byol.json` |
| Medium | 4 | 2 TB | `adb-medium-byol.json` | `adb-medium-public-mtls-byol.json` |
| Large | 8 | 4 TB | `adb-large-byol.json` | `adb-large-public-mtls-byol.json` |

Do not override a profile's compute, storage, workload, database version, or license values. Azure retains the existing official module defaults: CPU auto-scaling is enabled and storage auto-scaling is disabled. The ECPU values above are the base capacity, not a fixed maximum. This differs from the OCI profiles, which disable both forms of auto-scaling.

Render `__ADB_ADMIN_PASSWORD_SECRET_OCID__` as an existing OCI Vault secret OCID in `admin_password_secret_id`, exactly as for OCI ADB. Each database needs its own secret in the approved project/environment Vault scope. Platform CI validates every secret against the trusted handoff, uses its OCI region, and only then reads `CURRENT` with Instance Principal under the runner's existing OCI IAM permissions before passing the password privately to the Azure module. No password, runtime token, binding name or separate secret-region field is accepted for Azure ADB. Merge the selected entry into `azure/<environment>/<region>/database/database.json`.

Use explicit request inputs or relevant existing resource JSON for Azure foundation references; optional Markdown can suggest values and needs no separate prerequisite PR. A new ADB always needs its own secret OCID. Subscription and authentication come from the runner's existing `ARM_*` configuration. Private profiles require a resource group, region, VNet, and Oracle-delegated subnet. Public profiles require only the resource group and region, with no VNet or subnet. A public endpoint accepts connections from any IP address and requires a client wallet, mandatory mTLS, and database authentication. State that exposure in the request preview. IP allowlists are not part of these profiles. Do not add ACL fields, empty network IDs, or network placeholders to a public template. Private profiles retain their existing TLS behavior.

The size-specific filenames replace `project_oracle_adb_template.json` and `project_oracle_adb_public_mtls_template.json`. The `oracle_autonomous_databases` collection and Azure adapter remain the same. Existing manifests using `admin_password`, including runtime tokens, must migrate to one distinct `admin_password_secret_id` OCID per database; the old field is rejected. Select a size-specific filename for new catalog requests.

The reviewed Azure adapter is [CRQ121212 commit 791d46865e096cb58613b3b5319f0c5eee301e95](https://github.com/oci-clickops/clickops-orchestrator-azure/commit/791d46865e096cb58613b3b5319f0c5eee301e95). Each consuming project must use this connectivity-aware adapter before requesting a public profile. Existing private manifests can omit `network_access` and `mtls_connection_required`; their private defaults are preserved. Changing an existing ADB between private and public connectivity requires replacement.

### Google — compute

**`project_compute_template.json`** Provisions exactly one private Debian 12 VM using handed-off project, zone, subnetwork, and service-account references. Public-IP fields are not part of the contract.

### Google — databases

**`project_google_adbs_template.json`** Provisions Oracle Autonomous Database Serverless on Google Cloud through `terraform-oci-multicloud-google`. The project repository must already have handoff values for the Google project, ODB Network, and client ODB Subnet. The template uses `properties.secret_id` for the admin password source; do not add literal passwords to Git.

## Placeholders

All placeholders follow the `__UPPER_SNAKE_CASE__` pattern and must be rendered before publication. For Azure and Google VMs, replace the SSH public-key placeholder with the approved public key itself. Do not use an environment token or Vault binding name; private keys stay outside Git.

Cross-template dependency: NSG/security-group placeholders in workload templates are string references, not OCIDs. Render them with a key that already exists in the corresponding project network manifest.

## Validation

The protected project workflow, Platform CI, and selected orchestrator validate supported manifest shapes, paths, deployment tuples, unresolved placeholders and change limits. Human review checks OCI/Google references against the handoff and Azure inputs against the intended existing foundation; effective runner IAM controls cloud access. The runtime does not compare every reference with the handoff document. The catalog templates are examples for Project Teams; Project GitOps intentionally performs no duplicate resource-specific validation.

## Security notes

- Never commit passwords. OCI and Azure ADB use `admin_password_secret_id`; Google ADB uses its provider-native `properties.secret_id`. Runtime password tokens are unsupported, with no GitHub Secrets fallback.
- Use the approved OCI/Google environment handoff or the supplied Azure request/JSON inputs for foundation references. Azure Markdown is optional. Foundation identifiers are not Terraform credentials.

## Warranty disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND.
