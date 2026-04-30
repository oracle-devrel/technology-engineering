/*
Select AI - Proxy Integration with PostgreSQL
*/


/*
Pre-Requisites - Configuring Select AI
*/


/*
Note: Please refer to "00 - Setup Select AI - Anon" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.
*/


/*
Defining PostgreSQL Credential
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL(credential_name => '<enter-postgresql-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/
 


-- Create a credential that stores the PostgreSQL username and password.
BEGIN
    DBMS_CLOUD.CREATE_CREDENTIAL(
        credential_name => '<enter-postgresql-credential-name>',
        username        => '<enter-postgresql-user>',
        password        => '<enter-postgresql-password>'
    );
END;
/


/*
Create Database Link to PostgreSQL DB
*/


-- Drop Database Link
BEGIN
    DBMS_CLOUD_ADMIN.DROP_DATABASE_LINK(db_link_name => '<enter-postgres-database-link-name>');
EXCEPTION
  WHEN OTHERS THEN
    DBMS_OUTPUT.PUT_LINE('Database Link does not exist.');
END;
/


-- Create a heterogeneous database link to PostgreSQL. This example uses gateway_params to set the database type and SSL.
BEGIN
    DBMS_CLOUD_ADMIN.CREATE_DATABASE_LINK(
        db_link_name        => '<enter-postgresql-database-link-name>',
        hostname            => '<enter-postgresql-primary-endpoint-fqdn>',
        port                => 5432,
        service_name        => 'postgres',
        credential_name     => '<enter-postgresql-credential-name>',
        gateway_params      => JSON_OBJECT('db_type' VALUE 'postgres', 'enable_ssl' VALUE true),
        ssl_server_cert_dn  => NULL,
        private_target      => true
    );
END;
/


/*
Define a Logical View on PostgreSQL Table
*/


-- Drop View of Exists
DROP VIEW IF EXISTS V_POSTGRESQL_LINK_SALES;


-- Create a local view on the PostgreSQL table and map the remote PostgreSQL table into the Autonomous AI Database schema with a view.
CREATE VIEW V_POSTGRESQL_LINK_SALES AS (
    SELECT 
        *
    FROM 
        "sales"@postgresql_link
);


-- Query View
SELECT
    COUNT(*)
FROM
    V_POSTGRESQL_LINK_SALES;


-- Directly Query PostgreSQL Data
SELECT
    COUNT(*)
FROM
    "sales"@postgresql_link;


-- Diretcly Query PostgreSQL Data    
SELECT
    count(distinct "prod_id")
FROM
    "sales"@postgresql_link
WHERE
    "channel_id"=2;


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
		        private_key     => '<enter-private-key>',
		        fingerprint     => '<enter-enter-fingerprint>'       
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


-- Create AI Profile using OCI GenAI and API Credentials
BEGIN                                                                          
	DBMS_CLOUD_AI.CREATE_PROFILE
        (                                                
		        profile_name => '<enter-ai-profile-name>'
		    ,   attributes   => '{
                                        "provider"          : "oci"
		                            ,   "object_list"       : 
                                                                [
                                                                        {"owner": "<enter-schema-name>", "name": "V_POSTGRESQL_LINK_SALES"}
                                                                    ,   {"owner": "SH", "name": "CUSTOMERS"}
                                                                ]
                                    ,   "credential_name"   : "<enter-oci-api-credential-name>"
                                    ,   "model"             : "<enter-model-name-id>"
                                    ,   "oci_compartment_id": "<enter-compartment-id>"
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                    ,   "enforce_object_list": "true"
                                }'
        );
END;                                                                           
/


-- Set AI Profile
EXEC DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


/*
Query Oracle AI Database Table
*/


-- Call Select AI
SELECT AI HOW MANY CUSTOMERS DO WE HAVE; 


-- Call Select AI
SELECT AI SHOWSQL HOW MANY CUSTOMERS DO WE HAVE;


/*
Query PostgreSQL Proxy Tables
*/


-- Call Select AI - Proxy Object
SELECT AI WHAT IS THE TOTAL AMOUNT SOLD;


-- Call Select AI - Proxy Object
SELECT AI SHOWSQL WHAT IS THE TOTAL AMOUNT SOLD;


/*
Query Across Both Data Sources
*/


-- Query across both data sources
SELECT DBMS_CLOUD_AI.GENERATE(prompt       => 'what is the total amount sold for married customers',
                              profile_name => '<enter-ai-profile-name>',
                              action       => 'runsql') RESPONSE
FROM dual;


-- Verify Query Results
SELECT 
    SUM(s."amount_sold") AS "TOTAL_AMOUNT_SOLD"
FROM 
    "V_POSTGRESQL_LINK_SALES" s
    JOIN "SH"."CUSTOMERS" c ON s."cust_id" = c."CUST_ID"
WHERE 
    UPPER(c."CUST_MARITAL_STATUS") = UPPER('married');


/*
End of Notebook
*/

