/*
Select AI - Exploring Agent Tools
*/


/*
Pre-Requisites - Configuring Select AI
*/


/*
Note: Please refer to "00 - Setup Select AI - Anon" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.
*/


/*
PL/SQL Function Tool
*/


/*
This example creates a PL/SQL Function tool that is able to call a PL/SQL Function that you have defined. The PL/SQL Function is able to take input, execute the code block and then returning the output back to the agentic workflow.
*/


/*
Define PL/SQL Function
*/


-- Drop Function for fecthing logs
DROP FUNCTION IF EXISTS fetch_logs;


-- Create a customized fetch_logs procedure
CREATE OR REPLACE FUNCTION fetch_logs(since_date IN DATE) RETURN CLOB AS
  
  -- Declare variable
  l_logs CLOB;

  BEGIN
    SELECT JSON_ARRAYAGG(log_message RETURNING CLOB)
      INTO l_logs
    FROM demo_agents_app_logs
    WHERE log_timestamp >= since_date
    ORDER BY log_timestamp;

    RETURN l_logs;

  EXCEPTION
    WHEN OTHERS THEN
      RETURN 'Error fetching logs: ' || SQLERRM;

END fetch_logs;
/


/*
Define PL/SQL Function Tool
*/


-- Drop Log Fetcher Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('LOG_FETCHER_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


--Create Log Fetcher Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name => 'LOG_FETCHER_TOOL',
    attributes => '{"instruction": "retrieves and returns all log messages with a LOG_TIMESTAMP greater than or equal to the input date.",
                    "function": "fetch_logs"}'
    );
END;
/


/*
SQL Tool
*/


/*
This example creates a SQL tool that translates natural language queries into SQL statements. SQL tool helps the agents answer data-related questions by mapping prompts into SQL queries.

This example shows using OCI as the AI provider as specified in the AI profile named nl2sql_profile. The AI profile identifies the LLM the agent uses for reasoning and responses. In this example, the AI profile nl2sql_profile defines the set of SH schema tables that the agent can query, enabling natural language access to commonly used sales history data such as customers, products, promotions, and countries. The SQL tool uses the database objects that are specified in the AI profile, ensuring that generated SQL statements remain accurate and relevant to the SH data set.
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
     DBMS_CLOUD_AI.DROP_PROFILE(profile_name => '<enter-ai-profile-name>');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/


-- Create AI Profile
BEGIN
    DBMS_CLOUD_AI.create_profile 
        (                                              
                profile_name => '<enter-ai-profile-name>'
            ,   attributes   => '{
                                        "provider"          : "oci"
                                    ,   "credential_name"   : "<enter-ai-api-credential-name>"
                                    ,   "object_list"       : [
                                                                        {"owner": "SH", "name": "CUSTOMERS"}
                                                                    ,   {"owner": "SH", "name": "COUNTRIES"}
                                                                    ,   {"owner": "SH", "name": "SUPPLEMENTARY_DEMOGRAPHICS"}
                                                                    ,   {"owner": "SH", "name": "PROFITS"}
                                                                    ,   {"owner": "SH", "name": "PROMOTIONS"}
                                                                    ,   {"owner": "SH", "name": "PRODUCTS"}
                                                              ]
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "model"             : "<enter-model-name-id>"                                  
                                    ,   "oci_compartment_id": "<enter-compartment-ocid>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                }'
        );
END;
/


/*
Define SQL Tool
*/


-- Drop SQL Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('SQL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


-- Create SQL Tool
BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name  => 'SQL',
    attributes => '{"tool_type": "SQL",
                    "tool_params": {"profile_name": "<enter-ai-profile-name>"}}'
  );
END;
/


/*
RAG Tool
*/


/*
This example creates a RAG (Retrieval Augmented Generation) tool. The RAG tool lets agents retrieve and ground responses in enterprise documents, improving accuracy for knowledge-based answers.

This example illustrates defining a RAG_PROFILE with credentials, a vector index, and specifying profile parameters. Then, creating a vector index RAG_INDEX in Object Storage for document embeddings and creating the RAG_TOOL linked to your profile.
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
    DBMS_CLOUD_AI.DROP_PROFILE(profile_name => '<enter-ai-profile-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/


-- Create AI Profile
BEGIN
    DBMS_CLOUD_AI.CREATE_PROFILE 
        (                                              
                profile_name => '<enter-ai-profile-name>'
            ,   attributes   => '{
                                        "provider"          : "oci"
                                    ,   "credential_name"   : "<enter-oci-api-credential-name>"
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "model"             : "<enter-model-name-id>"
                                    ,   "temperature"       : 0.2
                                    ,   "max_tokens"        : 1000
                                    ,   "embedding_model"   : "<enter-embedding-model-name-id>"
                                    ,   "vector_index_name" : "<enter-vector-index-name>"                                  
                                    ,   "oci_compartment_id": "<enter-compartment-ocid>"
                                    ,   "enable_sources"    : true 
                                }'
        );
END;
/


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
Define Vector Index
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
    attributes  => '{
                        "vector_db_provider": "oracle",
                        "location": "<enter-object-storage-file-uri>",
                        "object_storage_credential_name": "<enter-oci-auth-token-credential-name>",
                        "profile_name": "<enter-ai-profile-name>",
                        "vector_dimension": 1024,
                        "vector_distance_metric": "cosine",
                        "chunk_overlap":20,
                        "chunk_size":250,
                        "match_limit":3
                    }'
    );
END;
/


/*
Define RAG Tool
*/


