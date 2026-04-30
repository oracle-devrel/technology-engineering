/*
Select AI - Translate
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
-- Your AI Profile must specify the target language
BEGIN                                                                          
	DBMS_CLOUD_AI.CREATE_PROFILE
        (                                                
		        profile_name => '<enter-ai-profile-name>'
		    ,   attributes   => '{
                                        "provider"          : "oci"
                                    ,   "target_language"   : "english"
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
SELECT DBMS_CLOUD_AI.GET_PROFILE() FROM DUAL;


/*
View Supported Languages for Translation
*/


SELECT * FROM AI_TRANSLATION_LANGUAGES WHERE PROVIDER = 'OCI';


/*
TRANSLATE - Between Languages
*/


-- Translate from Dutch
select ai translate Ik moet dit vertalen;


-- Translate from French
select ai translate Je dois traduire ceci;


-- Translate from Arabic
select ai translate أحتاج إلى ترجمة هذا;


-- Use the Translate Function
SELECT 
    DBMS_CLOUD_AI.TRANSLATE(
        profile_name    => '<enter-ai-profile-name>',
        text            => 'Ik moet dit vertalen',
        source_language => 'Dutch',
        target_language => 'English'
    ) AS TRANSLATION
FROM DUAL;
 

-- Use the Generate Function
SELECT 
    DBMS_CLOUD_AI.GENERATE(
        prompt            => 'Je dois traduire ceci',
        profile_name      => '<enter-ai-profile-name>',
        action            => 'translate',
        attributes        => '{"target_language": "en", "source_language": "fr"}'
    ) AS TRANSLATION
FROM DUAL;


/*
End of Notebook
*/

