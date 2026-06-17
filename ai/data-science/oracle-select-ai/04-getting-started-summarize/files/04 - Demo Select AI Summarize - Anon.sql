-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Select AI - Summarize
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
SELECT DBMS_CLOUD_AI.GET_PROFILE() from dual;


/*
SUMMARIZE - Generate Text Summaries
*/


-- If your text contains empty double quotes (""), enclose the text using q'[]' mechanism. 
select ai summarize q'[Oracle Corporation is an American multinational technology company headquartered in Austin, Texas.[5] Co-founded in 1977 in Santa Clara, California, by its current chairman of the board and chief technology officer Larry Ellison,[6][7] Oracle is among the 20 largest companies in the world[8] by market cap, and ranked 66th[9] on the Forbes Global 2000 as of 2025. The company sells database software (particularly the Oracle Database), enterprise applications, and cloud infrastructure and hardware. Oracles core application software is a suite of enterprise software products, including enterprise resource planning (ERP), human capital management (HCM), customer relationship management (CRM), enterprise performance management (EPM), Customer Experience Commerce (CX Commerce) and supply chain management (SCM) software.[10] History See also- List of acquisitions by Oracle Larry Ellison, executive chairman and co-founder of Oracle Oracle Corporations former headquarters in Redwood Shores, California USA 17 at Oracle Corporation Headquarters Picture of the Oracle Austin Riverside Campus in 2018 Larry Ellison, Bob Miner, and Ed Oates co-founded Oracle in 1977 in Santa Clara, California, as Software Development Laboratories (SDL).[2][11] Beginning as consultants with a background in large-scale memory after a project for Ampex,[12] Ellison took inspiration[13] from the 1970 paper written by Edgar F. Codd on relational database management systems (RDBMS) named A Relational Model of Data for Large Shared Data Banks.[14] He heard about the IBM System R database[12] from an article in an IBM research journal provided by Oates. Ellison wanted to make Oracles product compatible with System R, but failed to do so as IBM kept the error codes for their DBMS a secret. SDL changed its name to Relational Software, Inc (RSI) in 1979,[15] then again to Oracle Systems Corporation in 1983,[16] to align itself more closely with its flagship product Oracle Database. The name also drew from the codename of a 1977 project for the Central Intelligence Agency, Oracles first customer[17][18][11] the company received permission to use the code name for the new product.[12] (According to Oracle executive Mike Humphries, Miner told him that the new company had the choice of the CIA database project or another offer to develop a compiler for the PDP-4, and the founders flipped a coin to decide.)[19] Miner served as a senior programmer, and Oates also worked in development. The three founders decided that Ellison was the worst programmer so he became the salesman. Understanding both customers and technology, Ellison designed database tables that he used to demonstrate the power of SQL to customers.[12] By February 1983 the Rosen Electronics Letter said that Oracle was the most comprehensive offering weve seen among databases, with good marketing and a substantial installed base encouraging developers to write software for it. The newsletter said that revenue in fiscal 1983 would be about $8 million and would double in 1984.[20] On March 12, 1986, the company had its initial public offering.[21] In 1989, Oracle moved its world headquarters to the Redwood Shores neighborhood of Redwood City, California, though its campus[22] was not completed until 1995.[23] The company hired so many from top universities that Humphries compared it to Cargill buying crops. Some new employees worked as receptionists or distributed coffee until more suitable positions became available.]';


/*
Use SUMMARIZE Function - Text Input
*/

set long 5000

-- Call Summarize Function with Text Input
SELECT DBMS_CLOUD_AI.SUMMARIZE(
  content         => 'Oracle Corporation is an American multinational technology company headquartered in Austin, Texas.[5] Co-founded in 1977 in Santa Clara, California, by its current chairman of the board and chief technology officer Larry Ellison,[6][7] Oracle is among the 20 largest companies in the world[8] by market cap, and ranked 66th[9] on the Forbes Global 2000 as of 2025. The company sells database software (particularly the Oracle Database), enterprise applications, and cloud infrastructure and hardware. Oracles core application software is a suite of enterprise software products, including enterprise resource planning (ERP), human capital management (HCM), customer relationship management (CRM), enterprise performance management (EPM), Customer Experience Commerce (CX Commerce) and supply chain management (SCM) software.[10] History See also- List of acquisitions by Oracle Larry Ellison, executive chairman and co-founder of Oracle Oracle Corporations former headquarters in Redwood Shores, California USA 17 at Oracle Corporation Headquarters Picture of the Oracle Austin Riverside Campus in 2018 Larry Ellison, Bob Miner, and Ed Oates co-founded Oracle in 1977 in Santa Clara, California, as Software Development Laboratories (SDL).[2][11] Beginning as consultants with a background in large-scale memory after a project for Ampex,[12] Ellison took inspiration[13] from the 1970 paper written by Edgar F. Codd on relational database management systems (RDBMS) named A Relational Model of Data for Large Shared Data Banks.[14] He heard about the IBM System R database[12] from an article in an IBM research journal provided by Oates. Ellison wanted to make Oracles product compatible with System R, but failed to do so as IBM kept the error codes for their DBMS a secret. SDL changed its name to Relational Software, Inc (RSI) in 1979,[15] then again to Oracle Systems Corporation in 1983,[16] to align itself more closely with its flagship product Oracle Database. The name also drew from the codename of a 1977 project for the Central Intelligence Agency, Oracles first customer[17][18][11] the company received permission to use the code name for the new product.[12] (According to Oracle executive Mike Humphries, Miner told him that the new company had the choice of the CIA database project or another offer to develop a compiler for the PDP-4, and the founders flipped a coin to decide.)[19] Miner served as a senior programmer, and Oates also worked in development. The three founders decided that Ellison was the worst programmer so he became the salesman. Understanding both customers and technology, Ellison designed database tables that he used to demonstrate the power of SQL to customers.[12] By February 1983 the Rosen Electronics Letter said that Oracle was the most comprehensive offering weve seen among databases, with good marketing and a substantial installed base encouraging developers to write software for it. The newsletter said that revenue in fiscal 1983 would be about $8 million and would double in 1984.[20] On March 12, 1986, the company had its initial public offering.[21] In 1989, Oracle moved its world headquarters to the Redwood Shores neighborhood of Redwood City, California, though its campus[22] was not completed until 1995.[23] The company hired so many from top universities that Humphries compared it to Cargill buying crops. Some new employees worked as receptionists or distributed coffee until more suitable positions became available.',
  profile_name    => '<enter-ai-profile-name>',
  params          => '{"max_words":"500",
                        "min_words":"100",
                        "summary_style":"paragraph",
                        "chunk_processing_method": "map_reduce",
                        "extractiveness_level":"medium"
                      }',
  user_prompt     => 'The summary should start with ''The summary of '
) AS RESPONSE
FROM DUAL;


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
Use SUMMARIZE Function - Object Storage Input
*/


set long 5000

-- Call Summarize Function with Object Storage Input
SELECT DBMS_CLOUD_AI.SUMMARIZE(
                location_uri    => '<enter-file-object-storage-uri>',
                credential_name => '<enter-oci-auth-token-credential-name>',
                profile_name    => '<enter-ai-profile-name>',
                params          => '{"max_words":"500",
                                    "min_words":"100",
                                    "summary_style":"list",
                                    "chunk_processing_method": "iterative_refinement",
                                    "extractiveness_level":"medium"
                                }',
                user_prompt     => 'The summary should start with - The summary of..') AS RESPONSE
FROM DUAL;
/
 

/*
End of Notebook
*/

