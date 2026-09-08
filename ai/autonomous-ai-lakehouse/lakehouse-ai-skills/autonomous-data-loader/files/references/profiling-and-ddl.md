# Profiling and DDL proposals

Use this reference when the user asks for target DDL or curated tables after loading.

## DDL rule

Do not generate final DDL from a path, filename, or CSV header alone. Generate a proposed DDL only when one of these is available:

- user-provided schema,
- file metadata for structured formats,
- profiling results from a staging table,
- sample rows plus user confirmation,
- clear existing target table structure.

## Structured file formats

For Parquet, ORC, and Avro, file metadata can inform schema, but `COPY_DATA` still needs an existing target table. If the user needs DDL, consider a profiling external table workflow only as an advisory step, then propose the target table.

## CSV

For CSV, prefer conservative staging first. After load, profile each column for:

- null counts,
- maximum length,
- distinct count,
- numeric-like values,
- date/timestamp candidates,
- suspicious outliers.

## Proposed DDL pattern

Clearly label curated DDL as proposed:

```sql
-- Proposed curated table. Review before execution.
create table <CURATED_TABLE> (
  <COL_1> number,
  <COL_2> varchar2(100),
  <COL_3> date
);
```

Require approval before executing any `CREATE TABLE`.

## Promotion guidance

If the user wants to promote from staging to curated:

- generate validation checks first,
- make casts explicit,
- isolate rejected cast rows where possible,
- prefer `insert into ... select ...` for initial promotion,
- use `merge` only when keys and idempotency are defined.

Example cast check before promotion:

```sql
select count(*) as invalid_amount_rows
from <STAGING_TABLE>
where <AMOUNT_COL> is not null
  and not regexp_like(<AMOUNT_COL>, '^[-+]?[0-9]+(\.[0-9]+)?$');
```

Example promotion skeleton:

```sql
insert into <CURATED_TABLE> (<COL_LIST>)
select
  cast(<NUMERIC_TEXT_COL> as number),
  <TEXT_COL>,
  to_date(<DATE_TEXT_COL>, 'YYYY-MM-DD')
from <STAGING_TABLE>;
```
