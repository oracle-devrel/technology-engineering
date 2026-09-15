# COPY_DATA relational table loads

Use this reference when the user wants to load files from OCI Object Storage into an existing relational table in Autonomous AI Lakehouse.

## Contents

- Target table rule
- Basic COPY_DATA skeleton
- CSV into existing table
- Parquet, ORC, and Avro
- JSON into relational table
- XML caution
- After execution

## Target table rule

`DBMS_CLOUD.COPY_DATA` loads into an existing table. Do not assume the table exists.

Prefer bind variables when generating checks for MCP or manual execution:

```sql
select owner, table_name
from all_tables
where table_name = upper(:table_name)
  and (:schema_name is null or owner = upper(:schema_name));
```

For the current schema only:

```sql
select table_name
from user_tables
where table_name = upper(:table_name);
```

Inspect columns before loading:

```sql
select column_id,
       column_name,
       data_type,
       data_length,
       data_precision,
       data_scale,
       nullable
from all_tab_columns
where table_name = upper(:table_name)
  and (:schema_name is null or owner = upper(:schema_name))
order by owner, table_name, column_id;
```

For the current schema only:

```sql
select column_id,
       column_name,
       data_type,
       data_length,
       data_precision,
       data_scale,
       nullable
from user_tab_columns
where table_name = upper(:table_name)
order by column_id;
```

If the table does not exist, ask whether to generate a `CREATE TABLE` proposal. Do not invent final DDL from a filename alone.

## Basic COPY_DATA skeleton

Treat `COPY_DATA` as mutating. Generate first and require approval before execution.

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => '<TARGET_TABLE>',
    credential_name => '<CREDENTIAL_NAME>',
    file_uri_list   => '<FILE_URI_OR_URI_LIST>',
    format          => json_object(
      'type' value '<csv|json|parquet|orc|avro>',
      'enablelogs' value 'true',
      'logretention' value 7
    ),
    operation_id    => l_operation_id
  );

  dbms_output.put_line('operation_id=' || l_operation_id);
end;
/
```

Use `operation_id` for tracking when supported by the target environment.

## CSV into existing table

When the target table exists and the CSV has a header row:

```sql
format => json_object(
  'type' value 'csv',
  'skipheaders' value 1,
  'delimiter' value ',',
  'quote' value '"',
  'blankasnull' value 'true',
  'rejectlimit' value 100,
  'enablelogs' value 'true',
  'logretention' value 7
)
```

Use `detectfieldorder` only when the header is clean and restrictions are satisfied. It requires the number of header fields to match the table columns and does not support quoted field names.

## Parquet, ORC, and Avro

For Parquet, ORC, and Avro, prefer concise format options and rely on file metadata. Still check the target table and column compatibility first.

```sql
format => json_object(
  'type' value 'parquet',
  'enablelogs' value 'true',
  'logretention' value 7
)
```

Change `parquet` to `orc` or `avro` as appropriate.

## JSON into relational table

Use `COPY_DATA` for JSON only when the target is a relational table and the user knows how JSON fields map to table columns. Consider documented JSON options such as `columnpath` where required by the load pattern.

If the user wants document-style loading, use `COPY_COLLECTION` instead.

## XML caution

Treat XML as version-specific. Do not generate XML `COPY_DATA` workflows unless the user's Autonomous documentation explicitly confirms the supported load pattern and the expected relational mapping.

## After execution

Always monitor the load after execution:

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
order by start_time desc
fetch first 20 rows only;
```

If an `operation_id` is available, filter on it when the column is exposed in the target environment.
