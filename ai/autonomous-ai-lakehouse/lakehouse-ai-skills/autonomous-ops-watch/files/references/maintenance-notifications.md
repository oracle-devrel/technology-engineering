# Maintenance Notifications

Use this reference when the user asks about next maintenance, recent maintenance, in-progress maintenance, patch identifiers, or maintenance history visible from SQL.

## Source

Primary source: `DB_NOTIFICATIONS`

Official docs:
- Autonomous maintenance and patching: https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/maintenance-windows-patching.html

## Behavior

- Include maintenance notifications in the default ops summary.
- Show next scheduled maintenance if visible.
- Show in-progress maintenance if visible.
- Show last completed maintenance as one compact line.
- Include `PATCH_ID` when available.
- Include expected and actual start/end times when available.
- Do not infer patch readiness, safety, or application impact from this view alone.
- Do not expand patch bug details unless the user asks for patch contents.

## Query pattern

```sql
select type,
       time,
       expected_start_date,
       expected_end_date,
       actual_start_date,
       actual_end_date,
       maintenance_product,
       maintenance_status,
       description,
       patch_id
from db_notifications
where type = 'MAINTENANCE'
order by time desc
fetch first 20 rows only;
```

## Summary guidance

Summarize compactly:

- next scheduled or in-progress maintenance;
- last completed maintenance;
- patch id when visible;
- visibility limitations.

Example phrasing:

"Source: DB_NOTIFICATIONS. I found one scheduled maintenance window and one recently completed maintenance entry. This is SQL-observable maintenance evidence only; it does not certify readiness for patching."
