# Example: Lockdown Profile Errors

## User prompt

Show lockdown profile errors.

## Expected response style

Source: `DBA_LOCKDOWN_ERRORS`

Summarize the last 24 hours by default:

- total visible lockdown error records;
- top rule types;
- top error numbers/messages;
- affected usernames/modules/actions;
- latest occurrence;
- truncated SQL sample only when useful.

Explain that lockdown errors indicate SQL blocked by Autonomous lockdown profile rules and do not necessarily mean a database outage.
