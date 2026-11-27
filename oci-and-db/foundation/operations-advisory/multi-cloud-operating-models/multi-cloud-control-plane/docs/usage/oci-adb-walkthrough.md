# Walkthrough: Request a private OCI Autonomous Database

Follow one database request using sample names and placeholders. Use approved values from your own project if you follow the procedure.

## Outcome

Request a private Autonomous Database named `ordersadb` in `dev` and `eu-frankfurt-1`. The Small BYOL profile uses 2 ECPUs and 32 GB with compute and storage auto-scaling disabled.

## 1. Confirm that the request is ready

| You need | Where to find it |
| --- | --- |
| Write access to `nonprod-orders` and approval to use `dev` in `eu-frankfurt-1` | Cloud Operations and `environments/dev/environment_information.md` |
| Database compartment and private database-subnet OCIDs | The environment handoff |
| Database network security group key | `oci/dev/eu-frankfurt-1/network/project-nsgs.json` |
| Dedicated password secret OCID for `ordersadb` | The approved Vault scope in the deployment region. Cloud Operations prepares the runner's read access. |

Ask Cloud Operations to correct an incomplete handoff. Prepare a missing secret through your approved manual process or the [Codex plugin](codex-plugin.md#prepare-and-publish). The optional UI requires an existing OCID.

## 2. Prepare one manifest change

Use the OCI Small BYOL ADB template from the approved [resource catalog](../../repository-sources/gitops-templates/resources-catalog/README.md) and edit the existing regional manifest:

```text
oci/dev/eu-frankfurt-1/database/database.json
```

For the first database, replace the file's `{}` with the example below. If the file already has databases, add only the `ordersadb` entry to `databases` and check the existing compartment. Replace the bracketed placeholders with the approved compartment, subnet and secret OCIDs. Use the existing database NSG key in place of `orders-db-nsg`.

```json
{
  "autonomous_databases_configuration": {
    "default_compartment_id": "<database-compartment-ocid-from-handoff>",
    "databases": {
      "ordersadb": {
        "db_name": "ORDERSADB",
        "display_name": "ordersadb",
        "is_dedicated": false,
        "ecpu_count": 2,
        "non_dw_storage_size_in_gbs": 32,
        "db_workload": "OLTP",
        "license_model": "BRING_YOUR_OWN_LICENSE",
        "enable_cpu_auto_scaling": false,
        "enable_storage_auto_scaling": false,
        "admin_password_secret_id": "<ordersadb-vault-secret-ocid>",
        "networking": {
          "enable_private_endpoint": true,
          "subnet_id": "<private-database-subnet-ocid-from-handoff>",
          "network_security_groups": ["orders-db-nsg"]
        }
      }
    }
  }
}
```

Commit the secret OCID and keep the password in Vault. For manual preparation, use 12 to 30 characters with uppercase, lowercase and a digit. Exclude double quotes and `admin` in any casing. Keep one database configuration file for the selected cloud, environment and region.

## 3. Open and review the pull request

Validate the JSON and open a focused pull request. You can also prepare the request from the [optional UI](optional-ui.md) or [Codex plugin](codex-plugin.md). Record the change reference, for example `CRQ1234`.

Ask an independent reviewer to compare the compartment and subnet with the handoff and the NSG key with the regional network manifest. The current plan should show one new private database for the intended OCI scope.

## 4. Merge and verify the result

After approval, merge through the approved process. Verify the execution step for the merge commit and confirm that the database is available in the intended OCI environment. Keep the pull request and workflow link. See the [request lifecycle](request-lifecycle.md) for removal and troubleshooting.

## Request an Autonomous Database on Azure

Use the same review process in a separate Azure pull request. Choose the [Small private BYOL profile](../../repository-sources/gitops-templates/resources-catalog/azure/databases/adb-small-byol.json) or [Small public mTLS BYOL profile](../../repository-sources/gitops-templates/resources-catalog/azure/databases/adb-small-public-mtls-byol.json). Both use 2 base ECPUs, 1 TB, OLTP and Oracle Database 19c, with CPU auto-scaling enabled and storage auto-scaling disabled.

Merge the selected entry under `oracle_autonomous_databases` in `azure/<environment>/<region>/database/database.json`, for example `azure/dev/uksouth/database/database.json`. Replace `{}` for the first entry or add to the existing collection. Supply the intended existing `resource_group_name`, such as `rg-emea-oa`, and Azure `location`, such as `uksouth`, matching the manifest region. The runner supplies subscription and authentication.

| Profile | Network inputs and access |
| --- | --- |
| Private | Supply an existing `virtual_network_id` and Oracle-delegated `subnet_id`. Clients need connectivity to the private endpoint. |
| Public mTLS | No VNet or subnet input is required. Connections from any IP are permitted, with mandatory mTLS, a client wallet and database authentication. State this public exposure in the request. |

Each Azure database needs its own OCI Vault secret OCID in `admin_password_secret_id`, distinct from the OCI database secret and any other database secret. The version 5 environment handoff identifies the approved Vault, project key, Database secrets compartment and OCI region used to validate and resolve that secret. The Azure deployment location does not select the OCI Vault region. Keep secret values outside the manifest and do not add password or secret-region fields. Prepare a missing secret through the approved manual process or the [Codex plugin](codex-plugin.md#prepare-and-publish); the optional UI requires an existing OCID.

Replace every catalog placeholder and retain the chosen profile's fixed values. Confirm that Cloud Operations has enabled the required [Azure adapter and foundation inputs](../../repository-sources/gitops-templates/resources-catalog/README.md#azure--databases). Follow the common [review, merge and execution verification](request-lifecycle.md#review-and-execute), checking the resource group, location, network profile and dedicated secret reference. Keep the matching pull request and post-merge workflow as evidence.
