# Session Activity and Blocking Snapshot

Use this reference when the user asks about active sessions, blocking sessions, long-running active sessions, module activity, or possible connection leaks.

## Source

Primary sources:

- `V$SESSION`
- `GV$SESSION` when available and useful

Official docs:
- Autonomous events include session-related examples: https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-events.html
- `V$SESSION` reference: https://docs.oracle.com/en/database/oracle/oracle-database/21/refrn/V-SESSION.html

## Behavior

- Include active, blocking, and long-running active session signals in the default ops summary.
- Do not include all inactive sessions by default.
- Include inactive sessions only when the user asks, investigates connection leaks, or gives a threshold.
- Default long-running active threshold: 30 minutes.
- Show `MODULE`, `ACTION`, `SQL_ID`, wait event, and wait class when useful.
- Do not kill sessions or recommend session termination as an action in v0.1.

## Active sessions by module

```sql
select username,
       module,
       action,
       status,
       count(*) as session_count
from v$session
where username is not null
  and status = 'ACTIVE'
group by username, module, action, status
order by session_count desc;
```

## Long-running active sessions

```sql
select sid,
       serial#,
       username,
       module,
       action,
       sql_id,
       status,
       last_call_et,
       event,
       wait_class
from v$session
where username is not null
  and status = 'ACTIVE'
  and last_call_et > 1800
order by last_call_et desc;
```

## Blocking sessions

```sql
select sid,
       serial#,
       username,
       module,
       action,
       blocking_session_status,
       blocking_instance,
       blocking_session,
       final_blocking_session_status,
       final_blocking_instance,
       final_blocking_session,
       event,
       wait_class
from v$session
where blocking_session_status = 'VALID'
   or final_blocking_session_status = 'VALID'
order by username, module, action;
```

## Optional inactive sessions query

```sql
select sid,
       serial#,
       username,
       module,
       action,
       status,
       last_call_et
from v$session
where username is not null
  and status = 'INACTIVE'
  and last_call_et > :inactive_seconds
order by last_call_et desc;
```
