# Example: Troubleshooting a failed load

User request:

> The load failed. Help me debug it.

Recommended flow:

1. Query recent load operations.
2. Identify the failed operation.
3. Inspect `LOGFILE_TABLE`.
4. Inspect `BADFILE_TABLE` if present.
5. Recommend targeted format changes and retry strategy.

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

Then query the reported tables:

```sql
select * from <LOGFILE_TABLE>;
select * from <BADFILE_TABLE>;
```

If the log shows date conversion issues, suggest an explicit date format. If rows have too many columns, inspect delimiter and quote handling. If values are too long, profile lengths before suggesting truncation.
