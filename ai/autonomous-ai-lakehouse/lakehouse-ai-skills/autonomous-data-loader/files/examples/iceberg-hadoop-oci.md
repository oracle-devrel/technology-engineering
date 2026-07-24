# Example: query an Iceberg table on OCI Object Storage using HadoopCatalog

User request:

> My Iceberg table was created by Spark/OCI Data Flow using a HadoopCatalog lakehouse folder in OCI Object Storage. Create query access from Autonomous.

Recommended response behavior:

- Explain that this creates external-table query access; it does not copy Iceberg data into Autonomous.
- Confirm the external table name, credential name, OCI lakehouse folder URI, and `iceberg_table_path`.
- Warn about documented Iceberg limitations before asking for approval.
- Ask for approval before running `DBMS_CLOUD.CREATE_EXTERNAL_TABLE`.

```sql
begin
  dbms_cloud.create_external_table(
    table_name      => 'CUSTOMERS_ICEBERG_EXT',
    credential_name => 'OCI_CRED',
    format          => '{
      "access_protocol": {
        "protocol_type": "iceberg",
        "protocol_config": {
          "iceberg_catalog_type": "hadoop",
          "iceberg_warehouse": "https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/<namespace>/b/<bucket>/o/iceberg",
          "iceberg_table_path": "db.customers"
        }
      }
    }'
  );
end;
/
```

Read-only sanity checks after creation:

```sql
select count(*) as row_count
from CUSTOMERS_ICEBERG_EXT;
```

```sql
select column_id, column_name, data_type, data_length, data_precision, data_scale, nullable
from user_tab_columns
where table_name = 'CUSTOMERS_ICEBERG_EXT'
order by column_id;
```
