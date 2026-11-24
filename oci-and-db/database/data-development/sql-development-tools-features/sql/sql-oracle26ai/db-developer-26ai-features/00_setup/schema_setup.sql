-- Oracle Database Developer Notebook Environment
-- Run as the schema that will execute the developer notebooks.
-- This script performs the schema preflight and can optionally prepare the
-- in-database embedding model used by the optional AI notebook.

DEFINE ONNX_DIR_NAME = 'ONNX_MODEL_DIR'
DEFINE ONNX_MODEL_NAME = 'DEMO_MINILM'
DEFINE LOAD_ONNX_MODEL = 'N'
-- Examples for the defined inputs:
--   DEFINE ONNX_DIR_NAME = 'ONNX_DIR'
--   DEFINE ONNX_MODEL_NAME = 'DEMO_MINILM'
--   DEFINE LOAD_ONNX_MODEL = 'Y'
--
-- The URI and file name are requested below so the model source is explicit.
-- Example values:
--   ONNX_MODEL_URI  = https://objectstorage.example/.../all_MiniLM_L12_v2.onnx
--   ONNX_MODEL_FILE = all_MiniLM_L12_v2.onnx
-- Press Enter for the URI when LOAD_ONNX_MODEL=N and the optional model is not required.
ACCEPT ONNX_MODEL_URI CHAR PROMPT 'ONNX model URI (blank when not loading): '
ACCEPT ONNX_MODEL_FILE CHAR DEFAULT 'all_MiniLM_L12_v2.onnx' PROMPT 'ONNX model file [all_MiniLM_L12_v2.onnx]: '

SET VERIFY OFF
SET SERVEROUTPUT ON

PROMPT ============================================================
PROMPT Oracle Database Developer notebook - schema setup
PROMPT ============================================================

PROMPT -- Connection and database version
SELECT SYS_CONTEXT('USERENV','CON_NAME') AS container_name,
       SYS_CONTEXT('USERENV','SESSION_USER') AS session_user,
       SYS_CONTEXT('USERENV','CURRENT_SCHEMA') AS current_schema
FROM dual;

SELECT banner
FROM   v$version
WHERE  banner LIKE 'Oracle%';

PROMPT
PROMPT -- Compatibility
SELECT name, value
FROM   v$parameter
WHERE  name = 'compatible';

PROMPT
PROMPT -- Standard developer role and additional privileges
SELECT granted_role
FROM   user_role_privs
WHERE  granted_role = 'DB_DEVELOPER_ROLE';

SELECT privilege
FROM   session_privs
WHERE  privilege IN (
         'CREATE ASSERTION',
         'CREATE DATA ROLE',
         'CREATE DATA GRANT',
         'CREATE DOMAIN',
         'CREATE MINING MODEL',
         'CREATE MLE',
         'CREATE PROCEDURE',
         'CREATE TABLE',
         'CREATE VIEW',
         'EXECUTE DYNAMIC MLE'
       )
ORDER BY privilege;

PROMPT
PROMPT -- MLE readiness
SELECT name, value
FROM   v$parameter
WHERE  name = 'mle_prog_languages';

PROMPT MLE execution must not be OFF at the effective CDB/PDB/session scope.
PROMPT If the parameter is OFF, an administrator must enable MLE for the target container.
PROMPT Stored MLE modules need CREATE MLE; SQL/PLSQL call specifications need CREATE PROCEDURE.
PROMPT In 26ai, a separate EXECUTE ON JAVASCRIPT grant is not required for MLE in the current schema.

PROMPT
PROMPT -- Required database packages / objects
SELECT owner, object_name, object_type, status
FROM   all_objects
WHERE  owner = 'SYS'
AND    object_name IN ('DBMS_DEVELOPER','DBMS_MLE','DBMS_TRANSACTION','DBMS_VECTOR')
ORDER BY object_name, object_type;

PROMPT
PROMPT -- Schema storage used by the notebooks
SELECT ROUND(NVL(SUM(bytes),0) / 1024 / 1024, 1) AS schema_segment_mb
FROM   user_segments;

PROMPT For Always Free Autonomous AI Database, the service limit is 20 GB of storage.
PROMPT Keep demo tables, vector indexes, imported models, and prior runs small.
PROMPT If storage becomes constrained, run the separate cleanup scripts and remove
PROMPT any imported model that is no longer required.

PROMPT
PROMPT -- Optional ONNX environment
PROMPT Directory expected: &ONNX_DIR_NAME
SELECT directory_name, directory_path
FROM   user_directories
WHERE  directory_name = UPPER('&ONNX_DIR_NAME');

PROMPT
PROMPT The following block is executed only when LOAD_ONNX_MODEL = Y.
PROMPT For Autonomous AI Database, set ONNX_MODEL_URI to a reachable Object Storage
PROMPT object URI (a pre-authenticated URL can be used with credential_name => NULL),
PROMPT then the script downloads the file to ONNX_DIR and imports it.

BEGIN
  IF UPPER('&LOAD_ONNX_MODEL') = 'Y' THEN
    IF TRIM('&ONNX_MODEL_URI') IS NOT NULL THEN
      DBMS_CLOUD.GET_OBJECT(
        credential_name => NULL,
        object_uri     => '&ONNX_MODEL_URI',
        directory_name => '&ONNX_DIR_NAME',
        file_name      => '&ONNX_MODEL_FILE'
      );
    END IF;

    DBMS_VECTOR.DROP_ONNX_MODEL(
      model_name => '&ONNX_MODEL_NAME',
      force      => TRUE
    );

    DBMS_VECTOR.LOAD_ONNX_MODEL(
      directory  => '&ONNX_DIR_NAME',
      file_name  => '&ONNX_MODEL_FILE',
      model_name => '&ONNX_MODEL_NAME',
      metadata   => JSON('{"function":"embedding","embeddingOutput":"embedding","input":{"input":["DATA"]}}')
    );

    DBMS_OUTPUT.PUT_LINE('ONNX model loaded: &ONNX_MODEL_NAME');
  END IF;
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('ONNX setup failed: ' || SQLERRM);
    RAISE;
END;
/

PROMPT
PROMPT -- Verify imported ONNX model when present
SELECT model_name, mining_function, algorithm, algorithm_type, model_size
FROM   user_mining_models
WHERE  model_name = UPPER('&ONNX_MODEL_NAME');

SELECT model_name, attribute_name, attribute_type, data_type, vector_info
FROM   user_mining_model_attributes
WHERE  model_name = UPPER('&ONNX_MODEL_NAME')
ORDER BY attribute_name;

PROMPT
PROMPT ============================================================
PROMPT Schema setup / preflight complete
PROMPT ============================================================
PROMPT
PROMPT Core notebooks are now ready when the role and privilege checks above pass.
PROMPT
PROMPT Optional embedding path:
PROMPT   DEFINE LOAD_ONNX_MODEL = 'Y'
PROMPT   Enter the Object Storage/PAR URI when prompted.
PROMPT   Accept the default model file name or enter the downloaded ONNX file name.
PROMPT   DEFINE ONNX_MODEL_NAME = 'DEMO_MINILM'
PROMPT then rerun this script before opening the optional embedding notebook.
