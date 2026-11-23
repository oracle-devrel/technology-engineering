# Oracle Database Developer Notebook Setup Kit

This kit uses **one administrator script and one schema script**. The scripts are designed for Oracle AI Database 26ai and for Autonomous AI Database 26ai, including Always Free environments.

## 1. Administrator script

Run `admin_setup.sql` once in the target PDB as the administrative account.

`DEMO_USER` is intentionally not hard-coded. If it is not already defined, the script prompts for it on first use. For a repeatable run you can define it first, for example `DEFINE DEMO_USER = 'DBDEV_DEMO'`, then run `@admin_setup.sql`.

The script:

- grants `DB_DEVELOPER_ROLE`;
- adds `CREATE ASSERTION`, `CREATE DATA ROLE`, and `CREATE DATA GRANT` for the developer stories that need them;
- creates `ONNX_DIR` for the optional in-database embedding path and grants the schema READ/WRITE access.

The directory path defaults to `onnx_model`, which is the form used in Oracle Autonomous AI Database examples. For a regular Oracle database, replace it with a database-server filesystem path accessible to Oracle. The script contains commented `DEFINE` examples for `DEMO_TABLESPACE`, `ONNX_DIR_NAME`, and `ONNX_DIR_PATH`.

## 2. Schema script

Run `schema_setup.sql` as the demo schema.

It checks:

- current container/schema;
- Oracle version and `COMPATIBLE`;
- `DB_DEVELOPER_ROLE` and additional privileges;
- required supplied packages used by the notebooks;
- schema segment usage;
- ONNX directory availability.

The script can also prepare the optional imported ONNX model without adding another setup script. It prompts for the ONNX model URI and file name so the model source is explicit. Leave the URI blank when `LOAD_ONNX_MODEL` is `N`; set `LOAD_ONNX_MODEL` to `Y` when the optional model should be downloaded and imported. Commented examples are included beside the input definitions.

## Autonomous Always Free guidance

Always Free Autonomous AI Database provides **20 GB of storage**. Keep notebook datasets deliberately small, avoid accumulating prior demo objects, and use the separate cleanup scripts between sessions. Imported ONNX models and vector indexes consume the same database resources as other schema objects. Oracle also documents a 20 GB storage limit for Autonomous AI Database for Developers instances. [Oracle Autonomous AI Database Always Free](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-always-free.html) [Oracle Autonomous AI Database for Developers](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-for-developers.html)

## Optional ONNX embedding path

The in-database embedding notebook is intentionally more prescriptive than the core notebooks.

For Autonomous AI Database, the recommended setup is:

1. Use a compatible embedding model in ONNX format.
2. Store it in Oracle Object Storage or another reachable location.
3. Ensure the demo schema can use `ONNX_DIR`.
4. Run `schema_setup.sql` with `LOAD_ONNX_MODEL = 'Y'` and the model URI.
5. Confirm the model appears in `USER_MINING_MODELS` and `USER_MINING_MODEL_ATTRIBUTES`.
6. Run the optional embedding notebook.

Oracle's 26ai documentation shows both the directory-based `DBMS_VECTOR.LOAD_ONNX_MODEL` path and cloud/Object Storage approaches. `DBMS_VECTOR.UTL_TO_EMBEDDING` and `VECTOR_EMBEDDING` can then invoke the registered database model. [Import ONNX Models](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/import-onnx-models-oracle-ai-database-end-end-example.html) [SQL Quick Start](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/sql-quick-start-using-vector-embedding-model-uploaded-database.html) [Text to Embedding](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/convert-text-string-embedding-oracle-ai-database.html)

For Autonomous AI Database, the documented examples use `DBMS_CLOUD.GET_OBJECT` to place a model in the database directory and then `DBMS_VECTOR.LOAD_ONNX_MODEL`. A pre-authenticated Object Storage URL can be used without a stored credential when the URL permits anonymous retrieval. [Oracle Autonomous examples](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/select-ai-examples.html)

### Model and storage considerations

- The ONNX model must be compatible with Oracle's embedding-model requirements and include the necessary inputs/outputs for the chosen workflow.
- The database must be able to retrieve the model file, and the model consumes database storage while present.
- Imported models are not automatically shared in memory; `INMEMORY_ONNX_MODEL` is a separate, optional memory decision. Do not enable it in the standard setup script without understanding the memory impact. [Oracle INMEMORY_ONNX_MODEL](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/inmemory_onnx_model-dbms_vector.html)
- Vector indexes have memory/resource implications in addition to storage. Keep the core demo corpus small on free-tier environments.

## Deep Data Security

The standard administrator setup grants the privileges needed for the current notebook to create data roles and data grants. Runtime identity-aware testing is a separate environment concern. Autonomous AI Database supports Deep Data Security, but enterprise-authenticated testing requires IAM or Microsoft Entra ID configuration and end-user identity propagation. [Oracle Deep Data Security in Autonomous AI Database](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/deep-data-security.html)

## MLE preparation

The Program the Database notebook uses persistent MLE JavaScript modules and a SQL/PLSQL call specification. In Oracle AI Database 26ai, MLE execution must not be disabled for the effective CDB/PDB/session. Creating an MLE module in the developer's own schema requires `CREATE MLE`; publishing it through a SQL/PLSQL call specification also requires `CREATE PROCEDURE`. The standard `DB_DEVELOPER_ROLE` used by this archive supplies these privileges. The schema setup script reports the `MLE_PROG_LANGUAGES` setting and the relevant privileges; it does not silently alter the database configuration. `EXECUTE ON JAVASCRIPT` is not required for MLE in the developer's own schema in 26ai.

For the short MLE demo, no external JavaScript package installation is required. Third-party modules are supported, but package-specific deployment is deliberately outside the 60-minute session scope.

## Table DDL Change Notification

This feature is **not part of the standard Autonomous/Always Free preparation**. It is an OCI-client capability. Oracle documents requirements for a non-SYS user, `SELECT ANY TABLE`, `CHANGE NOTIFICATION`, and TCP/IPC listener plus `LOCAL_LISTENER` configuration. It should therefore be treated as an optional environment-specific demonstration rather than a core SQL Notebook requirement. [Oracle Table DDL Change Notification](https://docs.oracle.com/en/database/oracle/oracle-database/26/adfns/using-table-ddl-change-notification.html)

## Notebook cleanup

The existing per-story cleanup scripts remain the teardown mechanism. The setup scripts do not drop or recreate the story objects because the notebooks intentionally own their demonstration state.

## Credentials

The setup scripts contain no passwords or default password values. Supply account names and any external-service credentials through the execution environment when required. Do not embed passwords in shared scripts.
