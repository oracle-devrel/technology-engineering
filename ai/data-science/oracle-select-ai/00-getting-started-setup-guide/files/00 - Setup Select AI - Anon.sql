-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Setup Oracle Select AI within Oracle AI Database 
*/

/*
Pre-Requisites - Please Run any SQL/PLSQL in this Cell as ADMIN User
*/

/*
* If using OCI Generative AI as the LLM Provider - Set up Authentication:
    * Ensure correct networking is configured.
    * Option 1 - Authenticating with API Keys
        * Documentation (https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm#How).
        * Generate a set of API Keys or Upload existing API Keys to the OCI Console under your User Profile.
        * Make note of your user_ocid, tenancy_ocid, private_key, and fingerprint.
        * Create an OCI policy to allow users to access OCI Generative AI Service.
            * allow any-user to manage generative-ai-family in compartment <compartment-name>
        * Create a credential within the database for your OCI API Key.
            *  Example code given below in notebook.
    * Option 2 - Authenticating with Resource Principal
        * Documentation (https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/dbms-cloud-admin.html#GUID-4DC6A536-DC78-43FE-B173-CED1F9FB45A0).
        * Create Dynamic Group within OCI (https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/resource-principal.html#GUID-3CF59CED-F7DF-46AF-B3CF-E703ED0BB3EE).
            * ALL {resource.type='autonomousdatabase', resource.compartment.id='<compartment-ocid>'}
        * Create Policy for Dynamic Group to access OCI Generative AI Service.
            * allow dynamic-group <domain-name>/<dynamic-group-name> to manage generative-ai-family in compartment <compartment-name>
        * Enable resource principal in database.
            *  Example code given below in notebook. 


* If using a 3rd Party LLM Provider - Set up Authentication:
    * Ensure correct networking is configured.
    * Get API Key from relevant provider.
    * Create a credential within the database with your 3rd Party API Key.
        *  Example code given below in notebook.
    * Enable ACL privileges in database to access your external AI provider.
        * Documentation (https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/select-ai-manage-profiles.html#GUID-3721296F-14A1-428A-B464-7FA25E9EC8F3).
        *  Example code given below in notebook.


* If planning on using Select AI RAG: 
    * Generate an Auth Token within OCI Console under your User Profile.
        * Documentation (https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrygettingauthtoken.htm).
    * Make note of Authentication Token and OCI User Name.
    * Create a Policy within OCI to allow a Group that your user is assigned to, to manage Object Storage:
        * allow group <group-name> to manage object-family in compartment <compartment-name>
    * Create an Object Storage Bucket within the above Compartment to upload your documents.
    * Create a credential within the database with your Authentication Token.
        *  Example code given below in notebook.


* If planning on using Select AI Agents - Email Notification Tool: 
    * Identify your SMTP connection endpoint for Email Delivery. You may need to subscribe to additional Oracle Cloud Infrastructure regions if Email Delivery is not available in your current region. For example, select one of the following for the SMTP connection endpoint:
        * smtp.us-phoenix-1.oraclecloud.com
        * smtp.us-ashburn-1.oraclecloud.com
        * smtp.email.uk-london-1.oci.oraclecloud.com
        * smtp.email.eu-frankfurt-1.oci.oraclecloud.com
        * See Configure SMTP Connection for more information. (https://docs.oracle.com/iaas/Content/Email/Tasks/configuresmtpconnection.htm).
    * Generate SMTP credentials for Email Delivery.
        * See Generate SMTP Credentials for a User for more information. (https://docs.oracle.com/iaas/Content/Email/Reference/gettingstarted_topic-create-smtp-credentials.htm#top).
    * Create a credential within the database with your SMTP credentials.
        *  Example code given below in notebook.
    * Create an approved sender for Email Delivery. Complete this step for all email addresses you will use to send email notifications from.
        * See Managing Approved Senders for more information. (https://docs.oracle.com/iaas/Content/Email/Tasks/managingapprovedsenders.htm)
    * Allow SMTP access for ADMIN user by appending an Access Control Entry (ACE).
        *  Example code given below in notebook.
        

* If planning on using Select AI Translate 
    * To use the Select AI translation feature, you must have the appropriate IAM policy permissions to access Oracle Cloud Infrastructure Language services.
    * Grant the permission to use ai-service-language-family resource in your IAM policy. An example policy statement to grant permission to a user group in a specific compartment is:
        * allow group <your group name> to use ai-service-language-family in compartment <your_compartment>
        * If using Resource Principal credential, assign the permission to the Dynamic Group.
        * If using Private Key credential, assign the permission to the User Group.
        
*/


/*
Create User & Grant Permissions
*/

-- Create a new user
CREATE USER "<USER>" IDENTIFIED BY "<PASSWORD>"; 


 -- Grant permissions to user
GRANT CONNECT TO "<USER>";
GRANT CREATE SESSION TO "<USER>";
GRANT DWROLE TO "<USER>";
GRANT OML_DEVELOPER TO "<USER>";
GRANT EXECUTE ON DBMS_CLOUD_AI TO "<USER>";
GRANT EXECUTE ON DBMS_CLOUD_PIPELINE TO "<USER>"; 
GRANT EXECUTE ON DBMS_CLOUD_AI_AGENT TO "<USER>";
GRANT EXECUTE ON DBMS_NETWORK_ACL_ADMIN TO "<USER>";
GRANT EXECUTE ON DBMS_CLOUD_ADMIN TO "<USER>";
GRANT CREATE DATABASE LINK TO "<USER>";
GRANT COMMENT ANY TABLE TO "<USER>";
GRANT READ ON SYS.V_$MAPPED_SQL TO "<USER>";
GRANT READ ON SYS.V_$SESSION TO "<USER>";


