# Invalid Objects and Compile Errors

Use this reference when the user asks about invalid objects, compile errors, broken packages, failed views, invalid PL/SQL, or post-change object validity evidence.

## Sources

Primary sources:

- `ALL_OBJECTS` / `USER_OBJECTS` / `DBA_OBJECTS`
- `ALL_ERRORS` / `USER_ERRORS` / `DBA_ERRORS`

Official docs:
- `DBA_INVALID_OBJECTS`: https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/DBA_INVALID_OBJECTS.html
- `ALL_ERRORS`: https://docs.oracle.com/en/database/oracle/oracle-database/19/refrn/ALL_ERRORS.html

## Behavior

- Include invalid object and compile error summary in the default ops summary.
- Do not list every invalid object by default.
- First show aggregate summary by owner/schema and object type.
- If invalid object count is greater than 50, summarize only and offer drill-down.
- If count is small, a compact object list is acceptable.
- Prefer `ALL_*` views by default; use `DBA_*` only when available.

## Invalid object aggregate

```sql
select owner,
       object_type,
       count(*) as invalid_count,
       max(last_ddl_time) as latest_ddl_time
from all_objects
where status = 'INVALID'
group by owner, object_type
order by invalid_count desc, owner, object_type;
```

## Invalid object detail

```sql
select owner,
       object_name,
       object_type,
       status,
       last_ddl_time
from all_objects
where status = 'INVALID'
order by owner, object_type, object_name
fetch first 100 rows only;
```

## Compile errors aggregate

```sql
select owner,
       name,
       type,
       count(*) as error_count,
       min(line) as first_error_line
from all_errors
group by owner, name, type
order by error_count desc, owner, name, type
fetch first 50 rows only;
```

## Compile error detail

```sql
select owner,
       name,
       type,
       line,
       position,
       text,
       attribute,
       message_number
from all_errors
order by owner, name, type, sequence
fetch first 100 rows only;
```

## Interpretation guidance

Invalid objects are actionable evidence, but not every invalid object is an active outage. Ask for schema, object type, or object name when drilling down.
