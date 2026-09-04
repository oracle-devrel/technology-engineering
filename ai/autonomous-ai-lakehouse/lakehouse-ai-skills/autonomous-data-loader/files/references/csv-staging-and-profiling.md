# CSV staging and profiling

Use this reference when the user wants to load CSV files but does not have an existing target table or final schema.

## Contents

- Rule
- Conservative staging workflow
- Header-to-column sanitization
- Staging table template
- COPY_DATA for conservative staging
- Post-load profiling
- Curated DDL proposal

## Rule

CSV does not contain reliable data types. Do not generate a final business schema from the bucket, filename, or header alone.

If the target table does not exist, offer these options:

1. use a user-provided DDL/schema,
2. create a conservative staging table from the CSV header,
3. profile a sample first and then propose DDL.

## Conservative staging workflow

When the user approves conservative staging:

1. Discover objects with `DBMS_CLOUD.LIST_OBJECTS` if the user provided a bucket or prefix.
2. Read the CSV header through `DBMS_CLOUD.GET_OBJECT` when MCP can access the object; otherwise ask the user to paste the header line.
3. Sanitize column names.
4. Ask the user for the staging table name.
5. Create a staging table with all data columns as `VARCHAR2(4000)`.
6. Do not add metadata columns to the same `COPY_DATA` target by default.
7. Load with `skipheaders => 1`.
8. Reconcile and profile after load.
9. Propose curated DDL only after profiling or user-supplied schema requirements.

## Header-to-column sanitization

Apply these rules:

- trim whitespace,
- convert to uppercase unless the user requests quoted case-sensitive identifiers,
- replace spaces and punctuation with `_`,
- collapse repeated underscores,
- prefix with `C_` if the name starts with a digit,
- append `_COL` if the name is reserved or unsafe,
- deduplicate with suffixes such as `_2`, `_3`.

## Staging table template

Ask the user for the staging table name. If they ask for a suggestion, propose a safe name like `STG_<DATASET_NAME>_<YYYYMMDD>`.

```sql
create table <STAGING_TABLE> (
  <HEADER_COL_1> varchar2(4000),
  <HEADER_COL_2> varchar2(4000),
  <HEADER_COL_3> varchar2(4000)
);
```

## COPY_DATA for conservative staging

Treat the `CREATE TABLE` and `COPY_DATA` as mutating. Require approval before execution.

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => '<STAGING_TABLE>',
    credential_name => '<CREDENTIAL_NAME>',
    file_uri_list   => '<CSV_FILE_URI_OR_PATTERN>',
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

## Post-load profiling

After a conservative CSV staging load, run profiling queries before proposing curated DDL.

Row count:

```sql
select count(*) as row_count from <STAGING_TABLE>;
```

Nulls and lengths for a column:

```sql
select
  count(*) as row_count,
  sum(case when <COL> is null then 1 else 0 end) as null_count,
  max(length(<COL>)) as max_length,
  min(<COL>) as min_value,
  max(<COL>) as max_value,
  count(distinct <COL>) as distinct_count
from <STAGING_TABLE>;
```

Numeric candidate check:

```sql
select
  count(*) as row_count,
  sum(case when regexp_like(<COL>, '^[-+]?[0-9]+(\.[0-9]+)?$') then 1 else 0 end) as numeric_like_count,
  sum(case when <COL> is not null and not regexp_like(<COL>, '^[-+]?[0-9]+(\.[0-9]+)?$') then 1 else 0 end) as non_numeric_count
from <STAGING_TABLE>;
```

Date candidate check, using an explicit expected format:

```sql
select count(*) as candidate_count
from <STAGING_TABLE>
where <COL> is not null
  and validate_conversion(<COL> as date, 'YYYY-MM-DD') = 1;
```

## Curated DDL proposal

Only propose curated DDL after profiling or after the user supplies schema requirements. Label it as proposed and require approval before execution.

Do not create curated tables automatically unless the user explicitly approves the final DDL.
