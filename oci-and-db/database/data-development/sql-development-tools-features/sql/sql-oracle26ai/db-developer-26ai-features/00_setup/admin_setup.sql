-- Oracle Database Developer Notebook Environment
-- Run once as the database administrator in the target PDB.
-- Designed for Oracle AI Database 26ai and Autonomous AI Database 26ai.
--
-- Required input:
--   DEMO_USER       schema that will execute the notebooks
--
-- MLE note:
--   26ai MLE execution must not be disabled at CDB/PDB/session level. This
--   script does not force-enable MLE; the schema preflight reports the current
--   MLE_PROG_LANGUAGES setting so an administrator can correct an OFF setting.
--
-- Optional input:
--   DEMO_TABLESPACE tablespace for a regular database (ignored on Autonomous)
--   ONNX_DIR_NAME   directory object used by the optional in-database embedding path
--   ONNX_DIR_PATH   use 'onnx_model' for Autonomous AI Database; for a regular
--                   database use an OS path accessible to the database server

-- DEMO_USER is intentionally not given a dummy default. If it has not already
-- been DEFINEd by the caller, SQL*Plus/SQLcl prompts for it at the first &&DEMO_USER.
-- Example before running this script:
--   DEFINE DEMO_USER = 'DBDEV_DEMO'
--   @admin_setup.sql
--
-- Other inputs have safe defaults. Override them before running the script when needed.
DEFINE DEMO_TABLESPACE = 'USERS'
DEFINE ONNX_DIR_NAME = 'ONNX_DIR'
DEFINE ONNX_DIR_PATH = 'onnx_model'
-- Regular database example:
--   DEFINE DEMO_TABLESPACE = 'USERS'
--   DEFINE ONNX_DIR_NAME = 'ONNX_DIR'
--   DEFINE ONNX_DIR_PATH = '/u01/app/oracle/demo_models'

SET VERIFY OFF
SET SERVEROUTPUT ON

PROMPT ============================================================
PROMPT Oracle Database Developer notebook - administrator setup
PROMPT ============================================================
PROMPT Target schema : &&DEMO_USER
PROMPT ONNX directory: &ONNX_DIR_NAME
PROMPT ONNX location : &ONNX_DIR_PATH
PROMPT

PROMPT -- Grant the standard Oracle developer role
GRANT DB_DEVELOPER_ROLE TO &DEMO_USER;

PROMPT -- Additional privileges used by the developer notebooks
-- DB_DEVELOPER_ROLE supplies CREATE DOMAIN, CREATE MLE, CREATE MINING MODEL,
-- CREATE PROCEDURE, CREATE TABLE, CREATE VIEW, EXECUTE DYNAMIC MLE, etc.
-- For the MLE notebook, CREATE MLE is needed for modules and CREATE PROCEDURE
-- is needed for the SQL/PLSQL call specification. In 26ai a separate
-- EXECUTE ON JAVASCRIPT grant is not required for MLE in your own schema.
-- These three capabilities are not part of the standard role privilege set.
GRANT CREATE ASSERTION TO &DEMO_USER;
GRANT CREATE DATA ROLE TO &DEMO_USER;
GRANT CREATE DATA GRANT TO &DEMO_USER;

PROMPT -- Check the database developer role grant
SELECT grantee, granted_role
FROM   dba_role_privs
WHERE  grantee = UPPER('&DEMO_USER')
AND    granted_role = 'DB_DEVELOPER_ROLE';

PROMPT -- Check the additional developer privileges
SELECT privilege
FROM   dba_sys_privs
WHERE  grantee = UPPER('&DEMO_USER')
AND    privilege IN ('CREATE ASSERTION','CREATE DATA ROLE','CREATE DATA GRANT')
ORDER BY privilege;

PROMPT
PROMPT -- Create the ONNX staging directory used by the optional embedding path.
PROMPT -- Autonomous AI Database uses a database-managed directory name such as
PROMPT -- 'onnx_model'; the model file is placed there with DBMS_CLOUD.GET_OBJECT.
CREATE OR REPLACE DIRECTORY &ONNX_DIR_NAME AS '&ONNX_DIR_PATH';
GRANT READ, WRITE ON DIRECTORY &ONNX_DIR_NAME TO &DEMO_USER;

PROMPT -- Verify the ONNX directory
SELECT directory_name, directory_path
FROM   dba_directories
WHERE  directory_name = UPPER('&ONNX_DIR_NAME');

SELECT grantee, privilege
FROM   dba_tab_privs
WHERE  owner = 'SYS'
AND    table_name = UPPER('&ONNX_DIR_NAME')
AND    grantee = UPPER('&DEMO_USER')
ORDER BY privilege;

PROMPT
PROMPT -- Regular database quota (skip/adjust this statement if your platform
PROMPT -- manages quotas differently, including Autonomous AI Database).
PROMPT -- Example for a regular PDB:
PROMPT -- ALTER USER &DEMO_USER QUOTA 1G ON &DEMO_TABLESPACE;

PROMPT ============================================================
PROMPT Administrator setup complete
PROMPT ============================================================
PROMPT
PROMPT The standard notebook path needs no further administrator script.
PROMPT MLE is ready when DB_DEVELOPER_ROLE is granted and MLE_PROG_LANGUAGES
PROMPT is not OFF at the target CDB/PDB/session scope. The schema preflight checks this setting.
PROMPT Optional in-database embeddings are completed by the schema setup script
PROMPT after a compatible ONNX model is available to ONNX_DIR.
PROMPT
PROMPT Table DDL Change Notification is deliberately not granted here: it is an
PROMPT OCI client capability requiring SELECT ANY TABLE, CHANGE NOTIFICATION and
PROMPT listener/LOCAL_LISTENER configuration. It should be prepared only in an
PROMPT environment intended for that OCI demonstration.
