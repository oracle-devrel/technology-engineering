# First OCI Autonomous Database request

This tutorial uses the approved OCI database catalog entry and updates the
existing aggregate manifest. Select the target `dev`, `test`, or `uat`
environment first; do not create a second file containing the same Terraform root key.

1. Select `resources-catalog/oci/databases/project_database_template.auto.tfvars.json`.
2. Render its double-underscore placeholders using the handoff values. Map
   the catalog token `__ADB_ADMIN_PASSWORD__` to an environment-qualified runtime
   token such as `__DEV_ADB_ADMIN_PASSWORD__`, whose name exists in the selected
   repository secret bundle;
   do not put the password in JSON. The workflow resolves that placeholder at
   runtime.
3. Merge the rendered entry into `oci/dev/eu-frankfurt-1/database/database.json`.

For example, the existing aggregate file is:

```json
{"autonomous_databases_configuration":{"default_compartment_id":"ocid1.compartment.oc1..projectdatabase","databases":{"adb_existing":{"db_name":"EXISTING","display_name":"adb-existing","is_dedicated":false,"ecpu_count":2,"non_dw_storage_size_in_gbs":32,"db_workload":"OLTP","license_model":"BRING_YOUR_OWN_LICENSE","enable_cpu_auto_scaling":false,"enable_storage_auto_scaling":false,"admin_password":"__DEV_ADB_EXISTING_ADMIN_PASSWORD__","networking":{"enable_private_endpoint":true,"subnet_id":"ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase","network_security_groups":["NSG-DB-EXISTING"]}}}}}
```

The rendered catalog entry is **not** a separate var-file:

```json
{"autonomous_databases_configuration":{"default_compartment_id":"ocid1.compartment.oc1..projectdatabase","databases":{"adb_dev_project01":{"db_name":"PROJ01ADB","display_name":"adb-dev-project01","is_dedicated":false,"ecpu_count":2,"non_dw_storage_size_in_gbs":32,"db_workload":"OLTP","license_model":"BRING_YOUR_OWN_LICENSE","enable_cpu_auto_scaling":false,"enable_storage_auto_scaling":false,"admin_password":"__DEV_ADB_ADMIN_PASSWORD__","networking":{"enable_private_endpoint":true,"subnet_id":"ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase","network_security_groups":["NSG-DB-PROJECT01"]}}}}}
```

The single merged manifest is:

```json
{"autonomous_databases_configuration":{"default_compartment_id":"ocid1.compartment.oc1..projectdatabase","databases":{"adb_existing":{"db_name":"EXISTING","display_name":"adb-existing","is_dedicated":false,"ecpu_count":2,"non_dw_storage_size_in_gbs":32,"db_workload":"OLTP","license_model":"BRING_YOUR_OWN_LICENSE","enable_cpu_auto_scaling":false,"enable_storage_auto_scaling":false,"admin_password":"__DEV_ADB_EXISTING_ADMIN_PASSWORD__","networking":{"enable_private_endpoint":true,"subnet_id":"ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase","network_security_groups":["NSG-DB-EXISTING"]}},"adb_dev_project01":{"db_name":"PROJ01ADB","display_name":"adb-dev-project01","is_dedicated":false,"ecpu_count":2,"non_dw_storage_size_in_gbs":32,"db_workload":"OLTP","license_model":"BRING_YOUR_OWN_LICENSE","enable_cpu_auto_scaling":false,"enable_storage_auto_scaling":false,"admin_password":"__DEV_ADB_ADMIN_PASSWORD__","networking":{"enable_private_endpoint":true,"subnet_id":"ocid1.subnet.oc1.eu-frankfurt-1.projectdatabase","network_security_groups":["NSG-DB-PROJECT01"]}}}}}
```

Terraform does not deep-merge two files that set
`autonomous_databases_configuration`; a second file can replace or conflict
with the first. Keep the regional aggregate path from the
[canonical manifest-path table](operations.md#manifest-paths).

Open a focused pull request. Inspect the Terraform plan for the intended ADB,
independent approval, and no unrelated changes. After merge, verify the apply
workflow succeeds and that the database's display name and expected settings
appear in the cloud console or approved inventory. Never retry from a personal
credential or edit Terraform state manually.
