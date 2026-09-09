# Lockdown Profile Errors

Use this reference when the user asks about SQL blocked by Autonomous restrictions, lockdown profile errors, permission-like failures caused by lockdown rules, or repeated blocked operations.

## Source

Primary source: `DBA_LOCKDOWN_ERRORS`

Official docs:
- Lockdown profile errors view: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/lockdown_profile_erros_views.html

## Behavior

- Include aggregated lockdown profile errors in the default ops summary.
- Default time window: last 24 hours.
- Show aggregates by rule type, error number/message, username, module, and action.
- Show truncated SQL text samples only when useful.
- Do not list every SQL statement by default.
- Allow drill-down by rule type, error number, user, module, action, SQL ID, or time window.
- If `DBA_LOCKDOWN_ERRORS` is not visible, state that lockdown evidence is not available to the connected user.

## Aggregate query pattern

```sql
select rule_type,
       error_num,
       error_msg,
       username,
       module,
       action,
       count(*) as error_records,
       sum(occurrence_count) as total_occurrences,
       max(last_occurrence) as latest_occurrence
from dba_lockdown_errors
where last_occurrence >= systimestamp - interval '24' hour
group by rule_type, error_num, error_msg, username, module, action
order by total_occurrences desc
fetch first 10 rows only;
```

## Drill-down query pattern

```sql
select last_occurrence,
       occurrence_count,
       error_num,
       error_msg,
       rule_type,
       username,
       schema,
       module,
       action,
       client_id,
       sql_id,
       dbms_lob.substr(sql_text, 1000, 1) as sql_text_sample
from dba_lockdown_errors
where last_occurrence >= systimestamp - interval '24' hour
order by last_occurrence desc
fetch first 50 rows only;
```

## Interpretation guidance

Explain that lockdown errors indicate SQL statements blocked by Autonomous lockdown profile rules. They do not necessarily mean a database fault. They often indicate code, tool, privilege, or feature usage that is not allowed in the Autonomous environment.
