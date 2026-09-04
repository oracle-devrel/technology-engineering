# Example: query an Iceberg table on OCI Object Storage using metadata.json

User request:

> I have an Iceberg metadata.json file in OCI Object Storage. Create query access from Autonomous AI Lakehouse.

Recommended response behavior:

- Explain that this creates an external table for query access; it does not copy Iceberg data into Autonomous.
- Confirm the external table name, credential name, and exact `metadata.json` URI.
- Mention that the direct metadata path is point-in-time and may need recreation after snapshots or schema changes.
- Ask for approval before running `DBMS_CLOUD.CREATE_EXTERNAL_TABLE`.

```sql
begin
  dbms_cloud.create_external_table(
    table_name      => 'CUSTOMERS_ICEBERG_EXT',
    credential_name => 'OCI_CRED',
    file_uri_list   => 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/<namespace>/b/<bucket>/o/iceberg/customers/metadata/00001.metadata.json',
    format          => '{"access_protocol":{"protocol_type":"iceberg"}}'
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
