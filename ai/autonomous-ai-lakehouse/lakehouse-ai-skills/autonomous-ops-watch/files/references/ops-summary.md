# Ops Summary Workflow

Use this reference when the user asks for an operations summary, operational evidence, a quick state of the connected Autonomous AI Lakehouse, or a concise ops check.

## Principle

The ops summary is evidence-only. It must not conclude that the database is healthy, safe, or ready for patching. Use phrasing such as:

"Based on SQL-observable evidence from the connected Autonomous AI Lakehouse..."

## Default evidence sources

Inspect these sources by default when MCP or SQL execution is available:

1. `DB_NOTIFICATIONS` for maintenance notifications and patch ids.
2. `V$CLIENT_ERRORS` for aggregated client errors in the last 24 hours.
3. `DBA_LOCKDOWN_ERRORS` for aggregated lockdown profile errors in the last 24 hours, if visible.
4. `DBA_OPERATOR_ACCESS` and `DBA_CLOUD_CONFIG` for operator access evidence, if visible.
5. `UNIFIED_AUDIT_TRAIL` for compact ops-focused audit highlights in the last 24 hours.
6. `V$SESSION` for active, long-running active, and blocking sessions.
7. `ALL_OBJECTS` / `ALL_ERRORS` or DBA equivalents for invalid objects and compile errors.

Do not include by default:

- table and partition access stats;
- full patch details from `DBA_CLOUD_PATCH_INFO`;
- full SQL text samples;
- lifecycle recommendations;
- OCI-side evidence.

## Recommended summary shape

Use a flexible response, but include the important pieces:

- Source views inspected.
- Observed evidence.
- Interpretation.
- Visibility limits.
- Suggested drill-down questions.

## Example summary language

"I inspected SQL-visible operational evidence from `DB_NOTIFICATIONS`, `V$CLIENT_ERRORS`, `DBA_LOCKDOWN_ERRORS`, `DBA_OPERATOR_ACCESS`, `UNIFIED_AUDIT_TRAIL`, `V$SESSION`, `ALL_OBJECTS`, and `ALL_ERRORS`. This is not a readiness certification; it is a snapshot of evidence visible to the connected SQL user."
