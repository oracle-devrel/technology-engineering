# Unified Audit Reviewer

Use this reference when the user asks about audit evidence, failed logins, password changes, user or role changes, sensitive DDL, or security-relevant database activity visible through SQL.

## Source

Primary source: `UNIFIED_AUDIT_TRAIL`

Official docs:
- Autonomous audit: https://docs.oracle.com/en-us/iaas/autonomous-database-shared/doc/adb-audit.html

## Behavior

- Include compact audit highlights in the default ops summary.
- Default time window: last 24 hours.
- Use a limited ops-focused audit profile by default.
- Do not query or display the full `UNIFIED_AUDIT_TRAIL` broadly unless the user explicitly asks.
- If no relevant audit events are found, show one short line.
- Mention audit retention or visibility limits when relevant.
- Show truncated SQL text samples only; full SQL text only on explicit request and when appropriate.

## Default audit focus

- failed logins;
- password changes;
- user or account changes;
- role or grant changes;
- DDL on key objects such as procedures, packages, functions, views, and tables;
- sensitive package execution if visible.

## Failed login query

```sql
select event_timestamp,
       dbusername,
       userhost,
       action_name,
       return_code,
       unified_audit_policies
from unified_audit_trail
where event_timestamp >= systimestamp - interval '24' hour
  and action_name = 'LOGON'
  and return_code <> 0
order by event_timestamp desc
fetch first 50 rows only;
```

## Ops-focused audit query

```sql
select event_timestamp,
       dbusername,
       userhost,
       action_name,
       object_schema,
       object_name,
       system_privilege_used,
       unified_audit_policies,
       dbms_lob.substr(sql_text, 1000, 1) as sql_text_sample
from unified_audit_trail
where event_timestamp >= systimestamp - interval '24' hour
  and (
       action_name in ('CREATE USER','ALTER USER','DROP USER','GRANT','REVOKE','CREATE ROLE','DROP ROLE')
    or action_name like 'CREATE%'
    or action_name like 'ALTER%'
    or action_name like 'DROP%'
    or action_name = 'LOGON' and return_code <> 0
  )
order by event_timestamp desc
fetch first 50 rows only;
```

## Interpretation guidance

Treat audit rows as evidence. Do not infer malicious activity from a single row without context. Group by user, host, action, and object to find patterns.
