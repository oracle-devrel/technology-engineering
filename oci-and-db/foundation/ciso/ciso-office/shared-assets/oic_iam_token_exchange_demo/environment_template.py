#VARIABLES TO CHANGE FOR YOUR ENVIRONMENT
#########################################

#IDCS Instance Variables
idcs_url = "" # e.g. "https://idcs-1234.identity.oraclecloud.com/" 
idcs_client_id="" # e.g. e123432ejcn43k2kdkrkfkke
idcs_client_secret=""# e.g. e123432-ejcn-43k2-kdkr-kfdswe33kke

#Endpoint audience that you will be requesting an IDCS token for, e.g. "https://EAFE304003E34FA56.integration.ocp.oraclecloud.com:443"
target_audience="" 

#Scope of the target resource,  e.g. "urn:opc:resource:consumer::all"
idcs_scope=target_audience + ""

#Target Instance Variables
#FQDN of the target host you will be calling with your IDCS token, e.g. "https://oic-fr2323hpc-fr.integration.ocp.oraclecloud.com"
target_host="" 

# URI of your target endpoint, e.g. "/ic/api/integration/v1/flows/rest/ECHO/1.0/Testing"
target_url= target_host + ""

#Scope of your registered application which you will request in your IDCS token, e.g. "https://EAFE304003E34FA56.integration.ocp.oraclecloud.com:443urn:opc:resource:consumer::all"
idcs_scope=""


#User Variables
#User ID to include in your locally generated token
userID = ""

#JWT Variables
#Value to set for your JWT KID
jwt_kid = ""

#Local Variables (place keys/certs in keys folder and change filename below accordingly)
private_key = "keys/local_private_key.pem"
public_key = "keys/local_publickey.pub"
public_cert = "keys/local_public_certificate.crt"

#OCI Secret Variables
#OCID of the secret in which you have uploaded your private key in Vault (if using Vault integration)
secret_id = ""

#Profile name for your OCI CLI (must be configured locally if using Vault integration)
oci_profile = ""
