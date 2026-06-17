# Example: Client Errors

## User prompt

Show client errors from the last 24 hours.

## Expected response style

Source: `V$CLIENT_ERRORS`

Summarize:

- total visible client errors;
- top error numbers/messages by count;
- affected username/module/action when useful;
- latest occurrence;
- SQL ID when available.

Do not list every occurrence by default. Offer drill-down by error number, user, module, action, SQL ID, or time window.
