---
name: autonomous-data-loader
description: generate and safely execute oracle autonomous ai lakehouse data loading and oci object storage lakehouse access workflows using dbms_cloud. use when the user wants to list oci object storage files, choose files or prefixes to load, create conservative csv staging tables, generate or run copy_data or copy_collection, tune dbms_cloud format options, load json documents into soda collections, create external tables to query apache iceberg data stored in oci object storage using direct metadata.json or hadoop catalog patterns, monitor user_load_operations or dba_load_operations, inspect logfile_table or badfile_table, troubleshoot rejected rows, reconcile loads, or profile staged data after loading. this skill is mcp-first with generate-only fallback and is scoped to oci object storage and dbms_cloud-based workflows.
---

# Autonomous AI Lakehouse Data Loader

## Purpose

Use this skill to help users load data from OCI Object Storage into Oracle Autonomous AI Lakehouse with `DBMS_CLOUD`, and to create external-table access to Apache Iceberg data stored in OCI Object Storage. The skill is designed for a portable Agent Skill workflow: it can generate SQL/PLSQL for manual execution, or execute through an available MCP SQL tool when connected to the target Autonomous database.

## Core Scope

Handle these workflows:

- Discover objects in OCI Object Storage with `DBMS_CLOUD.LIST_OBJECTS`.
- Normalize Object Storage URIs and choose a file, selected file list, prefix, wildcard, or regex pattern.
- Prefer existing `DBMS_CLOUD` credential names and never request secrets in chat.
- Check whether target tables exist before generating `COPY_DATA`.
- Generate and optionally execute `DBMS_CLOUD.COPY_DATA` for supported file loads into existing relational tables.
- Generate and optionally execute `DBMS_CLOUD.COPY_COLLECTION` for JSON documents into SODA collections.
- For CSV without an existing target table, offer conservative staging from the CSV header using `VARCHAR2(4000)` columns.
- Generate format options for CSV, JSON, Parquet, ORC, and Avro. Treat XML as version-specific and verify official documentation before generating XML load workflows.
- Create and validate external tables that query Apache Iceberg data stored in OCI Object Storage, using only the direct `metadata.json` and HadoopCatalog-on-OCI patterns documented for Autonomous AI Database.
- Monitor and reconcile loads with native `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS`.
- Inspect `LOGFILE_TABLE` and `BADFILE_TABLE` after failures or rejected rows.
- Profile staged data after load and propose curated DDL only as a proposal.

Do not make Data Pump or `DBMS_CLOUD_PIPELINE` part of any default workflow. Do not add non-OCI Iceberg providers such as Unity, Polaris, AWS Glue, S3, Azure, or GCS to the default workflow.

## Execution Model

Default to MCP-enabled execution when a SQL execution tool is available. If no MCP SQL tool is available, use generate-only mode.

### MCP-enabled mode

- Use the available MCP SQL execution tool for read-only inspection queries.
- Do not assume a specific tool name. Prefer the SQL tool connected to the target Autonomous AI Lakehouse database.
- Execute read-only checks directly when useful: dictionary queries, `LIST_OBJECTS`, load-history queries, log and badfile inspection, Iceberg external-table sanity checks such as `COUNT(*)`.
- For mutating operations, generate the SQL/PLSQL first, explain the impact, and require approval before execution.

### Generate-only mode

- Generate SQL/PLSQL and ask the user to execute it manually in their preferred Oracle client.
- Ask the user to paste results back when the next step depends on inspection output.

## Approval Policy

Support two approval styles:

- **Strict approval**: ask before every mutating operation. This is the default.
- **Batch approval**: show the complete non-destructive mutating plan first, then execute the approved plan. Use only when the user asks for batch approval or clearly approves the entire plan.

Always require strict approval for destructive operations, even when batch approval is active.

Mutating operations include:

- `CREATE TABLE`, `ALTER TABLE`, `CREATE COLLECTION` patterns, and similar DDL.
- `DBMS_CLOUD.COPY_DATA`.
- `DBMS_CLOUD.COPY_COLLECTION`.
- `DBMS_CLOUD.COPY_COLLECTION` may create a missing SODA collection; treat it as mutating even before rows or documents are loaded.
- `DBMS_CLOUD.CREATE_CREDENTIAL`.
- `DBMS_CLOUD.CREATE_EXTERNAL_TABLE` for Iceberg access.
- `DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE` for Iceberg Object Storage ACL setup.
- `INSERT`, `UPDATE`, `DELETE`, `MERGE`.

Destructive operations include:

- `DROP TABLE`.
- `TRUNCATE TABLE`.
- `ALTER TABLE DROP COLUMN`.
- `DELETE` without a narrowly scoped predicate.
- Replacing, truncating, or recreating an existing staging table.

Prefer non-destructive alternatives, such as a new staging table name, before recommending destructive cleanup.

## Guardrails