-- Drop RAG Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('RAG_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name  => 'RAG_TOOL',
    attributes => '{"tool_type": "RAG",
                    "tool_params": {"profile_name": "<enter-ai-profile-name>"}}'
  );
END;
/


/*
Web Search Tool
*/


/*
This example creates a Websearch tool for retrieving details from the internet. The Websearch tool enables agents to look up information from the web, such as product prices or descriptions.

This example illustrates adding an ACL entry for the OpenAI provider. Creating credentials OPENAI_CRED with your API key and creating the Websearch tool, describing its purpose, linking it to the credential.

Note - OpenAI is the only Websearch AI provider supported.
*/


/*
Add ACL for OpenAI Provider
*/


-- Add ACL for OpenAI host
BEGIN
  DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
    host => 'api.openai.com',
    ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                        principal_name => '<enter-schema-name>',
                        principal_type => xs_acl.ptype_db)
   );
END;
/


/*
Define OpenAI Credentials
*/


BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-openai-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Define OpenAI Credential
BEGIN
DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '<enter-openai-credential-name>',
    username        => 'OPENAI',
    password        => '<enter-openai-api-key>'
  );
END;
/


/*
Define Web Search Tool
*/


-- Drop Web Search Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('WEBSEARCH_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


-- Define Web Search Tool
BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name  => 'WEBSEARCH_TOOL',
    attributes => '{"instruction": "This tool can be used for searching the details about topics mentioned in notes and prepare a summary about prices, details on web",
                      "tool_type": "WEBSEARCH",
                      "tool_params": {"credential_name": "<enter-openai-credential-name>"}}'
  );
END;
/


/*
Notification Tool with Email Type
*/

/*
This example creates an Email notification tool. The Email tool enables agents to send notification emails as part of their workflow.

This example illustrates creating credentials EMAIL_CRED with your password, allowing SMTP access for the database user, and creating a notification tool with type EMAIL, including SMTP details, sender, and recipient addresses.
*/

/*
Define SMTP Email Credential
*/


--  Drop SMTP Email Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-smtp-credential-name>');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Create SMTP Email Credential
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '<enter-smtp-credential-name>',
    username => '<enter-smtp-username>',
    password => '<enter-smtp-password>');
END;
/
 

/*
Define ACL for Built-in SMTP Server
*/


-- Define ACL for SMTP Server
BEGIN
   DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
     host => '<enter-smtp-region-host-name>',
     lower_port => 587,
     upper_port => 587,
     ace => xs$ace_type(privilege_list => xs$name_list('SMTP'),
                        principal_name => '<enter-schema-name>',
                        principal_type => xs_acl.ptype_db));
END;
/


/*
Define Email Notification Tool
*/


-- Drop Email Notification Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('EMAIL_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


-- Create Email Notification Tool
BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
    tool_name  => 'EMAIL_TOOL',
    attributes => '{"instruction": "This tool allows you to send an email to the DB Operations Team.",
                    "tool_type": "NOTIFICATION",
                    "tool_params": {"notification_type" : "EMAIL",
                                    "credential_name": "<enter-smtp-credential-name>",
                                    "recipient": "<enter-recipient-email-address>",
                                    "smtp_host": "<enter-smtp-region-host-name>",
                                    "sender": "<enter-approved-sender-email-address>"}}'
  );
END;
/
 

/*
Notification Tool with Slack Type
*/


/*
This example creates a Slack notification tool. The Slack tool enables agents to deliver notifications directly to a Slack workspace channel.

This example illustrates adding an ACL entry for Slack and creating a notification tool with type SLACK linking it to SLACK_CRED and the target channel.
*/


/*
Define Slack Credential
*/


-- Drop Slack Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-slack-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Define Slack Credential
BEGIN
DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '<enter-slack-credential-name>',
    username        => '<enter-slack-username>',
    password        => '<enter-slack-password>'
  );
END;
/


/*
Add ACL for Slack Notifications
*/


-- Add ACL for Slack Notifications
BEGIN
    DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE (
    host         => 'slack.com',
    lower_port   => 443,
    upper_port   => 443,
    ace          => xs$ace_type(
        privilege_list => xs$name_list('http'),
        principal_name => '<enter-schema-name>',
        principal_type => xs_acl.ptype_db));
    END;
/


/*
Define Slack Notification Tool
*/


-- Drop Slack Notification Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('SLACK_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


-- Create Slack Notification Tool
BEGIN
  DBMS_CLOUD_AI_AGENT.create_tool(
    tool_name  => 'slack',
    attributes => '{"tool_type": "SLACK",
                    "tool_params": {"credential_name": "<enter-slack-credential-name>",
                                    "channel": "<channel_number>"}}'
  );
END;
/


/*
End of Notebook
*/

