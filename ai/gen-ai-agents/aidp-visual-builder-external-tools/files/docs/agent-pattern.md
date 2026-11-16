# Agent pattern

The agent receives a request, decides which connected tools to call, reads their results, and writes one answer. Tool descriptions and agent instructions help it choose correctly.

A useful mixed-data pattern is:

1. Database tool: find facts in table rows.
2. Document search: retrieve relevant guidance or case notes.
3. Agent: explain which source supports each fact and prepare a human-reviewed draft.
4. Optional action tool: prepare a draft or other bounded output.

Do not ask the model to guess when a tool returns no result. Tell it to say which source is missing. Keep tools read-only until a real use case needs a change. For actions that send messages or update records, add an approval step and audit trail.

A Supervisor flow is useful when separate agents own clear sub-tasks and the supervisor must route work. It is not required just to connect several tools to one agent.
