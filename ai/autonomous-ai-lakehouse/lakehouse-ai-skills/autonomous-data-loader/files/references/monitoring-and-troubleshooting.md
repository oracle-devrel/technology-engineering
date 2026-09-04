# Monitoring and troubleshooting

Use this reference after any `DBMS_CLOUD.COPY_DATA` or `DBMS_CLOUD.COPY_COLLECTION` operation, or when the user says a load failed.

## Contents

- Load history query
- Log and badfile inspection
- Reconciliation checklist
- Troubleshooting flow
- Common root causes and fixes
- Safe retry decision tree

## Load history query

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

If the current user has privileges and needs a broader view:

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
from dba_load_operations
where type = 'COPY'
order by start_time desc
fetch first 50 rows only;
```

## Log and badfile inspection

When `LOGFILE_TABLE` is populated, query it:

```sql
select * from <LOGFILE_TABLE>;
```

When `BADFILE_TABLE` is populated, query it:

```sql
select * from <BADFILE_TABLE>;
```

Use dynamic SQL only if needed and only after validating table names from `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS`.

## Reconciliation checklist

After each load, report:

- target table or collection,
- load status,
- start and update time,
- selected files or pattern,
- log table name,
- badfile table name,
- target row count if applicable,
- rejected rows if visible,
- whether retry appears safe.

Target row count:

```sql
select count(*) as target_row_count from <TARGET_TABLE>;
```

## Troubleshooting flow

1. Query `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS`.
2. Locate the most relevant failed or recent `COPY` operation.
3. Query `LOGFILE_TABLE`.
4. Query `BADFILE_TABLE` when present.
5. Summarize likely root causes.
6. Recommend targeted format option changes.
7. Recommend whether retry is safe.

## Common root causes and fixes

- Wrong URI or credential: verify `LIST_OBJECTS` against the same credential and prefix.
- Mixed file formats: list objects and split loads by format.
- Header row loaded as data: add or adjust `skipheaders`.
- Wrong delimiter: change `delimiter` after inspecting sample rows.
- Quoted fields rejected: set `quote`, `endquote`, or embedded newline handling as documented.
- Date or timestamp conversion errors: set explicit `dateformat` or `timestampformat`.
- Numeric conversion errors: inspect separators, empty values, and target numeric types.
- Too many or too few fields: inspect delimiter, `ignoremissingcolumns`, `detectfieldorder`, and target column count.
- Values too long: profile `max(length(col))`; do not suggest `truncatecol` unless loss is acceptable.
- JSON structure mismatch: decide whether to use `COPY_COLLECTION`, JSON relational `COPY_DATA`, or raw JSON table.

## Safe retry decision tree

Before retrying, determine whether the previous run inserted rows and whether the target is isolated staging or a final/business table.

Use this decision tree:

1. **No rows inserted or load failed before target mutation**
   - Retry may be safe after fixing the root cause.
   - Still prefer a small validation load when the issue is format-related.

2. **Rows inserted into a dedicated staging table**
   - Prefer creating a new staging table for the retry.
   - If the user wants to reuse the same staging table, require strict approval before `TRUNCATE TABLE` or `DROP TABLE`.

3. **Rows inserted into a final or shared target table**
   - Do not retry blindly.
   - Recommend a reconciliation plan, duplicate detection, or loading corrected data into staging first.

4. **Unknown whether rows were inserted**
   - Treat as unsafe.
   - Inspect row counts and load logs first.
   - If still uncertain, create a new staging target.

5. **Cleanup is destructive**
   - Never include it silently in batch approval.
   - Require strict per-operation approval.

Safer options:

- load into a new staging table,
- truncate an existing staging table only after strict approval,
- reload a known isolated target,
- use a batch identifier pattern in a separate controlled workflow,
- promote to curated only after reconciliation.
