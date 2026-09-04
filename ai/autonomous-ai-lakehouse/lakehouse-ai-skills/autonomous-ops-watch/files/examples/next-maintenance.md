# Example: Next Maintenance

## User prompt

When is the next maintenance window?

## Expected response style

Source: `DB_NOTIFICATIONS`

I found the following SQL-visible maintenance evidence:

- Next scheduled maintenance: show expected start/end if available.
- In-progress maintenance: show if present.
- Last completed maintenance: show actual start/end and status as one compact line.
- Patch id: show if present.

This is maintenance notification evidence only. It does not certify application readiness for the maintenance window.
