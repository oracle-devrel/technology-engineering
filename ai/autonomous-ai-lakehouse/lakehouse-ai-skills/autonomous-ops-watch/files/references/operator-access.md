# Operator Access Audit

Use this reference when the user asks whether Oracle Cloud Operations accessed the database, whether operator access is enabled, what operator actions occurred, or how to produce operator access audit evidence.

## Sources

Primary sources:

- `DBA_OPERATOR_ACCESS`
- `DBA_CLOUD_CONFIG`

Official docs:
- View operator access: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/view-operator-access.html
- Operator access: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-operator-access.html

## Behavior

- Include a short operator access check in the default ops summary.
- Read-only only in v0.1.
- Do not call `DBMS_CLOUD_ADMIN.ENABLE_OPERATOR_ACCESS`.
- Do not call `DBMS_CLOUD_ADMIN.DISABLE_OPERATOR_ACCESS`.
- Show timestamp, request id, reason, and SQL/action summary when available.
- If `DBA_OPERATOR_ACCESS` has no rows, say that no SQL-visible operator actions were found in the time window, not that none ever occurred.

## Operator access configuration query

```sql
select param_name,
       param_value
from dba_cloud_config
where lower(param_name) like '%operator%'
order by param_name;
```

## Recent operator actions query

```sql
select event_timestamp,
       request_id,
       reason,
       dbusername,
       sql_text
from dba_operator_access
where event_timestamp >= systimestamp - interval '7' day
order by event_timestamp desc
fetch first 50 rows only;
```

## Summary guidance

Summarize:

- whether operator access appears enabled from SQL-visible configuration;
- recent Oracle Cloud Operations actions if visible;
- request id and reason when present;
- visibility limits.
