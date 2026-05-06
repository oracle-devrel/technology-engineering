# Privilege and Visibility Rules

Use this reference whenever a query may require privileges that the connected SQL user may not have.

## Core rules

- Prefer `USER_*` or `ALL_*` views when they provide useful evidence.
- Use `DBA_*`, `V$`, or `GV$` views when the user has privileges.
- If a DBA-level query fails, retry with a USER or ALL equivalent when possible.
- Never interpret lack of privileges as absence of issues.
- Never interpret an empty result as a clean bill of health when the user has limited visibility.
- Explicitly state when evidence is partial.

## Useful fallback patterns

Invalid objects:

- Try `ALL_OBJECTS` first for visible objects.
- Use `DBA_OBJECTS` only if broader database visibility is needed and available.

Compile errors:

- Try `ALL_ERRORS` or `USER_ERRORS` first.
- Use `DBA_ERRORS` only when available.

Table access stats:

- Try `ALL_TABLE_ACCESS_STATS` or `USER_TABLE_ACCESS_STATS` first.
- Use `DBA_TABLE_ACCESS_STATS` only when available.

Operator and lockdown evidence:

- `DBA_OPERATOR_ACCESS`, `DBA_CLOUD_CONFIG`, and `DBA_LOCKDOWN_ERRORS` may not have USER or ALL equivalents. If they are not visible, say the evidence is unavailable to the connected user.

## Safe phrasing

Use:

"I could not query `DBA_LOCKDOWN_ERRORS` with the connected user. This means lockdown error evidence is not visible through this connection, not that there are no lockdown errors."

Avoid:

"There are no lockdown errors."

unless the correct view was queried successfully and the time window is clear.
