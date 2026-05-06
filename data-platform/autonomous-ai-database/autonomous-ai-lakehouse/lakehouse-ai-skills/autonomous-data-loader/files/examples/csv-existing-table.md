# Example: CSV load into an existing table

User request:

> Load these CSV files from OCI Object Storage into `SALES_RAW` using credential `OBJ_STORE_CRED`.

Recommended flow:

1. List objects if the user provided a bucket or prefix.
2. Check `SALES_RAW` exists.
3. Inspect columns.
4. Generate `COPY_DATA`.
5. Ask approval before execution.
6. Monitor `USER_LOAD_OPERATIONS`.

```sql
select column_id, column_name, data_type, nullable
from user_tab_columns
where table_name = 'SALES_RAW'
order by column_id;
```

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => 'SALES_RAW',
    credential_name => 'OBJ_STORE_CRED',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/raw/sales/*.csv',
    format          => json_object(
      'type' value 'csv',
      'skipheaders' value 1,
      'delimiter' value ',',
      'quote' value '"',
      'blankasnull' value 'true',
      'rejectlimit' value 100,
      'enablelogs' value 'true',
      'logretention' value 7
    ),
    operation_id    => l_operation_id
  );
  dbms_output.put_line('operation_id=' || l_operation_id);
end;
/
```
