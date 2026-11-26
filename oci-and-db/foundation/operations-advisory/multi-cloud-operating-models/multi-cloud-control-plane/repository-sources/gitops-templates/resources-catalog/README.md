# Resource catalog

Choose a template for the requested cloud and resource. Replace its documented placeholders and preserve the literal keys, values, types and collection shapes. Populate a collection only when the template supplies an entry shape. Platform CI passes the reviewed manifests to the selected orchestrator as Terraform variable files.

## Templates

### OCI — network

Use `project_nsgs_template.json` in `oci/<environment>/<region>/network/project-nsgs.json`. Add the project network security group (NSG) under `network_configuration.network_configuration_categories.<category>.inject_into_existing_vcns.<vcn-key>.network_security_groups`. Set `__NSG_KEY__`, `__NSG_DISPLAY_NAME__`, `__NSG_COMPARTMENT_OCID__` and `__NSG_TIER__`. Use the project compartment from the handoff and keep one entry for each VCN key in the regional manifest. Workloads reference the NSG by its manifest key.

Add the optional TCP fragments only for requested rules. To add a rule to an existing NSG, merge the fragment into its existing entry.

| Rule input | Fields |
| --- | --- |
| Rule key and description | Use the catalog entry shape. |
| Ingress source | `src` and `src_type` |
| Egress destination | `dst` and `dst_type` |
| Destination port range | Integer `dst_port_min` and `dst_port_max` |
| Protocol | Fixed to `TCP` by the template. |

Types include `CIDR_BLOCK`, `NETWORK_SECURITY_GROUP` and `SERVICE_CIDR_BLOCK` where the OCI Landing Zone contract supports them. Include `0.0.0.0/0` ingress only when explicitly requested and state the public exposure in the preview.

### OCI — compute

All profiles use the private Frankfurt image, shape `VM.Standard.A1.Flex`, the catalog CIS level, a 50 GB boot volume and the platform-owned SSH public-key path. Use a reviewed regional profile outside Frankfurt.

| Template | OCPUs | Memory |
| --- | --- | --- |
| `project_compute_small_template.json` | 1 | 6 GB |
| `project_compute_medium_template.json` | 2 | 12 GB |
| `project_compute_large_template.json` | 4 | 24 GB |

Supply `__VM_KEY__`, `__VM_NAME__`, `__VM_SUBNET_OCID__` and `__VM_NSG_KEY__`. The NSG key must exist in the regional network manifest. Use the handed-off Application compartment for `__PROJ_APP_CMP_OCID__`.

### OCI — databases

The profiles provision Autonomous Database Serverless with BYOL, private endpoints and both compute and storage auto-scaling disabled. Each profile fixes `is_dedicated` to `false`.

| Template | ECPUs | Storage |
| --- | --- | --- |
| `adb-small-byol.json` | 2 | 32 GB |
| `adb-medium-byol.json` | 4 | 64 GB |
| `adb-large-byol.json` | 8 | 128 GB |

Use `__PROJ_DB_SUBNET_OCID__` for the private database subnet and `__NSG_DB_KEY__` for the database NSG. Define any required NSG in `project-nsgs.json` first. The workload references its key in `networking.network_security_groups`. Replace `__ADB_ADMIN_PASSWORD_SECRET_OCID__` in `admin_password_secret_id` with a dedicated Vault secret OCID in the approved project scope and deployment region. The OCI module uses the native secret reference.

### Azure — compute

`project_compute_template.json` provisions a private Ubuntu 22.04 LTS Gen2 VM. Supply the approved resource group, subnet and NSG in the request or resource JSON. The runner provides subscription and authentication.

### Azure — databases

Choose a fixed BYOL profile for Oracle Autonomous Database on Azure. All profiles use OLTP and Oracle Database 19c. CPU auto-scaling is enabled and storage auto-scaling is disabled. The ECPU count is the base capacity.

| Size | Base ECPUs | Storage | Private template | Public mTLS template |
| --- | --- | --- | --- | --- |
| Small | 2 | 1 TB | `adb-small-byol.json` | `adb-small-public-mtls-byol.json` |
| Medium | 4 | 2 TB | `adb-medium-byol.json` | `adb-medium-public-mtls-byol.json` |
| Large | 8 | 4 TB | `adb-large-byol.json` | `adb-large-public-mtls-byol.json` |

| Connectivity | Foundation inputs | Access |
| --- | --- | --- |
| Private | Resource group, region, existing VNet and Oracle-delegated subnet | Existing private TLS behavior |
| Public mTLS | Resource group and region. Leave network IDs and ACL fields out. | Any IP with a client wallet, mTLS and database authentication. State the exposure in the request preview. |

Merge the entry into `azure/<environment>/<region>/database/database.json` under `oracle_autonomous_databases`. Use the approved request or resource JSON for foundation inputs. The Azure handoff notes can suggest values and the runner supplies `ARM_*` settings. Set `__ADB_ADMIN_PASSWORD_SECRET_OCID__` in `admin_password_secret_id` to one OCI Vault secret OCID per database. Platform CI checks the secret in the trusted handoff's OCI region and resolves `CURRENT` privately. Use the OCID directly and leave password, binding and secret-region fields out of the manifest.

Platform CI also checks existing entries in the selected regional manifest. Legacy `admin_password` fields and runtime tokens fail validation. If you find one, confirm the project has a supported handoff and use the reviewed change process to replace the legacy input with the database's dedicated `admin_password_secret_id` before submitting another request in that scope.

Use the size-specific filenames for new requests. They supersede `project_oracle_adb_template.json` and `project_oracle_adb_public_mtls_template.json`. Existing private manifests may omit `network_access` and `mtls_connection_required` to use the private defaults. Changing between private and public connectivity requires replacement. Cloud Operations must pin the reviewed connectivity-aware adapter before enabling public requests. [Azure adapter revision](https://github.com/oci-clickops/clickops-orchestrator-azure/commit/791d46865e096cb58613b3b5319f0c5eee301e95)

### Google — compute

`project_compute_template.json` provisions a private Debian 12 VM. Use the approved Google Cloud handoff for its project, zone, subnetwork and service account.

### Google — databases

`project_google_adbs_template.json` provisions Autonomous Database Serverless through `terraform-oci-multicloud-google`. Use the handed-off Google project, ODB Network and client ODB Subnet. Supply the provider-native password reference in `properties.secret_id`.

## Placeholders

Replace every `__UPPER_SNAKE_CASE__` placeholder before publication. For Azure and Google Cloud VMs, use the approved SSH public key directly. Workload references to an OCI catalog NSG use its manifest key. Keep passwords and private keys outside Git.

## Validation

The workflows validate paths, manifest shapes, deployment scope and placeholders. Reviewers compare OCI and Google Cloud references with the handoff and Azure inputs with the intended existing foundation. Runner IAM controls cloud access. New fields or resource types require a reviewed extension.

## Warranty disclaimer

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND.