-- Assign Tablespace and Quota to user
ALTER USER "<USER>" DEFAULT TABLESPACE DATA;
ALTER USER "<USER>" QUOTA UNLIMITED ON DATA; 


/*
Switch to the created Select AI User to execute the below unless specified in the comments
*/

/*
Ensure user can access default SH Schema
*/


-- Count Records in SALES Table
SELECT COUNT(*) AS NUM_RECORDS FROM SH.SALES;


/*
Query the SH.TIMES table
*/


-- Preview all records in the TIMES table
SELECT * FROM SH.TIMES;


/*
LLM Provider: OCI GenAI 
Option 1 - Set up Credential (API Keys) & AI Profile
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


-- Drop AI Profile
BEGIN
     DBMS_CLOUD_AI.DROP_PROFILE(profile_name => '<enter-ai-profile-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;


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
                                    ,   "credential_name"   : "<enter-tenancy-ocid>"
                                    ,   "model"             : "<enter-model-id>"
                                    ,   "oci_compartment_id": "<enter-compartment-ocid>"
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                }'
        );
END;                                                                           
/


-- Set AI Profile
EXEC DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


-- Call Select AI chat action to test LLM response
 SELECT DBMS_CLOUD_AI.GENERATE(
    prompt       => 'what is oracle autonomous database',
    profile_name => '<enter-ai-profile-name>',
    action       => 'chat') as RESPONSE
FROM dual;


-- Call Select AI showsql action
SELECT AI SHOWSQL HOW MANY CUSTOMERS DO WE HAVE


/*
LLM Provider:  OCI GenAI 
Option 2 - Set up Credential (Resource Principal) & AI Profile
*/


-- Enable OCI Resource Principal
-- This Should be Run as ADMIN User
BEGIN
     DBMS_CLOUD_ADMIN.ENABLE_RESOURCE_PRINCIPAL (
          username => '<schema-name>',
          grant_option => TRUE
     );
END;
/


-- Drop AI Profile
BEGIN
     DBMS_CLOUD_AI.DROP_PROFILE(profile_name => '<enter-ai-profile-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;


-- Create AI Profile using OCI GenAI and Resource Principal
BEGIN
    DBMS_CLOUD_AI.create_profile 
        (                                              
                profile_name => '<enter-ai-profile-name>'
            ,   attributes   => '{
                                        "provider"          : "oci"
                                    ,   "credential_name"   : "OCI$RESOURCE_PRINCIPAL"
                                    ,   "object_list"       : [
                                                                        {"owner": "SH", "name": "SALES"}
                                                                    ,   {"owner": "SH", "name": "CUSTOMERS"}
                                                                    ,   {"owner": "SH", "name": "CHANNELS"}
                                                                    ,   {"owner": "SH", "name": "PRODUCTS"}
                                                              ]
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "model"             : "<enter-model-id>"                                  
                                    ,   "oci_compartment_id": "<enter-compartment-ocid>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                }'
        );
END;
/


-- Set AI Profile
EXEC DBMS_CLOUD_AI.SET_PROFILE('<enter-ai-profile-name>');


-- Call Select AI chat action to test LLM response
 SELECT DBMS_CLOUD_AI.GENERATE(
    prompt       => 'what is oracle autonomous database',
    profile_name => '<enter-ai-profile-name>',
    action       => 'chat') as RESPONSE
FROM dual;


-- Call Select AI showsql action
SELECT AI SHOWSQL HOW MANY CUSTOMERS DO WE HAVE


/*
LLM Provider: 3rd Party - OpenAI
Set up Credential (API Key) & AI Profile
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-third-party-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Create Credential for 3rd Party API Key
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '<enter-third-party-credential-name>',
    username        => '<third-party-provider-name>',
    password        => '<third-party-provider-api-key>'
  );
END;
/


-- Enable ACL to communicate with external 3rd Party Host
BEGIN
  DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
    host => '<third-party-host>',
    ace  => xs$ace_type(privilege_list => xs$name_list('http'),
                        principal_name => '<schema-name>',
                        principal_type => xs_acl.ptype_db)
   );
END;
/


/*
Select AI RAG Workflows
Set up Auth Token Credential to Access Object Storage
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
Select AI Agents - Email Notification Tool
Set up SMTP Credentials & ACL
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-smtp-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Create Credential for SMTP Credentials
BEGIN
  DBMS_CLOUD.CREATE_CREDENTIAL(
    credential_name => '<enter-smtp-credential-name>',
    username => '<enter-smtp-credential-username>',
    password => '<enter-smtp-credential-password>');
END;
/
 


-- Enable ACL to communicate with SMTP Server
BEGIN
   DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE(
     host => '<smtp-server-region-identifier>',
     lower_port => 587,
     upper_port => 587,
     ace => xs$ace_type(privilege_list => xs$name_list('SMTP'),
                        principal_name => '<schema-name>',
                        principal_type => xs_acl.ptype_db));
END;
/


/*
View all Credentials Created
*/


-- View all Databse Credentials
SELECT * FROM ALL_CREDENTIALS;


/*
End of Notebook 
*/

