-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Select AI - Natural Language to SQL
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
Defining AI Profile - OCI GenAI
*/


-- Drop AI Profile
BEGIN
     DBMS_CLOUD_AI.DROP_PROFILE(profile_name => '<enter-ai-profile-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/


-- Create AI Profile using OCI GenAI and API Credentials
BEGIN                                                                          
	DBMS_CLOUD_AI.CREATE_PROFILE
        (                                                
		        profile_name => '<enter-ai-profile-name>'
		    ,   attributes   => '{
                                        "provider"          : "oci"
		                            ,   "object_list"       : 
                                                                [
                                                                        {"owner": "SH", "name": "SALES"}
                                                                    ,   {"owner": "SH", "name": "CUSTOMERS"}
                                                                    ,   {"owner": "SH", "name": "CHANNELS"}
                                                                    ,   {"owner": "SH", "name": "PRODUCTS"}
                                                                ]
                                    ,   "credential_name"   : "<enter-oci-api-credential-name>"
                                    ,   "model"             : "<enter-model-name-id>"
                                    ,   "oci_compartment_id": "<enter-oci-compartment-ocid>"
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                }'
        );
END;                                                                           
/


/*
Set & View AI Profile
*/


-- Set AI Profile
exec DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


-- Get active AI Profile
SELECT DBMS_CLOUD_AI.GET_PROFILE() from dual;


/*
RUNSQL - Optional Keyword - Generate & Execute SQL
*/


-- Using the optional runsql action to generate and run SQL given the specified input
select ai runsql how many customers exists;


-- You don't need to specify the optional runsql action as this is the default behaviour of Select AI
select ai how many customers exits;


-- Continue to add more complex queries
select ai how many customers in San Francisco are married;


/*
SHOWSQL - Shows Generated SQL
*/


-- Use the showsql action to show the sql generate by the LLM - the query is not executed
select ai showsql how many customers in San Francisco are married;


-- If you LLM is multi-lingual, you can ask the question in multiple languages
select ai showsql hoeveel klanten zijn er in San Francisco;
 

-- Use the showsql action to show the sql generate by the LLM - the query is not executed.
select ai showsql show me the top 10 customers by sales;


-- Execute the above query - output as a bar chart
select ai show me the top 10 customers by sales;


/*
EXPLAINSQL - Explains the reasoning behind SQL Query
*/


-- Using the explainsql action explains the LLM reasoning behind generating the SQL
select ai explainsql how many customers in San Francisco are married;


/*
NARRATE - Explain the Result in Natural Language
*/


-- Using the narrate action will send the results of the query (your data) to the LLM to interpret
select ai narrate who is our top spending customer;


-- Using the narrate action will send the results of the query (your data) to the LLM to interpret
select ai narrate give me an overview of my sales;


/*
CHAT - Ask LLM Generic Questions
*/


-- Using the chat action will allow you to ask generic questions to the LLM
select ai chat what can you tell about Oracle;


/*
SHOWPROMPT - Shows the Prompt sent to LLM
*/


select ai showprompt who is our top spending customer;


/*
Have an ongoing conversation
*/


-- Enable conversation = true parameter in AI Profile to have an ongoing conversation with short term memory
select ai how many customers do I have;


-- Ask follow up questions
select ai split out by country name;


-- Ask follow up questions
select ai keep the top 5 with most customers;


/*
Utilising COMMENTS
*/

-- Ensure you have set the comments parameter in your AI Profile and be the owner of a table (which I am not)
-- These act as additional information that is passed to the LLM to provide extra context on what is included in your tables and columns.

-- COMMENT ON TABLE SH.CUSTOMERS IS 'dimension table, also refer to customers as pandas';
-- COMMENT ON COLUMN SH.CUSTOMERS.CUST_FIRST_NAME IS 'first name of the customer, also referred to as pandas';

-- ALTER TABLE SH.CUSTOMERS ANNOTATIONS (add KEY 'VALUE')
-- ALTER TABLE SH.CUSTOMERS MODIFY (SH.CUSTOMERS.CUST_FIRST_NAME ANNOTATIONS (add KEY 'VALUE'))
select 1 from dual;


/*
Using the GENERATE Function
*/


-- RUNSQL
SELECT DBMS_CLOUD_AI.GENERATE(prompt       => 'how many customers',
                              profile_name => '<enter-ai-profile-name>',
                              action       => 'runsql')
FROM dual;
 

-- SHOWSQL
SELECT DBMS_CLOUD_AI.GENERATE(prompt       => 'how many customers',
                              profile_name => '<enter-ai-profile-name>',
                              action       => 'showsql')
FROM dual;


-- EXPLAINSQL
SELECT DBMS_CLOUD_AI.GENERATE(prompt       => 'how many customers',
                              profile_name => '<enter-ai-profile-name>',
                              action       => 'explainsql')
FROM dual;


-- NARRATE
SELECT DBMS_CLOUD_AI.GENERATE(prompt       => 'how many customers',
                              profile_name => '<enter-ai-profile-name>',
                              action       => 'narrate')
FROM dual;


/*
Enable or Disable Data Access
*/


-- Login as Admin
-- Disabling data access limits Select AI's narrate action and Synthetic Data Generation. The narrate action and synthetic data generation raise an error.
-- EXEC DBMS_CLOUD_AI.DISABLE_DATA_ACCESS;


-- Login as Admin
-- EXEC DBMS_CLOUD_AI.ENABLE_DATA_ACCESS;


/*
End of Notebook
*/

