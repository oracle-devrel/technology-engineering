# Example: Parquet load into an existing table

User request:

> Load Parquet files from Object Storage into `ORDERS_RAW`.

Recommended flow:

1. List objects if needed.
2. Check `ORDERS_RAW` exists.
3. Inspect columns.
4. Generate and approve `COPY_DATA`.
5. Monitor.

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => 'ORDERS_RAW',
    credential_name => 'OBJ_STORE_CRED',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/raw/orders/*.parquet',
    format          => json_object(
      'type' value 'parquet',
      'enablelogs' value 'true',
      'logretention' value 7
    ),
    operation_id    => l_operation_id
  );
  dbms_output.put_line('operation_id=' || l_operation_id);
end;
/
```
