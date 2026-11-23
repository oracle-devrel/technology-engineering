# Walkthrough: Request a private OCI Autonomous Database

This example follows one Project Team request from a prepared non-production repository to a reviewed deployment. It uses sample names and placeholders; replace only the bracketed values with the approved values from your handoff. Never copy a password or deployment credential into Git.

## Outcome

The Project Team requests one private Autonomous Database named `ordersadb` in `dev` and `eu-frankfurt-1`. Cloud Operations has already handed off the repository, network, Database compartment, and runner boundary. The team proposes the change in a pull request; a reviewer approves it; trusted automation executes the merged request.

## 1. Confirm that the request is ready

Before editing anything, confirm all of the following:

- You have write access to the handed-off `nonprod-orders` repository.
- `dev` and `eu-frankfurt-1` are approved in `environments/dev/environment_information.md`.
- The handoff supplies the Database compartment and private database-subnet OCIDs.
- The existing `oci/dev/eu-frankfurt-1/network/project-nsgs.json` file defines the database NSG key you will use.
- The Project Team has a distinct administrator-password secret for `ordersadb`, or will prepare one through the Codex skill using its authorized Project Team OCI profile. The secret belongs to the handed-off Vault scope and deployment region. Cloud Operations has prepared the runner's read access.

If the handoff is incomplete, ask Cloud Operations to correct it. If the secret is missing, the [Codex plugin](codex-plugin.md) can propose its preparation, ask for a separate confirmation, create it using native Vault password generation and insert the returned OCID into the request. Manual preparation remains available; the optional UI requires an existing OCID. Do not invent a foundation reference or commit a secret value.

## 2. Prepare one manifest change

Use the OCI Small BYOL ADB template from the approved [resource catalog](../../repository-sources/gitops-templates/resources-catalog/README.md) and edit the existing regional manifest:

```text
oci/dev/eu-frankfurt-1/database/database.json
```

For the first database in that file, replace its `{}` contents with this single entry. Replace the bracketed values with handoff values, and replace `orders-db-nsg` with the key already present in the project NSG manifest.

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

The manifest contains the secret's OCID, not its value. The native module reads its current version from Vault during the reviewed plan and apply. Use a different secret for each database. The password must meet the catalog prerequisites: 12 to 30 characters with uppercase, lowercase and a digit, without double quotes or `admin` in any casing. Keep one database configuration file for this cloud, environment, and region; Terraform does not deep-merge repeated root values across separate files.

## 3. Open and review the pull request

Check the JSON, then create a focused branch and pull request through the [GitHub interface](github-interface.md), optional UI, or optional Codex plugin. Record the change reference required by your organization, for example `CRQ1234`.

Before approval, verify that the pull request changes only this OCI `dev` request, the compartment, subnet, and NSG key match the handoff, and the plan shows one intended private Autonomous Database. The reviewer must not be the pull-request author.

## 4. Merge and verify the result

After the required approval and successful plan, merge through the governed process. The trusted runner, not the Project Team, applies the change. Verify the post-merge workflow and the database outcome, then retain the pull request and workflow result as the request evidence.

For the complete safety rules, including removal and troubleshooting, follow the [request lifecycle](request-lifecycle.md). The supplied request surface and reference scope are listed in [Reference capabilities](../reference/support.md).
