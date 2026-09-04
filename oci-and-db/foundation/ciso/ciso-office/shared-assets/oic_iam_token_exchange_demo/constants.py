import random
import datetime
import environment as env

#####Common Values#####
idcs_token_endpoint_url = env.idcs_url + "/oauth2/v1/token"
token_validity_in_seconds = 600
content_type = {'Content-type': 'raw'}
id = str(random.randint(10000,99999))
idcs_audience = "https://identity.oraclecloud.com/"

#####Local SAML Request Values#####
saml_grant_type = "urn:ietf:params:oauth:grant-type:saml2-bearer"

#####Local SAML Assertion Values#####
xmlns = "urn:oasis:names:tc:SAML:2.0:assertion"
version = "2.0"
issuer = env.idcs_client_id
nameIdFormat = "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress"
subjectConfirmation = "urn:oasis:names:tc:SAML:2.0:cm:bearer"
recipient = 'https://identity.oraclecloud.com/'
authnContextClassRef = "urn:oasis:names:tc:SAML:2.0:ac:classes:X509"
issueInstant = str(datetime.datetime.utcnow().isoformat() + 'Z')
notOnOrAfter = str((datetime.datetime.utcnow()+datetime.timedelta(seconds=token_validity_in_seconds)).isoformat() + 'Z')

#####Local JWT Request Values#####
jwt_grant_type = "urn:ietf:params:oauth:grant-type:jwt-bearer"

##### Local JWT Token Values######
iat = datetime.datetime.utcnow()
exp = datetime.datetime.utcnow()+datetime.timedelta(seconds=token_validity_in_seconds)
algorithm = "RS256"
header = {
  "typ": "JWT",
  "alg": algorithm,
  "kid": env.jwt_kid
}
jwt_input={
 "sub":env.userID,
 "aud": [
 idcs_audience
 ],
 "iss": env.idcs_client_id,
 "prn": env.userID,
  "iat": iat,
  "exp": exp,
 "jti": id
}