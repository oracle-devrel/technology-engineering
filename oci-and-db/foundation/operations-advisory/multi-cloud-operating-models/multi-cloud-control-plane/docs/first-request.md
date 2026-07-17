# First OCI Autonomous Database request

This tutorial uses the approved OCI database catalog entry and updates the
existing aggregate manifest. Select the target `dev`, `test`, or `uat`
environment first; do not create a second file containing the same Terraform root key.

1. Select `resources-catalog/oci/databases/project_database_template.auto.tfvars.json`.
2. Render its double-underscore placeholders using the handoff values. Map
   the rendered `admin_password` field to the approved environment-scoped
   deployment secret;
   do not put the password in JSON. The workflow resolves that placeholder at
   runtime.
3. Merge the rendered entry into `oci/dev/eu-frankfurt-1/database/database.json`.

For example, the existing aggregate file is:

```json
{"autonomous_databases_configuration":{"adb_existing":{"display_name":"adb-existing"}}}
```

The rendered catalog entry is **not** a separate var-file:

```json
{"autonomous_databases_configuration":{"adb_dev_project01":{"display_name":"adb-dev-project01","admin_password":"<resolved-at-runtime>"}}}
```

The single merged manifest is:

```json
{"autonomous_databases_configuration":{"adb_existing":{"display_name":"adb-existing"},"adb_dev_project01":{"display_name":"adb-dev-project01","admin_password":"<resolved-at-runtime>"}}}
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
