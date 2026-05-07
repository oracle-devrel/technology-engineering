-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Select AI - Generating Synthetic Data
*/


/*
Pre-Requisites - Configuring Select AI
*/


/*
Note: Please refer to "00 - Setup Select AI - Anon" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.
*/


/*
Drop Demo Tables
*/


-- Drop Tables
DROP TABLE IF EXISTS select_ai_director CASCADE CONSTRAINTS PURGE;
DROP TABLE IF EXISTS select_ai_movie CASCADE CONSTRAINTS PURGE;
DROP TABLE IF EXISTS select_ai_actor CASCADE CONSTRAINTS PURGE;
DROP TABLE IF EXISTS select_ai_movie_actor CASCADE CONSTRAINTS PURGE;


/*
Create Demo Tables
*/


-- Create Demo Tables
CREATE TABLE select_ai_director (
    director_id     INT PRIMARY KEY,
    name            VARCHAR(100)
);

CREATE TABLE select_ai_movie (
    movie_id        INT PRIMARY KEY,
    title           VARCHAR(100),
    release_date    DATE,
    genre           VARCHAR(50),
    director_id     INT,
    FOREIGN KEY (director_id) REFERENCES select_ai_director(director_id)
);

CREATE TABLE select_ai_actor (
    actor_id        INT PRIMARY KEY,
    name            VARCHAR(100)
);

CREATE TABLE select_ai_movie_actor (
    movie_id        INT,
    actor_id        INT,
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES select_ai_movie(movie_id),
    FOREIGN KEY (actor_id) REFERENCES select_ai_actor(actor_id)
);


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
  DBMS_CLOUD_AI.DROP_PROFILE('<enter-ai-profile-name>');
EXCEPTION
  WHEN OTHERS THEN
      DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/


/*
Defining AI Profile - OCI GenAI
*/


-- Create AI Profile
BEGIN
    DBMS_CLOUD_AI.CREATE_PROFILE(  
        profile_name =>   '<enter-ai-profile-name>',  
        attributes   =>   '{
                                "provider"          : "oci"
                            ,   "credential_name"   : "<enter-oci-api-credential-name>"
                            ,   "model"             : "<model-name-id>"
                            ,   "object_list"       :   [    
                                                            {"owner": "<enter-schema-name>", "name": "SELECT_AI_DIRECTOR"}
                                                        ,   {"owner": "<enter-schema-name>", "name": "SELECT_AI_MOVIE"}
                                                        ,   {"owner": "<enter-schema-name>", "name": "SELECT_AI_ACTOR"}
                                                        ,   {"owner": "<enter-schema-name>", "name": "SELECT_AI_MOVIE_ACTOR"}
                                                        ]
                            ,   "oci_compartment_id": "<enter-compartment-ocid>"
                            ,   "region"            : "<enter-region-identifier>"
                            ,   "comments"          : "true"
                            ,   "conversation"      : "true"
                        }');  
END;
/


/*
Set AI Profile
*/


-- Set AI Profile
EXEC DBMS_CLOUD_AI.SET_PROFILE(profile_name => '<enter-ai-profile-name>');


/*
Create Synthetic Data for a Single Table
*/


-- Create Syntehtic Data for a single table
BEGIN
    DBMS_CLOUD_AI.GENERATE_SYNTHETIC_DATA(
        profile_name => '<enter-ai-profile-name>',
        object_name  => 'SELECT_AI_DIRECTOR',
        owner_name   => '<enter-schema-name>',
        record_count => 5,
        user_prompt  => 'all directors must have received oscar nominations',
        params       => '{"sample_rows":5, "priority":"HIGH", "comments":"True", "table_statistics":true}');
END;
/

-- user_prompt argument enables you to specify additional rules or requirements for data generation
-- by adding {"sample_rows": 5} to the params argument, you can send 5 sample rows from a table to the AI provider
-- priority parameter assign a priority value that defines the number of parallel requests sent to the LLM for generating synthetic data. Tasks with a higher priority will consume more database resources and complete faster.
-- table_statistics parameter - If a table has column statistics or is cloned from a database that includes metadata, Select AI can use these statistics to generate data that closely resembles or is consistent with the original data.
-- comments parameter - If column comments exist, Select AI automatically includes them to provide additional information for the LLM during data generation.


-- Preview Data
select * from select_ai_director;
 

/*
Generate Synthetic Data for Multiple Tables
*/


-- Create Synthetic Data for multiple tables
BEGIN
  DBMS_CLOUD_AI.GENERATE_SYNTHETIC_DATA(
    profile_name => '<enter-ai-profile-name>',
    object_list  => '[{"owner": "<enter-schema-name>", "name": "select_ai_director", "record_count":5},
                     {"owner": "<enter-schema-name>", "name": "select_ai_movie_actor", "record_count":5},
                     {"owner": "<enter-schema-name>", "name": "select_ai_actor", "record_count":10},
                     {"owner": "<enter-schema-name>", "name": "select_ai_movie", "record_count":5, "user_prompt":"all movies released in 2009"}]',
    params       => '{"sample_rows":5, "priority":"HIGH", "comments":true, "table_statistics":true}');
END;
/


-- Preview Data
select * from select_ai_movie;


-- Use NL2SQL
select ai how many actors are there; 

/*
Interrupting Synthetic Data Generation Task
*/


-- Find the operation ID of the running Synthetic Data Generation (SDG) process
SELECT * FROM user_load_operations WHERE type = 'SYNTHETIC_DATA';


-- Delete a specific SDG operation
EXEC DBMS_CLOUD.DELETE_OPERATION('<enter-id>');

-- Delete all SDG operations
-- EXEC DBMS_CLOUD.DELETE_ALL_OPERATIONS('SYNTHETIC_DATA');


/*
End of Notebook
*/
