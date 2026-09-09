# MCP-first execution

This skill is designed for environments where an MCP SQL execution tool may already be connected to Oracle Autonomous AI Lakehouse.

## Execution modes

### MCP-enabled mode

Use this mode when an SQL execution tool is available. Do not assume the tool name. It may be exposed as `execute_sql`, `run_sql`, `oracle_sql`, `sqlcl`, `adb_execute_sql`, or another name.

Use MCP directly for read-only operations, including:

- data dictionary checks,
- `DBMS_CLOUD.LIST_OBJECTS`,
- `USER_LOAD_OPERATIONS` and `DBA_LOAD_OPERATIONS` queries,
- `LOGFILE_TABLE` and `BADFILE_TABLE` inspection,
- profiling queries against staging tables.

Require approval before mutating operations:

- `CREATE TABLE`, `ALTER TABLE`, `DROP TABLE`, `TRUNCATE TABLE`,
- `DBMS_CLOUD.COPY_DATA`,
- `DBMS_CLOUD.COPY_COLLECTION`,
- `DBMS_CLOUD.CREATE_CREDENTIAL`,
- `INSERT`, `UPDATE`, `DELETE`, `MERGE`.

Destructive operations always require strict per-operation approval.

### Generate-only fallback

When no MCP SQL tool is available, generate SQL/PLSQL and ask the user to run it manually. Ask the user to paste back results for the next step.

## Approval styles

Default to strict approval. Allow batch approval for non-destructive plans when the user asks for it.

Batch approval rules:

- Show the complete SQL/PLSQL plan before execution.
- Include only the listed mutating operations in the batch.
- Stop on first failure.
- Switch to troubleshooting after failure.
- Do not hide destructive steps inside a batch.

## Result handling

After any load operation, inspect `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS`. If an operation reports `FAILED`, rejected rows, or a non-empty badfile table, inspect the log and badfile tables next.

## Iceberg MCP behavior

For Iceberg on OCI Object Storage, use MCP directly for read-only operations such as:

- checking whether the external table name already exists,
- listing candidate `metadata.json` files or HadoopCatalog folders with `DBMS_CLOUD.LIST_OBJECTS`,
- running `SELECT COUNT(*)` after external table creation,
- inspecting `USER_TAB_COLUMNS` for the created external table.

Require approval before mutating Iceberg operations:

- `DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE`,
- `DBMS_CLOUD.CREATE_EXTERNAL_TABLE`,
- dropping or recreating an Iceberg external table.
