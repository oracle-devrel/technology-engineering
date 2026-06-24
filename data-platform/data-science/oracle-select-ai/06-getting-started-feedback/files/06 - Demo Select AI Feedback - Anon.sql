-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Select AI - Feedback
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
EXEC DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


-- Get active AI Profile
SELECT DBMS_CLOUD_AI.get_profile() FROM DUAL;


/*
Provide Negative Feedback
*/


-- View a sample sql query 
-- Let's assume it did not generate the correct SQL and infact generated SELECT SUM(1) FROM "SH"."CUSTOMERS"
select ai showsql how many customers;


-- Provide negative feedback to the AI Profile, an example of what the query should NOT look like based on an natural language query
BEGIN
    DBMS_CLOUD_AI.FEEDBACK(
        profile_name    => '<enter-ai-profile-name>', 
        sql_text        => 'select ai showsql how many customers', 
        feedback_type   => 'negative', 
        response        => 'SELECT SUM(1) FROM "SH"."CUSTOMERS"'
        );
END;
/


-- View the negative feedback entry
SELECT 
    CONTENT, 
    ATTRIBUTES 
FROM 
    IS_PROFILE_OCI_GENAI_FEEDBACK_VECINDEX$VECTAB
WHERE
    JSON_VALUE(attributes, '$.sql_text') = 'select ai showsql how many customers';


/*
Provide Positive Feedback
*/


-- View a sample query
select ai showsql how many distinct customer cities;


-- Retrieve the sql_id from the v$mapped_sql view for the given prompt.
-- V$MAPPED_SQL lists the SQL statements that are translated and mapped in memory to a different SQL statement for execution.
SELECT 
    SQL_ID 
FROM 
    V$MAPPED_SQL 
WHERE 
    SQL_TEXT = 'select ai showsql how many distinct customer cities';


-- Provide positive feedback to the AI Profile, an example of what the query should look like based on an natural language query
-- This time you can add an entry based on the SQL ID rather than the SQL Text as we did with the negative feedback
BEGIN
    DBMS_CLOUD_AI.FEEDBACK(
        profile_name    => '<enter--aiprofile-name>',
        sql_id          => '<enter-sql-id-returned-above>',
        feedback_type   => 'positive', 
        operation       => 'add'
        );
END;
/


-- View the positive feedback entry
SELECT 
    CONTENT,
    ATTRIBUTES 
FROM 
    IS_PROFILE_OCI_GENAI_FEEDBACK_VECINDEX$VECTAB 
WHERE 
    JSON_VALUE(attributes, '$.sql_id') ='<enter-sql-id-returned-above>';


/*
Provide Feedback without Prior Usage
*/


-- You may provide feedback for SQL prompts even if the prompt has not been used previously.
BEGIN
  DBMS_CLOUD_AI.FEEDBACK(
    profile_name        =>'<enter--aiprofile-name>',
    sql_text            =>'select ai runsql how many customers named LOR', -- Prior usage not required
    feedback_type       =>'negative',
    response            =>'SELECT COUNT(*) AS "Num" FROM "SH"."CUSTOMERS" WHERE UPPER("CUST_FIRST_NAME") LIKE ''%LOR%''',
    feedback_content    =>'Use LIKE instead of ='
  );
END;
/


-- Run query
select ai runsql how many customers named LOR;


/*
Delete Feedback
*/


-- We can delete feedback similar to adding feedback. Use the delete operation and specify the sql_id or sql_text
BEGIN
    DBMS_CLOUD_AI.FEEDBACK(
        profile_name    =>'<enter-ai-profile-name>',
        sql_id          => '<enter-sql-id>',
        operation       =>'delete'
    );
END;
/


/*
Provide Negative Feedback on Last Query using the Feedback Action
*/


-- Execute example query
select ai showsql sort customer credit limit;


-- Immediately provide the feedback
select ai feedback use DESC sorting;


-- Execute same query - check if feedback is implemented
select ai showsql sort customer credit limit;


/*
Provide Positive Feedback on Last Query using the Feedback Action
*/


-- Example query
select ai showsql how many customers are in each marital status;


-- Provide positive feedback
select ai feedback this is correct;


/*
Use Feedback Action for Feedback using SQL_ID
*/


-- Execute example query
select ai showsql sort customer credit limit;


-- Get the SQL ID
SELECT
    SQL_ID
FROM 
    V$MAPPED_SQL 
WHERE
    SQL_TEXT = 'select ai showsql sort customer credit limit';


-- Provide feedback via Feedback Action
select ai feedback for query with sql_id = '<enter-sql-id-returned-above>', rank in descending sorting;


/*
Use Feedback Action for Feedback using Query Text 
*/


-- Sample query
select ai showsql what is the total customer credit limit;


-- Provide feedback via feedback action based on query text
select ai feedback for query "select ai showsql what is the total customer credit limit", name the column as total_limit;


/*
End of Notebook
*/

