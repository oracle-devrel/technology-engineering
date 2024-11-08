# Copyright (c) 2023 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
import datetime
import io
import json
import logging
from datetime import timedelta

import requests
from fdk import response
from requests.auth import HTTPBasicAuth

import ociVault

oauth_apps = {}

def initContext(context):
    # This method takes elements from the Application Context and from OCI Vault to create the OAuth App Clients object.
    if (len(oauth_apps) < 2):
        logging.getLogger().info('Retriving details about the API and backend OAuth Apps')
        try:
            logging.getLogger().info('initContext: Initializing context')
            
            # Using ociVault
            oauth_apps['apigw'] = {'introspection_endpoint': context['idcs_introspection_endpoint'], 
                                  'client_id': context['introspection_idcs_app_client_id'], 
                                  'client_secret': ociVault.getSecret(context['introspection_idcs_app_client_secret_ocid'])}
            oauth_apps['oic'] = {'token_endpoint': context['idcs_token_endpoint'], 
                                  'client_id': context['oic_idcs_app_client_id'], 
                                  'client_secret': ociVault.getSecret(context['oic_idcs_app_client_secret_ocid']), 'scope': context['oic_scope']}

        except Exception as ex:
            logging.getLogger().error('initContext: Failed to get config or secrets')
            print("ERROR [initContext]: Failed to get the configs", ex, flush=True)
            raise
    else:
        logging.getLogger().info('initContext: OAuth Apps already stored')

def introspectToken(access_token, introspection_endpoint, client_id, client_secret):
    # This method handles the introspection of the received auth token to IDCS.  
    payload = {'token': access_token}
    headers = {'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8', 
               'Accept': 'application/json'}
               
    try:
        token = requests.post(introspection_endpoint, 
                              data=payload, 
                              headers=headers, 
                              auth=HTTPBasicAuth(client_id, client_secret))

    except Exception as ex:
        logging.getLogger().error("introspectToken: Failed to introspect token" + ex)
        raise

    return token.json()

def getBackEndAuthToken(token_endpoint, client_id, client_secret, scope):
    # This method gets the token from the back-end system (oic in this case)
    payload = {'grant_type': 'client_credentials', 'scope': scope}
    headers = {'Content-Type' : 'application/x-www-form-urlencoded;charset=UTF-8', 
               'Accept': 'application/json'}
    
    try:
        backend_token = requests.post(token_endpoint,
                                    data=payload,
                                    headers=headers,
                                    auth=HTTPBasicAuth(client_id, client_secret))

        logging.getLogger().info("getBackEndAuthToken: Got the backend token " + backend_token.text)

    except Exception as ex:
        logging.getLogger().error("getBackEndAuthToken: Failed to get the backend token" + ex)
        raise
    
    return backend_token.json()

def getAuthContext(token, client_apps):
    # This method populates the Auth Context that will be returned to the gateway.
    auth_context = {}

    # Calling IDCS to validate the token and retrieve the client info
    try:
        token_info = introspectToken(token[len('Bearer '):], client_apps['apigw']['introspection_endpoint'], client_apps['apigw']['client_id'], client_apps['apigw']['client_secret'])

    except Exception as ex:
            logging.getLogger().error("getAuthContext: Failed to introspect token" + ex)
            raise

    # If IDCS confirmed the token is valid and active, we can proceed to populate the auth context
    if (token_info['active'] == True):
        auth_context['active'] = True
        # auth_context['principal'] = token_info['sub']
        auth_context['client_id'] = token_info['client_id']
        auth_context['scope'] = token_info['scope']
        
        # Retrieving the back-end Token
        backend_token = getBackEndAuthToken(client_apps['oic']['token_endpoint'], client_apps['oic']['client_id'], client_apps['oic']['client_secret'], client_apps['oic']['scope'])

        # The maximum TTL for this auth is the lesser of the API Client Auth (IDCS) and the Gateway Client Auth (oic)
        if (datetime.datetime.fromtimestamp(token_info['exp']) < (datetime.datetime.utcnow() + timedelta(seconds=backend_token['expires_in']))):
            auth_context['expiresAt'] = (datetime.datetime.fromtimestamp(token_info['exp'])).replace(tzinfo=datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat()
        else:
            auth_context['expiresAt'] = (datetime.datetime.utcnow() + timedelta(seconds=backend_token['expires_in'])).replace(tzinfo=datetime.timezone.utc).astimezone().replace(microsecond=0).isoformat()

        # Storing the back_end_token in the context of the auth decision so we can map it to Authorization header using the request/response transformation policy
        auth_context['context'] = {'back_end_token': ('Bearer ' + str(backend_token['access_token']))}

    else:
        # API Client token is not active, so we will go ahead and respond with the wwwAuthenticate header
        auth_context['active'] = False
        auth_context['wwwAuthenticate'] = 'Bearer realm=\"identity.oraclecloud.com\"'

    return(auth_context)

def handler(ctx, data: io.BytesIO=None):
    logging.getLogger().info('Entered Handler')
    initContext(dict(ctx.Config()))
      
    auth_context = {}
    try:
        gateway_auth = json.loads(data.getvalue())

        auth_context = getAuthContext(gateway_auth['data']['token'], oauth_apps)

        if (auth_context['active']):
            logging.getLogger().info('Authorizer returning 200...')
            return response.Response(
                ctx,
                response_data=json.dumps(auth_context),
                status_code = 200,
                headers={"Content-Type": "application/json"}
                )
        else:
            logging.getLogger().info('Authorizer returning 401...')
            return response.Response(
                ctx,
                response_data=json.dumps(str(auth_context)),
                status_code = 401,
                headers={"Content-Type": "application/json"}
                )

    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))

        return response.Response(
            ctx,
            response_data=json.dumps(str(auth_context)),
            status_code = 401,
            headers={"Content-Type": "application/json"}
            )

