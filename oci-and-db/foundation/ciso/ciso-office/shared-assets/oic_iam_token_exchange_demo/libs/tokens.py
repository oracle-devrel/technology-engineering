import jwt
import requests
import json
import constants
import environment as env
import base64
import xml.etree.cElementTree as ET
import re

from requests.models import HTTPBasicAuth
from lxml import etree
from signxml import XMLSigner, XMLVerifier

###JWT
#Create the local JWT token
def generate_local_jwt_token(private_key):

    # Lets create the JWT token -- this is a byte array, meant to be sent as an HTTP header
    try:
        jwt_token = jwt.encode(constants.jwt_input, key=private_key, algorithm=constants.algorithm, headers=constants.header)
        return jwt_token
    except Exception as e:
        print('ERROR: Could not generate local JWT token')
        raise

#Exchange local token for IDCS token
def swap_local_token_for_idcs_jwt(local_token, tokentype):
    try:
        if (tokentype == "jwt"):
            response = requests.post(constants.idcs_token_endpoint_url, auth=HTTPBasicAuth(env.idcs_client_id, env.idcs_client_secret), data={'grant_type':constants.jwt_grant_type, 'assertion':local_token,'scope':env.idcs_scope})
        else: 
             response = requests.post(constants.idcs_token_endpoint_url, auth=HTTPBasicAuth(env.idcs_client_id, env.idcs_client_secret), data={'grant_type':constants.saml_grant_type, 'assertion':local_token,'scope':env.idcs_scope})
        JSONResponse = response.json()
        #print(JSONResponse)
        return JSONResponse['access_token']
    except Exception as e:
        print('ERROR: Cannot retrieve IDCS token')
        raise
    return idcs_jwt_token

#Decode JWT token
def decode_jwt_token(jwt_token, public_key, token_type="idcs"):
    if (token_type == "local"):
        decoded_jwt_token = jwt.decode(jwt_token, public_key, audience=constants.idcs_audience, algorithms=constants.algorithm)
    else:
        decoded_jwt_token=jwt.decode(jwt_token, audience=env.target_audience, algorithms=constants.algorithm, options={"verify_signature": False})
    return json.dumps(decoded_jwt_token, indent=4)

###SAML
#Generate the local SAML assertion
def generateSAML():
    assertion = ET.Element("Assertion", IssueInstant=constants.issueInstant, ID=constants.id, Version=constants.version, xmlns=constants.xmlns)
    Issuer = ET.SubElement(assertion, "Issuer").text = constants.issuer
    Subject = ET.SubElement(assertion, "Subject")
    SubjectNameId = ET.SubElement(Subject, "NameID", Format=constants.nameIdFormat).text = env.userID
    SubjectConfirmation = ET.SubElement(Subject, "SubjectConfirmation", Method=constants.subjectConfirmation)
    SubjectConfirmationData = ET.SubElement(SubjectConfirmation, "SubjectConfirmationData", NotOnOrAfter=constants.notOnOrAfter, Recipient=constants.recipient)
    Conditions = ET.SubElement(assertion, "Conditions")
    AudienceRestriction = ET.SubElement(Conditions, "AudienceRestriction")
    Audience = ET.SubElement(AudienceRestriction, "Audience").text = constants.idcs_audience

    AuthnStatement = ET.SubElement(assertion, "AuthnStatement", AuthnInstant=constants.issueInstant)

    AuthnContext = ET.SubElement(AuthnStatement, "AuthnContext")

    AuthnContextClassRef = ET.SubElement(AuthnContext, "AuthnContextClassRef").text = constants.authnContextClassRef

    samltree = ET.ElementTree(assertion)
    samltree.write("saml.xml")
    return samltree

#Digitally sign the local SAML assertion
def signSAML(privateKey):
    with open('saml.xml', 'r') as file :
        data_to_sign = file.read()
    with open(env.public_cert, 'r') as cert:
        certificate = cert.read()
    p = re.search('<Subject>', data_to_sign).start()
    tmp_message = data_to_sign[:p]
    tmp_message = tmp_message +\
              '<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="placeholder"></ds:Signature>'
    data_to_sign = tmp_message + data_to_sign[p:]
    saml_root = etree.fromstring(data_to_sign)
    signed_saml_root = XMLSigner(c14n_algorithm="http://www.w3.org/2001/10/xml-exc-c14n#")\
    .sign(saml_root, key=privateKey, cert=certificate)
    verified_data = XMLVerifier().verify(signed_saml_root, x509_cert=certificate).signed_xml
    signed_saml_root_str = etree.tostring(signed_saml_root, encoding='unicode')
    with open('signedsaml.xml', 'w') as file:
        file.write(signed_saml_root_str)

#Open the file to return to the calling function
def openSignedSamlAssertion():
    with open('signedsaml.xml', 'r') as file:
        signed_saml = file.read()
    return signed_saml

#Base64 encode the file to pass to IDCS
def b64EncodeSaml():
    with open('signedsaml.xml', 'rb') as file:
        encoded = base64.encodebytes(file.read()).decode("utf-8")
    return encoded