# Select AI Custom Tool for AIDP

This package adds an AIDP Custom Tool called **Query Supplier Feedback**. It sends a natural-language question to the `SUPPLIER_FEEDBACK_SQL` tool exposed by an Autonomous AI Database MCP endpoint. The database runs Select AI and returns the rows. The Python code does not contain a key, password, database OCID, or customer data.

## Before uploading

The database must already have:

- A Select AI profile scoped to the table(s) the agent may query.
- The database MCP server enabled.
- A Select AI Agent tool named `SUPPLIER_FEEDBACK_SQL` with required inputs `ACTION` and `QUERY`. `ACTION` accepts `runsql`; `QUERY` receives the natural-language question.
- A database user with permission to call the MCP tool and use the profile. Use a dedicated least-privilege user for production.

See Oracle’s [Select AI profile guide](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/select-ai-manage-profiles.html) and [Autonomous Database MCP Server guide](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/use-mcp-server.html) to configure these database-side pieces.

## Add the database login to AIDP

In AIDP **Credential Store**, create a **Secret Token** credential with two keys:

- `username` — your database user name
- `password` — that database user's password

Use your own credential name. The package includes no credential values. At runtime it reads those values from Credential Store, requests a short-lived database token, and does not return or log the token.

## Upload and configure

1. Attach an active AI Compute to the agent.
2. Add egress for `dataaccess.adb.<your-region>.oraclecloudapps.com`.
3. Add a **Custom Tool** node and upload [`select-ai-custom-tool.zip`](select-ai-custom-tool.zip).
4. Select `SupplierFeedbackQuery` and attach it to the agent.
5. In its **Configuration** settings, fill in:
   - `region`: your database's region identifier
   - `database_ocid`: your database OCID
   - `credential_name`: the name you chose above
   - `username_key`: `username`
   - `password_key`: `password`
   - `timeout_seconds`: `45`
6. Save. Test with a question about the table in your Select AI profile.

The configuration values are for your environment and should not be committed to Git. Keep the region, OCID, and credential name in AIDP settings; the secret values remain in Credential Store.

## Source

The readable package source is in [`source/`](source/). The ZIP has `tool_config.json` and `tool_implementation.py` at its root, as AIDP requires. See [AIDP Custom Tool documentation](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/agent-flow-tools.html) for upload details.