- Never ask users to paste secrets, API keys, auth tokens, private keys, or passwords into the prompt.
- Prefer an existing `DBMS_CLOUD` credential name.
- If a credential is missing, generate a `CREATE_CREDENTIAL` template with placeholders and warn users to replace placeholders outside the chat.
- Do not infer a final CSV business schema from a filename, bucket, or folder alone.
- For CSV without a target table, ask whether the user wants conservative staging, a user-provided schema, or profiling first.
- Do not mix formats in a single `COPY_DATA` operation.
- Do not load from a whole prefix until object discovery shows the files are homogeneous enough.
- Exclude marker/control files such as `_SUCCESS`, `.crc`, manifests, readme files, and zero-byte files unless the user explicitly requests otherwise.
- Treat generated curated DDL as proposed until the user approves it.
- For Iceberg workflows, keep the scope to OCI Object Storage only and generate only external table access patterns; do not treat Iceberg as a `COPY_DATA` load.
- For Iceberg direct metadata, warn that the table points to a specific `metadata.json` snapshot and may need to be recreated after snapshot or schema changes.
- For Iceberg HadoopCatalog on OCI, require the lakehouse folder URI and `iceberg_table_path`.
- Warn users about documented Iceberg limitations before creating an external table: fixed external-table schema, no query-time time travel, unsupported merge-on-read delete files, and provider/version-specific restrictions.

## Workflow Decision Tree

1. Identify the source request:
   - bucket or prefix discovery: use `references/object-discovery-and-selection.md`.
   - direct relational table load: use `references/copy-data.md`.
   - JSON document collection load: use `references/copy-collection-json.md`.
   - Apache Iceberg data stored in OCI Object Storage: use `references/iceberg-oci-object-storage.md`.
   - failed load or rejected rows: use `references/monitoring-and-troubleshooting.md`.
   - CSV with no target table: use `references/csv-staging-and-profiling.md`.

2. Collect minimum inputs:
   - `credential_name` or instruction to create one.
   - OCI Object Storage URI, bucket/prefix, or exact file URI.
   - target table or collection name, unless the user wants discovery/planning only.
   - format or enough evidence to infer the format from selected object names.
   - for Iceberg: external table name, credential name, OCI Object Storage URI for `metadata.json` or lakehouse folder, and optionally `iceberg_table_path` for HadoopCatalog.

3. Run read-only pre-checks when MCP is available:
   - list object candidates with `DBMS_CLOUD.LIST_OBJECTS`.
   - check target table or collection existence.
   - inspect target columns when loading into a relational table.
   - inspect recent load history when troubleshooting.
   - inspect Iceberg metadata file or lakehouse folder candidates when building an Iceberg external table.

4. Plan the load or access pattern:
   - choose exact file list, prefix/wildcard, or regex pattern.
   - select `COPY_DATA`, `COPY_COLLECTION`, or `CREATE_EXTERNAL_TABLE` for Iceberg query access.
   - select format options or Iceberg access protocol configuration.
   - decide direct load versus user-named staging.

5. For mutating operations:
   - present the SQL/PLSQL.
   - explain the risk.
   - ask for strict or batch approval.
   - execute only after approval if MCP is available.

6. After execution:
   - query `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS` for load operations.
   - for Iceberg external tables, run a read-only sanity check such as `SELECT COUNT(*)` and inspect table columns.
   - reconcile status, operation id, start/update time, log table, badfile table, and row counts where possible.
   - if failed or rejected rows are present, switch to troubleshooting.
   - if CSV staging was used, offer post-load profiling and curated DDL proposal.

## Response Style

Be flexible and concise. Do not force every answer into a rigid template. For mutating or destructive operations, always clearly show:

- what will change,
- the SQL/PLSQL involved,
- whether approval is required,
- how to monitor the result,
- and how to troubleshoot failures.

For Iceberg external-table access, clearly state that the operation creates query access to data in Object Storage; it does not copy the Iceberg data into Autonomous.

## References

Use these files when relevant:

- `references/oracle-docs-index.md` for official Oracle documentation links.
- `references/version-notes.md` for the v0.1 scope and release notes.
- `references/minimum-inputs.md` for minimum required inputs by workflow.
- `references/object-discovery-and-selection.md` for object listing and file selection.
- `references/source-and-credentials.md` for OCI Object Storage credentials and URI patterns.
- `references/copy-data.md` for relational table loads with `DBMS_CLOUD.COPY_DATA`.
- `references/copy-collection-json.md` for JSON document loads into SODA collections.
- `references/format-options.md` for format option guidance.
- `references/iceberg-oci-object-storage.md` for querying Iceberg data in OCI Object Storage with external tables.
- `references/csv-staging-and-profiling.md` for CSV staging and post-load profiling.
- `references/monitoring-and-troubleshooting.md` for load monitoring, logs, badfiles, and retry guidance.
- `references/mcp-execution.md` for MCP-first execution behavior.

Use examples in `examples/` only when the user needs a concrete pattern.
