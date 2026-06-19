# Example: Operator Access

## User prompt

Has Oracle Cloud Operations accessed this database recently?

## Expected response style

Source: `DBA_OPERATOR_ACCESS`, `DBA_CLOUD_CONFIG`

Summarize:

- operator access configuration if visible;
- Oracle Cloud Operations actions in the last 7 days;
- timestamp, request id, reason, and SQL/action summary when available.

Do not enable or disable operator access. v0.1 is read-only.
