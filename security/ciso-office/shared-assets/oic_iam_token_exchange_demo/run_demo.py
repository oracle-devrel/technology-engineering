import os
import environment as env

from libs.keys import load_private_key, load_public_key #handles the key loading
from libs.utils import call_target, cleanup_local_files
from libs.tokens import generate_local_jwt_token, swap_local_token_for_idcs_jwt, decode_jwt_token, generateSAML, signSAML, openSignedSamlAssertion, b64EncodeSaml

#Initialisation
cleanup_local_files()

#Call target without any token
os.system('clear')
print('\n***********CALLING OIC TARGET API ENDPOINT WITHOUT TOKEN***********\n')
print(env.url + "\n")
endpoint_test_call = call_target(env.target_url)
print("Status: " + str(endpoint_test_call))
print('\n*******************************************************************\n')
wait = input("Press Enter to continue.")

#Asking user where to obtain the private key from
keylocation = input("\nPress 1 to retrieve keys from local file, or 2 to retrieve keys from OCI Vault (Default = 1): ")
if (not keylocation) or (int(keylocation) == 1):
    private_key = load_private_key("local")
    print('\n***********LOADED PRIVATE KEY FROM LOCAL FILE***********\n')
else:
    private_key = load_private_key("vault")
    print('\n***********LOADED PRIVATE KEY FROM OCI VAULT***********\n')

#Load the public key from a file
public_key = load_public_key()

#Asking user whether to generate a local SAML or JWT token, which will be passed to IAM for exchange.
localtokeninput = input("\nPress 1 to create local JWT token, or 2 to create local SAML token (Default = 1): ")
if (not localtokeninput) or (int(localtokeninput) == 1):
    localtokentype = "jwt"
    print('\n***********JWT TOKEN SELECTED***********\n')
else:
    localtokentype = "saml"
    print('\n***********SAML TOKEN SELECTED***********\n')

#Generate the local token depending on the user's initial token type selection
if (localtokentype == "jwt"):  
    #Generate the local JWT token
    print('\n***********GENERATING LOCAL JWT TOKEN***********\n')
    local_jwt_token = generate_local_jwt_token(private_key)
    decoded_local_jwt_token = decode_jwt_token(local_jwt_token, public_key, "local")
    print(decoded_local_jwt_token)
    print('\n************************************************\n')
    wait = input("Press Enter to continue.")
else:
    #Generate the local SAML token
    print('\n***********GENERATING LOCAL SAML TOKEN***********\n') 
    generateSAML()
    signSAML(private_key)
    local_saml_token = openSignedSamlAssertion()
    print(local_saml_token)
    print('\n************************************************\n')
    wait = input("Press Enter to continue.")

#Call IDCS to swap local token from IDCS JWT token
if (localtokentype == "jwt"):
    idcs_jwt_token = swap_local_token_for_idcs_jwt(local_jwt_token, "jwt")
else:
    local_saml_token = b64EncodeSaml()
    idcs_jwt_token = swap_local_token_for_idcs_jwt(local_saml_token, "saml")
decoded_idcs_jwt_token = decode_jwt_token(idcs_jwt_token, public_key)
print('\n***********SWAPPING LOCAL JWT TOKEN FOR IDCS JWT TOKEN SCOPED for OIC***********\n')
print(decoded_idcs_jwt_token)
print('\n*****************************************************************\n')
wait = input("Press Enter to continue.")

#Call target with IDCS JWT token
print('\n***********CALLING OIC ENDPOINT WITH IDCS JWT TOKEN***********\n')
target_response = call_target(env.target_url, idcs_jwt_token)
print(target_response)
print('\n**************************************************************\n')
