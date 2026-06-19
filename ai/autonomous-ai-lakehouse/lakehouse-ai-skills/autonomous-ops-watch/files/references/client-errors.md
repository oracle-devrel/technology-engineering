# Client Errors

Use this reference when the user asks about client-side ORA errors, recent failures, repeated errors, SQL IDs associated with failures, or application modules experiencing database errors.

## Source

Primary source: `V$CLIENT_ERRORS`

Official docs:
- Query client errors / alert log related data: https://docs.oracle.com/iaas/autonomous-database-serverless/doc/autonomous-query-alert-log.html
- `V$CLIENT_ERRORS`: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/v-client-errors.html

## Behavior

- Include aggregated client errors in the default ops summary.
- Default time window: last 24 hours.
- Show total visible client errors.
- Show top 5 error numbers/messages by count.
- Include affected usernames, modules, actions, SQL IDs, and latest occurrence when useful.
- Do not list every occurrence by default.
- Do not expose full SQL text by default.
- Allow drill-down by error number, user, module, action, SQL ID, or time window.

## Aggregate query pattern

```sql
select error_num,
       error_message,
       username,
       module,
       action,
       sqlid,
       count(*) as occurrences,
       max(error_time) as latest_error_time
from v$client_errors
where error_time >= systimestamp - interval '24' hour
group by error_num, error_message, username, module, action, sqlid
order by occurrences desc, latest_error_time desc
fetch first 10 rows only;
```

## Recent detail query pattern

```sql
select error_time,
       username,
       module,
       action,
       sqlid,
       error_num,
       error_message
from v$client_errors
where error_time >= systimestamp - interval '24' hour
order by error_time desc
fetch first 50 rows only;
```

## Interpretation guidance

Client errors are SQL-visible evidence of errors seen by database clients. They do not always prove root cause. Group by module, action, username, and SQL ID to find patterns before escalating.
