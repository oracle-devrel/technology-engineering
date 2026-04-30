/*
Select AI - RAG
*/


/*
Pre-Requisites - Configuring Select AI
*/


/*
Note: Please refer to "00 - Setup Select AI - Anon" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.
*/


/*
Define OCI API Credential
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-oci-api-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Create Credentials for OCI API Key
BEGIN                                                                          
	DBMS_CLOUD.CREATE_CREDENTIAL
        (  
		    	credential_name => '<enter-oci-api-credential-name>',
			 	user_ocid 		=> '<enter-user-ocid>',
		        tenancy_ocid    => '<enter-tenancy-ocid>',
		        private_key     => '<enter-private-key-value>',
		        fingerprint     => '<enter-private-key-fingerprint>'       
        );                                                                           
END;                                                                           
/


/*
Define AI Profile
*/


-- Drop AI Profile
BEGIN  
  DBMS_CLOUD_AI.DROP_PROFILE('<enter-ai-profile-name>');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/  


-- Create AI Profile
BEGIN
    DBMS_CLOUD_AI.CREATE_PROFILE(                                              
        profile_name => '<enter-ai-profile-name>',
        attributes   => '{
                                "provider"          : "oci"
                            ,   "credential_name"   : "<enter-oci-api-credential-name>"
                            ,   "region"            : "<enter-region-identifier>"
                            ,   "model"             : "<enter-model-name-id>"
                            ,   "temperature"       : 0.2
                            ,   "max_tokens"        : 1000
                            ,   "embedding_model"   : "<enter-embedding-model-name-id>"
                            ,   "vector_index_name" : "<enter-vector-index-name>"                                  
                            ,   "oci_compartment_id": "<enter-compartment-ocid>"
                            ,   "enable_sources"    : "true"
                            ,   "conversation"      : "true"
                        }'
    );
END;
/


-- You also have the option to use an in-database ONNX Embedding model
-- Review pre-requisites on how to load an ONNX embedding model - https://docs.oracle.com/pls/topic/lookup?ctx=en/cloud/paas/autonomous-database/serverless/adbsb&id=VECSE-GUID-D8140BF9-08E9-4B3F-9E28-E40A6FD181A4

-- Create Embedding Profile
/*
BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
     profile_name => 'EMBEDDING_PROFILE',
     attributes   => '{"provider" : "database",
                       "embedding_model": "<enter-model-name>"}'
  );
END;
/

BEGIN
  DBMS_CLOUD_AI.CREATE_PROFILE(
     profile_name => '<enter-profile-name>',
     attributes   => '{"provider": "oci",
                       "model": "<model-name-id>",
                       "credential_name": "<enter-api-credential-name>",
                       "vector_index_name": "<enter-vector-index-name>",
                       "embedding_model": "database: <enter-onnx-model-name>"}'
  );
END;
/
*/


/*
Set AI Profile
*/


-- Set AI Profile
EXEC DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


/*
Define OCI Auth Token Credential
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-oci-auth-token-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/



-- Create Credential for OCI Authentication Token
BEGIN                                                                          
	DBMS_CLOUD.CREATE_CREDENTIAL
        (  
		        credential_name => '<enter-oci-auth-token-credential-name>'
		    ,   username        => '<domain-name>/<enter-oci-user>'
		    ,   password        => '<enter-oci-auth-token>'
        );                                                                           
END;                                                                           
/
 

/*
Setup Vector Index
*/


-- Drop Vector Index
BEGIN
  DBMS_CLOUD_AI.DROP_VECTOR_INDEX('<enter-vector-index-name>');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Vector Index does not exist.');
END;
/


-- Create Vector Index
BEGIN
  DBMS_CLOUD_AI.CREATE_VECTOR_INDEX(
    index_name  => '<enter-vector-index-name>',
    attributes  => '{"vector_db_provider": "oracle",
                     "location": "<enter-object-storage-url>",
                     "object_storage_credential_name": "<enter-oci-auth-token-credential-name>",
                     "profile_name": "<enter-ai-profile-name>",
                     "vector_dimension": 1024,
                     "vector_distance_metric": "cosine",
                     "chunk_overlap":20,
                     "chunk_size":250,
                     "vector_table_name": "<enter-vector-table-name>",
                     "match_limit":3}');
END;
/


/*
View Vector Index Pipeline Information
*/


-- Preview Vector Pipeline Information
SELECT
    PIPELINE_ID,
    PIPELINE_NAME,
    STATUS,
    LAST_EXECUTION,
    STATUS_TABLE
FROM
    USER_CLOUD_PIPELINES;


-- Preview Specific Pipeline
SELECT 
   *
FROM
   "<enter-status-table-from-above-query>";


-- View Pipeline Attributes
SELECT 
   *
FROM
   USER_CLOUD_PIPELINE_ATTRIBUTES;


-- View Pipeline Run History
SELECT 
    *
FROM
    USER_CLOUD_PIPELINE_HISTORY;


-- Count Records
SELECT 
    COUNT(*)
FROM
    "<enter-vector-table-name>";


-- Preview Data
SELECT
    CONTENT,
    ATTRIBUTES,
    EMBEDDING
FROM
    "<enter-vector-table-name>"
WHERE
    ROWNUM <= 5;


/*
Query Data
*/


-- Query RAG Pipeline
select ai narrate Why Use Oracle AI Vector Search;


-- Execute NARRATE
SELECT DBMS_CLOUD_AI.GENERATE (
    PROFILE_NAME => '<enter-ai-profile-name>',
    ACTION => 'NARRATE',
    PROMPT => 'Why Use Oracle AI Vector Search'
) AS QUESTION;
 


-- Execute RUNSQL
SELECT JSON_SERIALIZE(
    DBMS_CLOUD_AI.GENERATE (
    PROFILE_NAME => '<enter-ai-profile-name>',
    ACTION => 'RUNSQL',
    PROMPT => 'Why Use Oracle AI Vector Search'
    ) PRETTY
) AS QUESTION;
 


-- Execute SHOWSQL
SELECT DBMS_CLOUD_AI.GENERATE (
    PROFILE_NAME => '<enter-ai-profile-name>',
    ACTION => 'SHOWSQL',
    PROMPT => 'Why Use Oracle AI Vector Search'
) AS QUESTION;


/*
End of Notebook
*/
