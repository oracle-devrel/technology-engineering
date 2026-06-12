# COPY_COLLECTION JSON document loading

Use this reference when the user wants to load JSON documents from OCI Object Storage into a SODA collection.

## Contents

- Decision rule
- Collection existence and creation behavior
- COPY_COLLECTION skeleton
- JSON arrays
- Extended JSON
- Monitoring

## Decision rule

Ask the user to choose when JSON intent is ambiguous:

1. relational table load with `DBMS_CLOUD.COPY_DATA`,
2. document collection load with `DBMS_CLOUD.COPY_COLLECTION`,
3. raw JSON table for later modeling.

Use `COPY_COLLECTION` when the user wants schemaless/document-style loading into a SODA collection.

## Collection existence and creation behavior

`DBMS_CLOUD.COPY_COLLECTION` loads JSON documents into a SODA collection. In supported Autonomous environments, the procedure can create the collection if it does not already exist. Treat this as mutating even when the collection is new.

Before execution, check or clarify:

- desired collection name,
- whether creating a missing collection is acceptable,
- whether the source is normal JSON or Extended JSON,
- whether JSON array unpacking is needed.

## COPY_COLLECTION skeleton

Treat `COPY_COLLECTION` as mutating. Generate first and require approval before execution.

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_collection(
    collection_name => '<COLLECTION_NAME>',
    credential_name => '<CREDENTIAL_NAME>',
    file_uri_list   => '<JSON_FILE_URI_OR_URI_LIST>',
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

## JSON arrays

When a JSON file contains an array of documents, include the documented array-unpacking option if applicable in the user's Autonomous version.

```sql
format => json_object(
  'type' value 'json',
  'unpackarrays' value 'true',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

If the user's documentation/version uses different option names or restrictions, follow the official docs for that environment.

## Extended JSON

Use `ejson` only when the user needs extended JSON scalar values supported by Oracle JSON/SODA behavior.

```sql
format => json_object(
  'type' value 'ejson',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

## Monitoring

Monitor JSON document loads the same way as other `DBMS_CLOUD` load operations:

```sql
select id,
       table_name,
       owner_name,
       type,
       status,
       start_time,
       update_time,
       logfile_table,
       badfile_table
from user_load_operations
where type = 'COPY'
order by start_time desc;
```

If `LOGFILE_TABLE` or `BADFILE_TABLE` is present, query those tables for detail.
