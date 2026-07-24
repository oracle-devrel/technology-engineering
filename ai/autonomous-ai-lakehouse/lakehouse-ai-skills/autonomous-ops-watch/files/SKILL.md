---
name: autonomous-ops-watch
description: inspect sql-observable operational evidence for one connected oracle autonomous ai lakehouse. use when users ask for maintenance notifications, patch identifiers or patch details, client errors, lockdown profile errors, operator access audit evidence, unified audit highlights, active or blocking sessions, invalid objects, compile errors, table or partition access statistics, or an operations summary based only on sql evidence. this skill is read-only, sql/mcp-first, and does not use oci apis, oci events, console, cli, lifecycle actions, resource principal views, or external schedulers.
---

# Autonomous AI Lakehouse Ops Watch

## Purpose

Use this skill to help operations teams inspect SQL-observable operational evidence for a single connected Oracle Autonomous AI Lakehouse. The skill is read-only and evidence-focused: it summarizes what can be observed through SQL views and dictionary objects, not what can be certified about the whole environment.

## Core rules

- Use only SQL-observable evidence from the connected Autonomous AI Lakehouse database.
- Treat the active MCP or SQL connection as the target database.
- Execute only `SELECT` statements in v0.1.
- If an MCP or SQL execution tool is available, execute read-only queries after briefly explaining what evidence will be inspected.
- If no SQL execution tool is available, generate SQL for the user to run manually.
- Always mention the SQL source view or dictionary object used.
- Prefer concise operational summaries over raw SQL output.
- Show full SQL only when the user asks for it, no SQL tool is available, or manual execution is required.
- Never certify that the database is healthy, safe, or ready for patching.
- Never perform OCI lifecycle actions or database configuration changes.
- Clearly state privilege or visibility limits when evidence may be incomplete.

## Limitations

This skill does not:

- certify that an Autonomous AI Lakehouse is ready for patching;
- certify operational health or safety;
- perform lifecycle operations;
- start, stop, restart, scale, terminate, clone, restore, or patch databases;
- use OCI API, OCI Events, Console, CLI, SDK, or Resource Principal views;
- inspect multiple Autonomous databases automatically;
- inspect external ETL jobs or schedulers;
- inspect OCI Logging, OCI Monitoring, Object Storage posture, cost, or budgets;
- enable, disable, or modify operator access;
- execute mutating SQL.

## Default time windows

Use these defaults unless the user provides a different time window:

- Client errors: last 24 hours.
- Lockdown profile errors: last 24 hours.
- Unified audit highlights: last 24 hours.
- Operator access: last 7 days.
- Session activity and blocking: current state.
- Invalid objects and compile errors: current state.
- Table and partition access stats: since instance startup, because that is how the views behave.
- Maintenance notifications: recent rows ordered by notification time.
- Patch details: only when the user asks for patch contents, bug fixes, or a specific patch version.

## Capability routing

Use these references based on the user request:

- Maintenance notifications, next maintenance, recent maintenance, patch id: see `references/maintenance-notifications.md`.
- Patch contents, bug fixes, or patch version details: see `references/patch-details.md`.
- Lockdown profile errors or SQL blocked by Autonomous restrictions: see `references/lockdown-errors.md`.
- Client ORA errors, repeated failures, SQL IDs associated with client errors: see `references/client-errors.md`.
- Oracle Cloud Operations / operator access audit evidence: see `references/operator-access.md`.
- Failed logins, password changes, grants, sensitive DDL, or audit evidence: see `references/unified-audit.md`.
- Active sessions, blocking sessions, long-running active sessions: see `references/session-activity.md`.
- Invalid objects or compile errors: see `references/invalid-objects.md`.
- Hot tables, scan counts, or table/partition access stats: see `references/table-access-stats.md`.
- Broad operational evidence summary: see `references/ops-summary.md`.
- Privilege fallbacks and visibility caveats: see `references/privilege-and-visibility.md`.
- Official documentation links: see `references/oracle-docs-index.md`.

## Ops summary behavior

When the user asks for an operations summary, inspect SQL-visible evidence only. Include by default:

1. Maintenance notifications from `DB_NOTIFICATIONS`.
2. Aggregated client errors from `V$CLIENT_ERRORS`.
3. Aggregated lockdown profile errors from `DBA_LOCKDOWN_ERRORS`.
4. Operator access audit evidence from `DBA_OPERATOR_ACCESS` and operator access configuration from `DBA_CLOUD_CONFIG`, when visible.
5. Compact unified audit highlights from `UNIFIED_AUDIT_TRAIL`.
6. Active, long-running active, and blocking session snapshot from `V$SESSION`.
7. Invalid object and compile error summary from `ALL_OBJECTS` / `ALL_ERRORS` or DBA equivalents when available.

Do not include table or partition access stats in the default ops summary unless the user asks for hot objects, scan counts, or object access evidence.

Do not include full patch fix details in the default ops summary. Show patch ids from maintenance notifications only, and ask the user if they want patch details.

Use language such as: "Based on SQL-observable evidence..." rather than absolute health claims.

## SQL text exposure

For views that may include SQL text, show truncated samples only by default. This applies to sources such as:

- `DBA_LOCKDOWN_ERRORS.SQL_TEXT`
- `UNIFIED_AUDIT_TRAIL.SQL_TEXT`
- any client error or diagnostic source that exposes SQL text

Include `SQL_ID` where available. Provide full SQL text only if the user explicitly asks for it and it is appropriate to reveal.

## Privilege fallback

Prefer `USER_*` or `ALL_*` views when they provide enough evidence. Use `DBA_*`, `V$`, or `GV$` views when the connected user has privileges. If a DBA-level query fails, retry with USER or ALL scope where possible. Never interpret missing privileges or empty DBA views as proof that no issue exists.

## Response style

Be flexible. Adapt to the user's question. When summarizing operational evidence, clearly separate:

- observed SQL evidence;
- interpretation;
- limitations or visibility gaps;
- suggested follow-up.

Keep summaries concise. Offer drill-down dimensions such as time window, user, module, action, SQL ID, object owner, object type, or error number.
