import requests
import os

def cleanup_local_files():
    if (os.path.isfile("saml.xml")):
        os.remove("saml.xml")
    if (os.path.isfile("signedsaml.xml")):
        os.remove("signedsaml.xml")
    if (os.path.isfile("idcs_jwt.json")):
        os.remove("idcs_jwt.json")

def call_target(url, idcs_jwt_token=""):
    status = ""
    headers = ""
    if (idcs_jwt_token != ""):
        authorization_header="Bearer " + idcs_jwt_token
        headers = {"Authorization":authorization_header}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 401:
            return response.status_code
        else:
            return response.content
    except Exception as e:
        print('ERROR: Could not retrieve data from target' + status)
        raise

