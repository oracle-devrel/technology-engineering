# Example: Ops Summary

## User prompt

Give me an ops summary for this Autonomous AI Lakehouse.

## Expected behavior

Briefly explain that SQL-visible evidence will be inspected, then query the default evidence sources if an MCP/SQL tool is available.

## Expected response style

Source views inspected: `DB_NOTIFICATIONS`, `V$CLIENT_ERRORS`, `DBA_LOCKDOWN_ERRORS`, `DBA_OPERATOR_ACCESS`, `DBA_CLOUD_CONFIG`, `UNIFIED_AUDIT_TRAIL`, `V$SESSION`, `ALL_OBJECTS`, `ALL_ERRORS`.

Based on SQL-observable evidence from the connected Autonomous AI Lakehouse:

- Maintenance: next scheduled maintenance is visible; last completed maintenance is also visible. Patch ids are shown when present.
- Client errors: summarize top errors from the last 24 hours, if any.
- Lockdown errors: summarize top lockdown rule types and errors from the last 24 hours, if visible.
- Operator access: show whether operator access configuration and recent Oracle Cloud Operations actions are visible.
- Audit: show compact ops-focused audit highlights from the last 24 hours.
- Sessions: show active, long-running active, and blocking session signals.
- Invalid objects: summarize invalid object and compile error counts.

Do not say the database is healthy or ready for patching. Offer drill-downs.
