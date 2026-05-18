# Example: JSON document load into a SODA collection

User request:

> Load this line-delimited JSON file into a document collection.

Recommended flow:

1. Confirm document-style loading.
2. Generate `COPY_COLLECTION`.
3. Ask for approval.
4. Monitor `USER_LOAD_OPERATIONS` and inspect log/badfile tables if needed.

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_collection(
    collection_name => 'EVENTS_COLLECTION',
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

For arrays of JSON documents, add the documented array-unpacking option when supported:

```sql
format => json_object(
  'type' value 'json',
  'unpackarrays' value 'true',
  'enablelogs' value 'true',
  'logretention' value 7
)
```
