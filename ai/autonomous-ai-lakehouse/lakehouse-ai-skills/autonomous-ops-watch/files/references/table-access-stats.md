# Table and Partition Access Statistics

Use this reference only when the user asks about hot tables, heavily scanned objects, table access, partition access, or scan counts.

## Sources

Primary sources:

- `USER_TABLE_ACCESS_STATS`
- `ALL_TABLE_ACCESS_STATS`
- `DBA_TABLE_ACCESS_STATS`
- `V$TABLE_ACCESS_STATS`
- `GV$TABLE_ACCESS_STATS`

Official docs:
- Scan count tracking views: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/scancount-tracking-views.html

## Behavior

- On-demand only.
- Do not include in the default ops summary.
- Always limit output by default, for example top 20 objects.
- Explain that access counts are accumulated since instance startup, not over a user-specified historical window.
- Prefer `USER_*` or `ALL_*` views unless DBA-level visibility is available.

## Top accessed objects query

```sql
select owner,
       object_name,
       object_type,
       read_count
from all_table_access_stats
order by read_count desc
fetch first 20 rows only;
```

## Schema-specific query

```sql
select owner,
       object_name,
       object_type,
       read_count
from all_table_access_stats
where owner = upper(:owner)
order by read_count desc
fetch first 20 rows only;
```

## Interpretation guidance

Use these stats as object access evidence. Do not infer root cause from high scan counts alone. Combine with user context, workload, and performance evidence when available.
