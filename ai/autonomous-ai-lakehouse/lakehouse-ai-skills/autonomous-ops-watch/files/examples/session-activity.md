# Example: Session Activity

## User prompt

Show active and blocking sessions.

## Expected response style

Source: `V$SESSION`

Summarize:

- active sessions grouped by username/module/action;
- long-running active sessions over the default threshold;
- blocking or final blocking sessions if visible;
- SQL IDs, wait class, and wait event when useful.

Do not include all inactive sessions unless the user asks for them.
