# Iceberg on OCI Object Storage

Use this reference when the user wants to query Apache Iceberg data stored in OCI Object Storage from Oracle Autonomous AI Lakehouse.

This workflow creates external-table query access. It does not copy Iceberg data into Autonomous and it does not use `COPY_DATA`.

## Official docs

- Query Apache Iceberg Tables: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/query-external-data-apache-iceberg.html
- DBMS_CLOUD package reference: https://docs.oracle.com/en/database/oracle/oracle-database/26/arpls/dbms_cloud.html
- DBMS_CLOUD.CREATE_EXTERNAL_TABLE: https://docs.oracle.com/en/database/oracle/oracle-database/26/arpls/dbms_cloud.html

## OCI-only scope

Support only these OCI Object Storage patterns:

1. Direct metadata file: external table points to a specific Iceberg root `metadata.json` file in OCI Object Storage.
2. HadoopCatalog on OCI: external table points to an OCI Object Storage lakehouse folder and an Iceberg table path.

Do not generate Unity, Polaris, AWS Glue, S3, Azure, or GCS examples in this skill.

## Important limitations to mention before creating the table

- Direct metadata access points to a specific `metadata.json` snapshot. To follow new snapshots, recreate the external table against the new metadata file.
- The external table schema is fixed at creation time and must match the Iceberg schema version referenced by the metadata.
- Query-time time travel by snapshot, version, or timestamp is not supported.
- Merge-on-read delete files are not supported; queries can fail when Iceberg metadata references delete files.
- Review the user's Autonomous AI Database version and documentation before promising support for advanced Iceberg features.

## Required inputs

For direct metadata mode:

- `external_table_name`
- `credential_name`
- `metadata_json_uri`, for example `https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/<path>/metadata.json`

For HadoopCatalog on OCI:

- `external_table_name`
- `credential_name`
- `iceberg_lakehouse_uri`, for example `https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/<lakehouse-folder>`
- `iceberg_table_path`, for example `db.icebergTablePy`

For ACL setup, when needed:

- `schema_name`
- OCI Object Storage region, for example `eu-frankfurt-1`

## Pre-checks

When MCP SQL execution is available, run read-only checks first:

```sql
select table_name
from user_tables
where table_name = upper(:external_table_name);
```

Check candidate metadata files or lakehouse folders with `LIST_OBJECTS` when the user gives a prefix instead of an exact URI:

```sql
select object_name, bytes, created, last_modified
from dbms_cloud.list_objects(
  credential_name => :credential_name,
  location_uri    => :location_uri
)
where object_name like '%.metadata.json'
   or object_name like '%metadata.json'
   or object_name like '%version-hint.text%'
order by object_name;
```

Do not guess the final Iceberg target when multiple metadata files or table paths are present. Ask the user to choose a `metadata.json` file or an `iceberg_table_path`.

## ACL helper for OCI Object Storage

Creating Iceberg external tables may require outbound HTTPS ACL privileges for the schema that creates and owns the external table.

Treat this as a mutating operation and require approval before execution.

```sql
begin
  dbms_network_acl_admin.append_host_ace(
    host       => 'objectstorage.<region>.oraclecloud.com',
    lower_port => 443,
    upper_port => 443,
    ace        => xs$ace_type(
      privilege_list => xs$name_list('http'),
      principal_name => '<schema_name>',
      principal_type => xs_acl.ptype_db
    )
  );
end;
/
```

Keep ACLs as narrow as possible: the specific Object Storage regional endpoint, HTTPS port 443, and only the schema that creates or owns the external table.

## Direct metadata external table

Use this pattern when the user has an exact Iceberg root `metadata.json` URI in OCI Object Storage.

Treat this as mutating because it creates an external table object.

```sql
begin
  dbms_cloud.create_external_table(
    table_name      => '<EXTERNAL_TABLE_NAME>',
    credential_name => '<OCI_CREDENTIAL_NAME>',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/<path>/metadata.json',
    format          => '{"access_protocol":{"protocol_type":"iceberg"}}'
  );
end;
/
```

After approval and execution, run a read-only sanity check:

```sql
select count(*) as row_count
from <EXTERNAL_TABLE_NAME>;
```

Then inspect the inferred external-table columns:

```sql
select column_id, column_name, data_type, data_length, data_precision, data_scale, nullable
from user_tab_columns
where table_name = upper(:external_table_name)
order by column_id;
```

## HadoopCatalog on OCI Object Storage

Use this pattern when Spark or OCI Data Flow wrote an Iceberg table using a HadoopCatalog-style lakehouse folder in OCI Object Storage.

Treat this as mutating because it creates an external table object.

```sql
begin
  dbms_cloud.create_external_table(
    table_name      => '<EXTERNAL_TABLE_NAME>',
    credential_name => '<OCI_CREDENTIAL_NAME>',
    format          => '{
      "access_protocol": {
        "protocol_type": "iceberg",
        "protocol_config": {
          "iceberg_catalog_type": "hadoop",
          "iceberg_lakehouse": "https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/<lakehouse-folder>",
          "iceberg_table_path": "<database>.<table>"
        }
      }
    }'
  );
end;
/
```

After approval and execution, run:

```sql
select count(*) as row_count
from <EXTERNAL_TABLE_NAME>;
```

## Troubleshooting Iceberg access

Common symptoms and likely next steps:

- `ORA-24247: network access denied by access control list`: generate the OCI Object Storage ACL helper and ask for approval before execution.
- Failure to generate column list: check ACLs, credential access, `metadata.json` URI, and Iceberg restrictions.
- Query fails after Iceberg table changed: recreate the external table against the current metadata/schema.
- Query fails because delete files are referenced: explain that merge-on-read delete files are not supported by the documented Iceberg query path.
- Zero rows or missing data: verify the selected `metadata.json` snapshot or HadoopCatalog table path.

## Response guidance

When handling Iceberg requests:

- State clearly that this is query access, not data loading into Autonomous.
- Ask whether the user has a direct `metadata.json` URI or a HadoopCatalog-style lakehouse folder.
- Prefer direct metadata for a simple, fixed snapshot demo.
- Prefer HadoopCatalog on OCI when the table was produced by Spark or OCI Data Flow with a lakehouse folder and table path.
- Require approval before ACL changes or `CREATE_EXTERNAL_TABLE`.
- Run `COUNT(*)` and column inspection after creation.
