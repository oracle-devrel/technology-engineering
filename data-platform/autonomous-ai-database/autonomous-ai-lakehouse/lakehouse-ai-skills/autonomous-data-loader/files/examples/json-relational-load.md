# Example: JSON load into a relational table

User request:

> Load JSON data from Object Storage into existing table `EVENTS_RAW`.

Recommended flow:

1. Ask whether the user wants relational table loading or document collection loading.
2. If relational, check the table exists and inspect columns.
3. Generate `COPY_DATA` with JSON format options and mappings as needed.
4. Ask for approval.
5. Monitor the load.

```sql
select column_id, column_name, data_type, nullable
from user_tab_columns
where table_name = 'EVENTS_RAW'
order by column_id;
```

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => 'EVENTS_RAW',
    credential_name => 'OBJ_STORE_CRED',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/raw/events/events.json',
    format          => json_object(
      'type' value 'json',
      'enablelogs' value 'true',
      'logretention' value 7
    ),
    operation_id    => l_operation_id
  );
  dbms_output.put_line('operation_id=' || l_operation_id);
end;
/
```
