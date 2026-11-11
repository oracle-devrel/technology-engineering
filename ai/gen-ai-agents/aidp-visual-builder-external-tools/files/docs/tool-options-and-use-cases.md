# Pick the right tools

Keep the first version small. Give the agent only the tools needed for its task.

| Tool | In plain words | Example |
|---|---|---|
| SQL / Select AI | Ask questions about rows and columns in a database. | “How many late deliveries were recorded last month?” |
| RAG / vector search | Find useful parts of documents by meaning. | “What does the delivery guide say to include in a follow-up?” |
| HTTP | Call a web API using a URL and request settings. | Check a ticket status or look up an approved service. |
| Remote MCP | Connect to an MCP server that offers one or more tools. | Reuse a database or company service MCP tool. |
| Custom Tool | Run a small Python function when the other choices do not fit. | Format a report, validate required fields, or combine a few local steps. |
| Prompt | Ask a model to rewrite or summarize text. | Turn notes into a short plain-English handoff. |

## A realistic pattern

For a monthly vendor delivery review, the agent can:

1. Use the database tool to check delivery records and scores.
2. Search approved guidance for the evidence to request.
3. Compare the tool results and say which source supports each point.
4. Draft a short message for a person to review.

The included Select AI Custom Tool calls the database MCP service. Its actual access is controlled by the database user and Select AI profile, so give it a least-privilege, read-only database user for this review task.

Other useful company tasks include support case summaries, IT troubleshooting with a policy lookup, sales meeting preparation, and incident handoffs. Each can combine structured records with relevant documents and then prepare a human-reviewed draft.

## When to use more than one agent

A single agent with well-described tools is a good first version. Add Supervisor/Executor or specialist agents when tasks are genuinely separate, such as one agent checking records, another searching policy, and a supervisor combining their results. More agents add setup and debugging work, so use them only when routing makes the result clearer.

## Production notes

Keep the first version read-only. If you later add a tool that changes data or triggers an external action, add access checks, audit logging, and a human approval step.
