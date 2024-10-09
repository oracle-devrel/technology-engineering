import os
import base64
import requests
import time
import jwt
import json
from six.moves.urllib.parse import urlparse
from six.moves import urllib
import six
from Constants import Constants
import logging
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import simplejson as json
import re
from lruttl import LRUCache
import warnings
import functools




def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emitted
    when the function is used."""
    @functools.wraps(func)
    def deprecatedWarning(*args, **kwargs):
        warnings.simplefilter('always', DeprecationWarning)  # turn off filter
        warnings.warn("Call to deprecated function {}.".format(func.__name__),
                      category=DeprecationWarning,
                      stacklevel=2)
        warnings.simplefilter('default', DeprecationWarning)  # reset filter
        return func(*args, **kwargs)
    return deprecatedWarning

class MetadataManager:
    """
    This class provide methods to retrieve and manage the metadata for a tenant.
    """

    def __init__(self, options, tenant = None):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = options
        if tenant is not None:
            self.tenant = tenant
        else:
            self.tenant =  Utils.getTenant(self.options)
        self.logger = Utils.getLogger(options)

    def getMetaData(self):
        """
        It returns the metadata as a JSON object.
        The tenant for which metadata is returned is determined from the BaseUrl present in options
        :return: JSON Object of tenant's metadata
        """
        tenant = self.tenant
        if tenant.lower() in CacheManager.metadata:
            self.logger.debug("Metadata found in cache. Checking for expiry.")
            md = CacheManager.metadata[tenant.lower()]

            if md.getExpiry() > round(time.time()):
                self.logger.debug("Metadata not expired. Returning from cache.")
                return CacheManager.metadata[tenant.lower()]

            self.logger.debug("Metadata expired. Going to Fetch new metadata.")

        if Constants.BASE_URL not in self.options:
            raise ValueError("BaseUrl is missing in required options for fetching Metadata.")
        url = self.options[Constants.BASE_URL]
        url += Constants.DISCOVERY_PATH
        self.logger.debug("Going to fetch metadata from %s", url)
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.get(url, verify=verify)
        if response.status_code == 200 :
            md = response.json()
            ret = Metadata(md)
            CacheManager.metadata[tenant.lower()] = ret
            self.logger.debug("Metadata fetch successful. Persisting in cache and returning.")
            return ret
        self.logger.error("Unable to fetch Metadata. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Metadata. Response text server %s", response.text)
        raise IdcsException("Failed to fetch Metadata", response)


class AccessTokenManager:
    """
    This class provide methods to fetch and manage access token to perform operations like fetching user details, jwk
    """

    def __init__(self, options):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = options
        self.logger = Utils.getLogger(options)

    def getAccessToken(self):
        """
        This method returns a access token for urn:opc:idm:__myscopes__ using client credentials given in options
        :return: Access Token for scope urn:opc:idm:__myscopes__
        """
        tenant = Utils.getTenant(self.options)
        if tenant.lower() in CacheManager.tokens:
            self.logger.debug("Access Token found in cache. Going to check expiry.")
            token = CacheManager.tokens[tenant.lower()]
            ret = jwt.decode(token, options={"verify_signature": False},algorithms=['RS256'])
            curTime = round(time.time()) + 120
            if ret[Constants.TOKEN_CLAIM_EXPIRY] > curTime :
                self.logger.debug("Access Token valid. Returning from cache.")
                return token
            else:
                self.logger.debug("AccessToken expired.")

        self.logger.debug("Going to fetch new Access Token.")
        am = AuthenticationManager(self.options)
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        res = am.clientCredentials(Constants.MY_SCOPES)
        CacheManager.tokens[tenant.lower()] = res.getAccessToken()
        self.logger.debug("Access Token fetched successfully. Persisting in cache and returning.")
        return res.getAccessToken()


class UserAssert:

    def __init__(self, options, cacheManager):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = options
        self.logger = Utils.getLogger(options)
        self.asserterCache = cacheManager.getAsserterCache()

    def assertClaims(self, jwt):
        """
        This method asserts the identity with App Roles and Group Memberships for a given token
        :param token: Access Token or Id Token
        :return: a JSON Object with asserted Attributes else throws IDCSException
        """
        id = None
        tenant = None
        subType = None
        claim_user_id = self.options[Constants.USER_ID_TOK_CLAIM] if Constants.USER_ID_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_USER_ID
        if "AT" == jwt[Constants.TOKEN_CLAIM_TOKEN_TYPE] and claim_user_id not in jwt:
            id = jwt[self.options[Constants.CLIENT_ID_TOK_CLAIM] if Constants.CLIENT_ID_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_CLIENT_ID]
            tenant = jwt[self.options[Constants.CLIENT_TENANT_TOK_CLAIM] if Constants.CLIENT_TENANT_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_CLIENT_TENANT]
        else:
            id = jwt[claim_user_id]
            tenant = jwt[self.options[Constants.USER_TENANT_TOKEN_CLAIM] if Constants.USER_TENANT_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_USER_TENANT]

        if Constants.TOKEN_CLAIM_SUB_TYPE in jwt:
            subType = jwt[Constants.TOKEN_CLAIM_SUB_TYPE]
        if six.PY2:
            id = id.encode("utf-8")

        # if "AT" == jwt[Constants.TOKEN_CLAIM_TOKEN_TYPE] and not id.endswith("_APPID"):
        #     return jwt

        if Constants.ONLY_USER_TOK_CLAIM_ENABLED in self.options and not self.options[Constants.ONLY_USER_TOK_CLAIM_ENABLED]:
            group_claim = self.options[Constants.GROUP_TOKEN_CLAIM] if Constants.GROUP_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_GROUPS
            appRole_claim = self.options[Constants.APP_ROLE_TOKEN_CLAIM] if Constants.APP_ROLE_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_APP_ROLES
            if group_claim in jwt or appRole_claim in jwt:
                return jwt

        key = tenant + ":" + id
        if self.asserterCache.contains(key):
            self.logger.debug("Claims Found in Cache. Returning from cache")
            claims = self.asserterCache.get(key)
            jwt.update(claims)
            return
        mdm = MetadataManager(self.options, tenant)
        md = mdm.getMetaData()
        url = md.getAsserterUrl()

        atm = AccessTokenManager(self.options)
        at = atm.getAccessToken()

        headers = {}
        headers[Constants.HEADER_AUTHORIZATION] = Constants.AUTH_BEARER % at
        headers[Constants.HEADER_CONTENT] = Constants.APPLICATION_JSON

        body = {}
        if Constants.APP_NAME in self.options:
            body[Constants.IDCS_APPNAME_FILTER_ATTRIB] = self.options[Constants.APP_NAME]

        if (id.endswith("_APPID") or (subType is not None and subType == "client")):
            var = "do nothing here"
        else:
            body[Constants.IDCS_MAPPING_ATTRIBUTE] = self.options[Constants.USER_ID_RES_ATTR] if Constants.USER_ID_RES_ATTR in self.options else Constants.MAPPING_ATTR_ID
        # if not id.endswith("_APPID"):
        #     body[Constants.IDCS_MAPPING_ATTRIBUTE] = self.options[Constants.USER_ID_RES_ATTR] if Constants.USER_ID_RES_ATTR in self.options else Constants.MAPPING_ATTR_ID
        body[Constants.IDCS_MAPPING_ATTRIBUTE_VALUE] = id
        schemas = [Constants.IDCS_ASSERTER_SCHEMA]
        body[Constants.IDCS_SCHEMAS] = schemas
        body[Constants.IDCS_INCLUDE_MEMBERSHIPS] = True
        if (subType is not None and subType == "client"):
            body[Constants.SUBJECT_TYPE_ATTR]  =  subType

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, json=body, headers=headers, verify=verify)
        if response.status_code != 201 and response.status_code != 200:
            self.logger.error("Unable to Assert Claims. Response Code from server %s", str(response.status_code))
            self.logger.error("Unable to Assert. Response text server %s", response.text)
            raise IdcsException("Failed to Assert Claims", response)
        res = response.json()
        ##CacheManager.asserterCache[key] = res
        self.asserterCache.put(key,res)
        jwt.update(res)
        return jwt


class TokenVerifier:
    """
    This class provide methods to verify access and id tokens
    """

    def __init__(self, options, cacheManager = None):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = options
        self.logger = Utils.getLogger(options)
        if cacheManager is None:
            cacheManager = CacheManager()
        self.fqsCache = cacheManager.getFqsCache()


    def verifyJwtToken(self, token):
        """
        This method verifies a JWT token, its signature, and expiry
        :param token: JWT Token
        :return: decoded JWT token as a JSON Object
        """
        try:
            header = jwt.get_unverified_header(token)
            decoded = jwt.decode(token, options={"verify_signature": False},algorithms=['RS256'])
        except:
            raise IdcsException("Failed to Decode JWT Token")

        tenant = Utils.getTenantNameFromClaim(decoded, self.options)
        kid = header[Constants.HEADER_CLAIM_KEY_ID]
        km = KeyManager(self.options, tenant)
        jwks = km.fetchKey()
        for val in jwks[Constants.KEYS]:
            if val.get(Constants.HEADER_CLAIM_KEY_ID) is not None and val[Constants.HEADER_CLAIM_KEY_ID] == kid:
                jwk = val
                break
        else:
            jwk = jwks[Constants.KEYS][0]

        x5c = jwk[Constants.X5C][0]
        try:
            cert_obj = x509.load_der_x509_certificate(base64.b64decode(x5c), default_backend())
            public_key = cert_obj.public_key()
            options = {
                'verify_signature': True,
                'verify_exp': False,
                'verify_nbf': False,
                'verify_iat': False,
                'verify_aud': False
            }
            level = self.options[Constants.TOKEN_VALIDATION_LEVEL] if Constants.TOKEN_VALIDATION_LEVEL in self.options else Constants.VALIDATION_LEVEL_FULL
            verify = False if Constants.VALIDATION_LEVEL_NONE == level else True
            ret = jwt.decode(token, public_key, options=options, verify=verify, algorithms=[jwk[Constants.ALG]], issuer=Utils.getTokenIssuerUrl(self.options))
            skew = Constants.TOKEN_CLOCK_SKEW_DEFAULT_VALUE
            if Constants.TOKEN_CLOCK_SKEW in self.options:
                skew = self.options[Constants.TOKEN_CLOCK_SKEW]
            if (ret[Constants.TOKEN_CLAIM_EXPIRY] + skew) <= round(time.time()):
                self.logger.debug("JWT Token is expired.")
                raise IdcsException("JWT Token is expired")

            crossTenant = False
            if Constants.CROSS_TENANT in self.options:
                crossTenant = self.options[Constants.CROSS_TENANT]
            if crossTenant:
                res = re.search("idcs-[(a-z)|(0-9)]{32}$", tenant)
                if res is None:
                    raise IdcsException("tenant present is token doesnot comply with idcs standards")
            else:
                if Utils.getTenant(self.options).lower() != tenant.lower():
                    raise IdcsException("tenant present is token doesn't match with already configured tenant")
            return ret
        except Exception as e:
            self.logger.error(e)
            error = "Failed to Verify Signature on JWT Token"
            if(e.args is not None and e.args[0] is not None):
                error += ": "+e.args[0]
            raise IdcsException(error)

    def validateAudience(self, token, isIdToken):
        """
        Method to validate Audience
        :param token: decoded JWT as a JSON Object
        :param isIdToken: true if token id_token else false
        :return: true is Audience is valid else false
        """
        if Constants.TOKEN_CLAIM_AUDIENCE not in token:
            if Constants.TOKEN_CLAIM_SCOPE not in token:
                return False
            else:
                scope = token[Constants.TOKEN_CLAIM_SCOPE]
                return Utils.isEmpty(scope)
        else:
            aud = token[Constants.TOKEN_CLAIM_AUDIENCE]
            if not isinstance(aud, list):
                aud = [aud]
            necessary = self.getNecessaryAudience(aud)
            if len(necessary) == 0:
                return self.validateSufficientAudience(token, aud,isIdToken)
            else:
                return self.validateNecessaryAudience(token, necessary)

    def getNecessaryAudience(self, aud):
        necessary = []
        for audience in aud:
            if audience.startswith(Constants.NECESSARY_AUDIENCE_PREFIX):
                necessary.append(audience)
        return necessary

    def validateSufficientAudience(self, token, aud, isIdToken):
        if self.options[Constants.CROSS_TENANT] and isIdToken:
            self.logger.info("validateSufficientAudience for idToken and cross tenant case returning true")
            return True
        resourceTenant = Utils.getTenantNameFromClaim(token, self.options)
        for audience in aud:
            if isIdToken:
                if audience == self.options[Constants.CLIENT_ID]:
                    return True
            else:
                if self.__validateSufficientAudience(urlparse(audience), urlparse(self.options[Constants.AUDIENCE_SERVICE_URL]), resourceTenant):
                    return True
        return False

    def __validateSufficientAudience(self, audienceUrl, serviceUrl, resourceTenant):
        if serviceUrl.scheme != audienceUrl.scheme:
            return False

        host = serviceUrl.hostname
        crossTenant = False
        if Constants.CROSS_TENANT in self.options:
            crossTenant = self.options[Constants.CROSS_TENANT]
        if crossTenant:
            try:
                idx = host.index(".")
                host = resourceTenant + host[idx:]
            except:
                return False

        if audienceUrl.hostname != host:
            return False

        #if audienceUrl.port is not None:
        if audienceUrl.port is None:
            if audienceUrl.scheme == "https":
                audPortFromToken = 443
            else:
                audPortFromToken = 80
        else:
            audPortFromToken = audienceUrl.port

        if serviceUrl.port is None:
            if serviceUrl.scheme == "https":
                audPortFromServiceUrl = 443
            else:
                audPortFromServiceUrl = 80
        else:
            audPortFromServiceUrl = serviceUrl.port

        if audPortFromToken != audPortFromServiceUrl:
            return False

        if audienceUrl.path != "":
            if not serviceUrl.path.startswith(audienceUrl.path):
                return False

        return True

    def validateNecessaryAudience(self, token, necessary):
        for audience in necessary:
            if not self.__validateNecessaryAudience(token, audience):
                return False
        return True

    def __validateNecessaryAudience(self, token, audience):
        if Constants.AUDIENCE_SCOPE_ACCOUNT == audience:
            return self.__validateScopeAccount(token)
        elif audience.startswith(Constants.AUDIENCE_SCOPE_TAG):
            return self.__validateScopeTag(audience)
        else:
            return False

    def __validateScopeAccount(self, token):
        client_tenant = token[Constants.TOKEN_CLAIM_TENANT]
        tenant = Utils.getTenant(self.options)
        if tenant == client_tenant:
            return True
        else:
            return False

    def __validateScopeTag(self, audience):
        tokenTags = self.getTokenTags(audience)
        scopes = Utils.getFqs(self.options)
        for scope in scopes:
            resTags = self.getTagsForResource(scope)
            for key, value in resTags.items():
                if key in tokenTags:
                    return True
        return False

    def getTokenTags(self, audience):
        ret = {}
        i = audience.index("=")
        decoded = base64.b64decode(audience[i+1:])
        parsed = json.loads(decoded)
        if "tags" in parsed:
            tags = parsed["tags"]
            for tag in tags:
                ret[tag["key"] + ":" + tag["value"]] = ""
        return ret

    def getTagsForResource(self, scope):
        key = scope
        if self.fqsCache.contains(key):
            tags = self.fqsCache.get(key)
            if tags.getExpiry() > round(time.time()):
                return tags.getTags()
        ret = {}
        atm = AccessTokenManager(self.options)
        at = atm.getAccessToken()

        url = self.options[Constants.BASE_URL]
        url += Constants.GET_APP_INFO_PATH
        params = {}
        params["filter"] = Constants.FQS_FILTER % scope
        enc = urllib.parse.urlencode(params)
        url += "?" + enc

        headers = {}
        headers[Constants.HEADER_AUTHORIZATION] = Constants.AUTH_BEARER % at

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code != 200:
            self.logger.error("Unable to fetch App Info. Response Code from server %s", str(response.status_code))
            self.logger.error("Unable to fetch App Info. Response text server %s", response.text)
            raise IdcsException("Failed to obtain App Details", response)
        res = response.json()
        resources = res["Resources"]
        for resource in resources:
            if "tags" in resource:
                tags = resource["tags"]
                for tag in tags:
                    ret[tag["key"] + ":" + tag["value"]] = ""
        ttl = Constants.FQS_RESOURCE_CACHE_TTL_DEFAULT
        if Constants.FQS_RESOURCE_CACHE_TTL in self.options:
            ttl = self.options[Constants.FQS_RESOURCE_CACHE_TTL]
        self.fqsCache.put(key,Tags(ret, ttl))
        return ret


class KeyManager:
    """
    This class provide methods to fetch and manage JWK for tenants
    """

    def __init__(self, options, tenant = None):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = options
        if tenant is not None:
            self.tenant = tenant
        else:
            self.tenant =  Utils.getTenant(self.options)
        self.logger = Utils.getLogger(options)

    def fetchKey(self):
        """
        This method fetches JWK of the tenant for the BaseUrl given in options
        :return: JSON Web Key of the tenant
        """
        tenant = self.tenant
        if tenant.lower() in CacheManager.keys:
            self.logger.debug("Key found Cache.")
            jwk = CacheManager.keys[tenant.lower()]
            if jwk.getExpiry() > round(time.time()):
                self.logger.debug("Returning from cache.")
                return jwk.getJwk()
            else:
                self.logger.debug("JWK is expired.")

        self.logger.debug("JWK Not present in cache or expired. Going to fetch from server.")
        atm = AccessTokenManager(self.options)
        token = atm.getAccessToken()
        mdm = MetadataManager(self.options, tenant)
        md = mdm.getMetaData()
        url = md.getJwksUrl()
        self.logger.debug("Going to fetch JWK from %s", url)
        headers = {Constants.HEADER_AUTHORIZATION: Constants.AUTH_BEARER % token}
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            CacheManager.keys[tenant] = Jwk(res)
            self.logger.debug("JWK fetched successfully. Persisting in cache and returning.")
            return res
        self.logger.error("Unable to fetch JWK. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch JWK. Response text server %s", response.text)
        raise IdcsException("Failed to Fetch JWK", response)


class AuthenticationManager:
    """
    This class provide methods for the different OAUTH authentication flows to get Access Token
    """
    def __init__(self, options):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = Utils.validateOptions(options)
        self.logger = Utils.getLogger(options)
        self.cacheManager = CacheManager()
        self.tokenCache = self.cacheManager.getTokenCache()

    def verifyToken(self, token):
        """
        This method verifies idToken or accessToken given and parse it and return decoded token
        :param token: id_token or access_token
        :return: decoded token as JSON Object
        """
        if token is None or not token.strip():
            raise ValueError("token is empty")
        key = hash(token)
        verifiedJwt = self.tokenCache.get(key)
        if verifiedJwt is None:
            self.logger.info("token claims not found in cache")
            tv = TokenVerifier(self.options, self.cacheManager)
            verifiedJwt = tv.verifyJwtToken(token)
            if verifiedJwt is None :
                return None
            type = verifiedJwt[Constants.TOKEN_CLAIM_TOKEN_TYPE]
            isIdToken = False if "AT" == type else True
            level = self.options[Constants.TOKEN_VALIDATION_LEVEL] if Constants.TOKEN_VALIDATION_LEVEL in self.options else Constants.VALIDATION_LEVEL_FULL
            if Constants.VALIDATION_LEVEL_FULL == level:
                valid = tv.validateAudience(verifiedJwt, isIdToken)
                if not valid:
                    raise IdcsException("Failed to Verify Audience")

            ttl = Utils.getTTLFromClaim(verifiedJwt)
            if key is not None and ttl > 0:
                self.tokenCache.put(key, verifiedJwt, ttl)

        if verifiedJwt is not None:
            userAssert = UserAssert(self.options, self.cacheManager)
            userAssert.assertClaims(verifiedJwt)

        return verifiedJwt

    def verifyIdToken(self, id_token):
        """
        This method verifies idToken given and parse ite and return IdToken Object
        :param id_token: idToken of User
        :return: IdToken Class object containing claims present in idToken. Returns Null id fails to verify.
        """
        token = self.verifyToken(id_token)
        return IdToken(token)

    def verifyAccessToken(self, access_token):
        """
        This method verifies accessToken given and parse ite and return AccessToken Object
        :param access_token: access Token
        :return: Access Token Class object containing claims present in access token. Returns Null id fails to verify.
        """
        token = self.verifyToken(access_token)
        return AccessToken(token)

    def getAuthorizationCodeUrl(self, redirect_uri, scope=None, state=None, response_type=None, nonce=None):
        """
        This method returns the Authorization Code URL for the tenant for the BaseUrl present in options 
        :param redirect_uri: The redirect_uri where authorization code would be sent back
        :param scope: The scopes for which the authorization code is returned
        :param state: The state to be passed to OAUTH provider
        :param response_type The response type required from OAUTH Provider
        :param nonce The nonce is used for openId verification to prevent replay attacks. Use other method for non openid flow
        :return: A complete formed URL at which the browser should hit to get the authorization code 
        """
        if redirect_uri is None or not redirect_uri.strip():
            raise ValueError("redirect_uri is empty")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getAuthorizationUrl()
        self.logger.debug("Got Authorization Endpoint %s", url)
        params = {}
        params[Constants.PARAM_CLIENT_ID] = self.options[Constants.CLIENT_ID]
        if response_type is None:
            params[Constants.PARAM_RESPONSE_TYPE] = Constants.RESPONSE_TYPE_CODE
        else:
            params[Constants.PARAM_RESPONSE_TYPE] = response_type
        params[Constants.PARAM_REDIRECT_URI] = redirect_uri
        if scope is not None:
            params[Constants.PARAM_SCOPE] = scope
        if state is not None:
            params[Constants.PARAM_STATE] = state
        if nonce is not None:
            params[Constants.PARAM_NONCE] = nonce
        url += "?" + urllib.parse.urlencode(params)
        self.logger.debug("Returning Authorization code Url %s", url)
        return url

    def authorizationCode(self, code, nonce=None):
        """
        This methods fetched access token for the authorization code flow
        :param code: The authorization code sent by OAUTH provider
        :param nonce The nonce is used for openId verification to prevent replay attacks. Use other method for non openid flow
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        if code is None or not code.strip():
            raise ValueError("code is empty")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        self.logger.debug("Got Token Endpoint %s", url)
        auth = self.options[Constants.CLIENT_ID] + ":" + self.options[Constants.CLIENT_SECRET]
        encode = base64.b64encode(auth.encode(Constants.UTF8))
        basicAuth = Constants.AUTH_BASIC % encode.decode(Constants.UTF8)
        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED,
                   Constants.HEADER_AUTHORIZATION: basicAuth}
        params = {Constants.PARAM_GRANT_TYPE : Constants.GRANT_AUTHZ_CODE, Constants.PARAM_CODE : code}
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully from authorization code.")
            try:
                if Constants.ID_TOKEN in res:
                    #decoded = jwt.decode(res[Constants.ID_TOKEN], verify=False)
                    decoded = jwt.decode(res[Constants.ID_TOKEN],options={"verify_signature": False},algorithms=['RS256'] )
                    if(Constants.PARAM_NONCE in decoded):
                        if nonce is None or nonce == "":
                            err = "authorizationCode : Nonce should not be null."
                            self.logger.error(err)
                            raise IdcsException(err)
                        if nonce != decoded[Constants.PARAM_NONCE]:
                            err = "authorizationCode : Nonce didn't match."
                            self.logger.error(err)
                            raise IdcsException(err)
            except:
                raise IdcsException("Failed to Decode JWT Token")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def resourceOwner(self, username, password, scope=None):
        """
        This method fetches Access Token using resource owner OAUTH flow
        :param username: Login Id used to do login
        :param password: Password of the User
        :param scope: List of scopes for which access token is required
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        if username is None or not username.strip():
            raise ValueError("username is empty")
        if password is None or not password.strip():
            raise ValueError("password is empty")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        self.logger.debug("Got Token Endpoint %s", url)

        auth = self.options[Constants.CLIENT_ID] + ":" + self.options[Constants.CLIENT_SECRET]
        encode = base64.b64encode(auth.encode(Constants.UTF8))
        basicAuth = Constants.AUTH_BASIC % encode.decode(Constants.UTF8)

        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED,
                   Constants.HEADER_AUTHORIZATION: basicAuth}

        params = {Constants.PARAM_GRANT_TYPE : Constants.GRANT_PASSWORD, Constants.PARAM_USER_NAME : username, Constants.PARAM_PASSWORD : password}
        if scope is not None:
            params[Constants.PARAM_SCOPE] = scope

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully using resource owner credentials")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def refreshToken(self, refresh_token, scope=None):
        """
        This method fetches access token using the refresh token OAUTH flow
        :param refresh_token: The refresh token to fetch access token
        :param scope: List of scopes for which access token is required
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        if refresh_token is None or not refresh_token.strip():
            raise ValueError("refresh_token is empty")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        self.logger.debug("Got Token Endpoint %s", url)

        auth = self.options[Constants.CLIENT_ID] + ":" + self.options[Constants.CLIENT_SECRET]
        encode = base64.b64encode(auth.encode(Constants.UTF8))
        basicAuth = Constants.AUTH_BASIC % encode.decode(Constants.UTF8)

        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED,
                   Constants.HEADER_AUTHORIZATION: basicAuth}

        params = {Constants.PARAM_GRANT_TYPE : Constants.GRANT_REFRESH_TOKEN, Constants.PARAM_REFRESH_TOKEN : refresh_token}
        if scope is not None:
            params[Constants.PARAM_SCOPE] = scope

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully using refresh token")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def clientAssertion(self, user_assertion, client_assertion, scope=None):
        """
        This method fetches access token using the Client Assertion OAUTH flow
        :param user_assertion: User Assertion as JSON WEB Token
        :param client_assertion:  Client Assertion as JSON WEB Token
        :param scope: List of scopes for which access token is required
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if user_assertion is None or not user_assertion.strip():
            raise ValueError("user_assertion is empty")
        if client_assertion is None or not client_assertion.strip():
            raise ValueError("client_assertion is empty")

        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        self.logger.debug("Got Token Endpoint %s", url)

        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED}

        params = {Constants.PARAM_GRANT_TYPE : Constants.GRANT_ASSERTION,
                  Constants.PARAM_CLIENT_ID : self.options[Constants.CLIENT_ID],
                  Constants.PARAM_ASSERTION : user_assertion,
                  Constants.PARAM_CLIENT_ASSERTION : client_assertion,
                  Constants.PARAM_CLIENT_ASSERTION_TYPE : Constants.ASSERTION_JWT}
        if scope is not None:
            params[Constants.PARAM_SCOPE] = scope

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully using client assertion")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def userAssertion(self, user_assertion, scope=None):
        """
        This method fetches access token using the User Assertion OAUTH flow
        :param user_assertion: User Assertion as JSON WEB Token
        :param scope: List of scopes for which access token is required
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        if user_assertion is None or not user_assertion.strip():
            raise ValueError("user_assertion is empty")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        self.logger.debug("Got Token Endpoint %s", url)

        auth = self.options[Constants.CLIENT_ID] + ":" + self.options[Constants.CLIENT_SECRET]
        encode = base64.b64encode(auth.encode(Constants.UTF8))
        basicAuth = Constants.AUTH_BASIC % encode.decode(Constants.UTF8)

        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED,
                   Constants.HEADER_AUTHORIZATION: basicAuth}

        params = {Constants.PARAM_GRANT_TYPE : Constants.GRANT_ASSERTION,
                  Constants.PARAM_ASSERTION : user_assertion}
        if scope is not None:
            params[Constants.PARAM_SCOPE] = scope

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully using user assertion")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def clientCredentials(self, scope):
        """
        This method fetches Access Token using the Client Credentials OAUTH Flow
        :param scope: List of scopes for which access token is required
        :return: AuthenticationResult Object containing claims returned in Authentication
        """
        if Constants.CLIENT_ID not in self.options:
            raise ValueError("ClientId is missing in required options for fetching Access Token.")
        if Constants.CLIENT_SECRET not in self.options:
            raise ValueError("ClientSecret is missing in required options for fetching Access Token.")
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getTokenUrl()
        auth = self.options[Constants.CLIENT_ID] + ":" + self.options[Constants.CLIENT_SECRET]
        encode = base64.b64encode(auth.encode(Constants.UTF8))
        basicAuth = Constants.AUTH_BASIC % encode.decode(Constants.UTF8)
        headers = {Constants.HEADER_CONTENT : Constants.WWW_FORM_ENCODED,
                   Constants.HEADER_AUTHORIZATION: basicAuth}
        params = {Constants.PARAM_GRANT_TYPE: Constants.GRANT_CLIENT_CRED,
                  Constants.PARAM_SCOPE: scope}
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, data=params, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("Access Token fetched successfully using client credentials")
            return AuthenticationResult(res)
        self.logger.error("Unable to fetch Access Token. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch Access Token. Response text server %s", response.text)
        raise IdcsException("Failed to obtain access token", response)

    def generateAssertion(self, privateKey, headers, claims, alg=None):
        """
        This method produces a signed JWT from the given claims
        :param privateKey: RSA Private Key to sign the assertion
        :param headers: A dictionary of headers for Signed token. Claims kid or x5t are mandatory
        :param claims: A dictionary of claims for Signed token. Claims sub,exp,aud are mandatory
        :param alg: The algorithm used to sign. Default is RS256
        :return: Serialized Signed Json Web Token
        """
        if claims is None:
            raise ValueError("Claims is empty")
        if Constants.TOKEN_CLAIM_SUBJECT not in claims:
            raise ValueError("Subject claim not present")
        if Constants.TOKEN_CLAIM_EXPIRY not in claims:
            raise ValueError("Expiry claim not present")
        if Constants.TOKEN_CLAIM_AUDIENCE not in claims:
            raise ValueError("Audience claim not present")
        if Constants.TOKEN_CLAIM_ISSUE_AT not in claims:
            raise ValueError("Issue At claim not present")
        if Constants.TOKEN_CLAIM_ISSUER not in claims:
            raise ValueError("Issuer claim not present")

        if headers is None:
            raise ValueError("Headers is empty")
        if Constants.HEADER_CLAIM_KEY_ID not in headers:
            if Constants.HEADER_CLAIM_X5_THUMB not in headers:
                raise ValueError("No kid or x5t present in header")

        if alg is None:
            alg = "RS256"

        headers[Constants.HEADER_CLAIM_TYPE] = Constants.TOKEN_TYPE_JWT
        token = jwt.encode(claims, privateKey, headers=headers, algorithm=alg)
        return token.decode("utf-8")

    """
    def getLogoutUrl(self, postLogoutRedirectUri, idTokenHint, state=None):
        if idTokenHint is None or not idTokenHint.strip():
            raise ValueError("token is empty")

        key = hash(idTokenHint)
        self.cacheManager.getTokenCache().remove(key)

        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        params = {}
        if postLogoutRedirectUri is not None:
            params[Constants.PARAM_POST_LOGOUT_URI] = postLogoutRedirectUri
        if state is not None:
            params[Constants.PARAM_STATE] = state

        params[Constants.PARAM_ID_TOKEN_HINT] = idTokenHint

        logoutUrl = md.metadata[Constants.META_OPENID_CONFIGURATION][Constants.META_OPENID_CONFIGURATION_ENDSESSION_ENDPOINT]
        self.logger.debug("Got logoutUrl %s", logoutUrl)

        logoutUrl += "?" + urllib.parse.urlencode(params)
        self.logger.debug("Returning logoutUrl %s", logoutUrl)
        return logoutUrl
    """
    def getLogoutUrl(self, postLogoutRedirectUri=None, idTokenHint=None, state=None):
        """
        This method returns Logout URL for the tenant and clear the Token Cache
        :param postLogoutRedirectUri: The postLogoutRedirectUri where post logout would be sent back
        :param idTokenHint: The token used to inititate logout
        :param state: The state to be passed to OAUTH provider
        :return: A complete formed URL at which the browser should hit to logout else returns error
        """
        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        params = {}
        if idTokenHint is not None:
            key = hash(idTokenHint)
            self.cacheManager.getTokenCache().remove(key)
            params[Constants.PARAM_ID_TOKEN_HINT] = idTokenHint
            if postLogoutRedirectUri is not None:
                params[Constants.PARAM_POST_LOGOUT_URI] = postLogoutRedirectUri
            if state is not None:
                params[Constants.PARAM_STATE] = state


        logoutUrl = md.metadata[Constants.META_OPENID_CONFIGURATION][
            Constants.META_OPENID_CONFIGURATION_ENDSESSION_ENDPOINT]
        self.logger.debug("Got logoutUrl %s", logoutUrl)

        logoutUrl += "?" + urllib.parse.urlencode(params)
        self.logger.debug("Returning logoutUrl %s", logoutUrl)
        return logoutUrl






@deprecated
class UserManager:
    """
    This Class provides methods to fetch User Details
    """

    def __init__(self, options):
        """
        Default Constructor
        :param options: A Dictionary containing BaseUrl, ClientId, and ClientSecret
        """
        self.options = Utils.validateOptions(options)
        self.logger = Utils.getLogger(options)
        self.userCache = CacheManager().getUserCache()
        self.asserterCache = CacheManager().getAsserterCache()

    @deprecated
    def getUser(self, userId):
        """
        This method fetches the User details for the given user Id
        :param userId: the Id of user
        :return: A User Object containing User Detail attributes
        """
        if Constants.BASE_URL not in self.options:
            raise ValueError("BaseUrl is missing in required options for fetching User.")
        if userId is None or not userId.strip():
            raise ValueError("userId is empty")
        key = Utils.getTenant(self.options) + ":" + userId
        if self.userCache.contains(key):
            self.logger.debug("User Found in Cache. Returning from cache")
            return self.userCache.get(key)

        atm = AccessTokenManager(self.options)
        token = atm.getAccessToken()
        url = self.options[Constants.BASE_URL]
        url+= Constants.GET_USER_PATH % userId

        params = {Constants.PARAM_ATTRIBUTES : Constants.USER_ATTRIBUTES}
        url += "?" + urllib.parse.urlencode(params)

        self.logger.debug("Going to fetch user from %s", url)
        headers = {Constants.HEADER_AUTHORIZATION: Constants.AUTH_BEARER % token}
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("User Fetched Successfully")
            ret = User(res)
            self.userCache.put(key,ret)
            return ret
        self.logger.error("Unable to fetch User. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch User. Response text server %s", response.text)
        raise IdcsException("Failed to obtain User Details", response)

    @deprecated
    def getAuthenticatedUser(self, access_token):
        """
        This method fetches the authenticated user to which access token belongs
        :param access_token: Access token of User
        :return: A User Object containing User Detail attributes
        """
        if Constants.BASE_URL not in self.options:
            raise ValueError("BaseUrl is missing in required options for fetching User.")
        if access_token is None or not access_token.strip():
            raise ValueError("access_token is empty")

        am = AuthenticationManager(self.options)
        at = am.verifyAccessToken(access_token)

        key = Utils.getTenant(self.options) + ":" + at.getSubject()
        if self.userCache.contains(key):
            self.logger.debug("User Found in Cache. Returning from cache")
            return self.userCache.get(key)

        url = self.options[Constants.BASE_URL]
        url+= Constants.GET_ME_PATH
        params = {Constants.PARAM_ATTRIBUTES : Constants.USER_ATTRIBUTES + "," + Constants.CLAIM_USER_CUSTOM_EXTENSIONS}
        url += "?" + urllib.parse.urlencode(params)
        self.logger.debug("Going to fetch user from %s", url)

        headers = {Constants.HEADER_AUTHORIZATION: Constants.AUTH_BEARER % access_token}
        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.get(url, headers=headers, verify=verify)
        if response.status_code == 200 :
            res = response.json()
            self.logger.debug("User Fetched Successfully")
            ret = User(res)
            self.userCache.put(key,ret)
            return ret
        self.logger.error("Unable to fetch User. Response Code from server %s", str(response.status_code))
        self.logger.error("Unable to fetch User. Response text server %s", response.text)
        raise IdcsException("Failed to obtain User Details", response)

    @deprecated
    def getGroupMembership(self, userId):
        """
        Fetches the list of Groups to which this user is member of
        :param userId: User Id of the User
        :return: A list containing objects of Group
        """
        if Constants.BASE_URL not in self.options:
            raise ValueError("BaseUrl is missing in required options for fetching User.")
        if userId is None or not userId.strip():
            raise ValueError("userId is empty")

        key = Utils.getTenant(self.options) + ":" + userId
        res = None
        if self.userCache.contains(key):
            self.logger.debug("User Found in Cache. Returning from cache")
            user = self.userCache.get(key)
            res = user.getUser()
        else:
            atm = AccessTokenManager(self.options)
            token = atm.getAccessToken()

            url = self.options[Constants.BASE_URL]
            url+= Constants.GET_USER_PATH % userId

            params = {Constants.PARAM_ATTRIBUTES : Constants.USER_ATTRIBUTES}
            url += "?" + urllib.parse.urlencode(params)

            self.logger.debug("Going to fetch groups for user from %s", url)
            headers = {Constants.HEADER_AUTHORIZATION: Constants.AUTH_BEARER % token}
            response = None
            verify = True
            if Constants.IGNORE_SSL in self.options:
                verify = not bool(self.options[Constants.IGNORE_SSL])
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code == 200:
                res = response.json()
                self.userCache.put(key,res)
                self.logger.debug("Groups Fetched Successfully")
            self.logger.error("Unable to fetch User. Response Code from server %s", str(response.status_code))
            self.logger.error("Unable to fetch User. Response text server %s", response.text)
            raise IdcsException("Failed to obtain User Details", response)

        groups = []
        if Constants.CLAIM_GROUPS in res:
            for item in res[Constants.CLAIM_GROUPS]:
                groups.append(Group(item))
        return groups

    @deprecated
    def getAppRoles(self, userId):
        if Constants.BASE_URL not in self.options:
            raise ValueError("BaseUrl is missing in required options for fetching User.")
        if userId is None or not userId.strip():
            raise ValueError("userId is empty")

        key = Utils.getTenant(self.options) + ":" + userId
        res = None
        if self.userCache.contains(key):
            self.logger.debug("User Found in Cache. Returning from cache")
            user = self.userCache.get(key)
            res = user.getUser()
        else:
            atm = AccessTokenManager(self.options)
            token = atm.getAccessToken()
            url = self.options[Constants.BASE_URL]
            url+= Constants.GET_USER_PATH % userId

            params = {Constants.PARAM_ATTRIBUTES : Constants.USER_ATTRIBUTES}
            url += "?" + urllib.parse.urlencode(params)

            self.logger.debug("Going to fetch user from %s", url)
            headers = {Constants.HEADER_AUTHORIZATION: Constants.AUTH_BEARER % token}
            response = None
            verify = True
            if Constants.IGNORE_SSL in self.options:
                verify = not bool(self.options[Constants.IGNORE_SSL])
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code == 200 :
                res = response.json()
                self.userCache.put(key,User(res))
                self.logger.debug("User Fetched Successfully")
            self.logger.error("Unable to fetch User. Response Code from server %s", str(response.status_code))
            self.logger.error("Unable to fetch User. Response text server %s", response.text)
            raise IdcsException("Failed to obtain User Details", response)

        appRoles = []
        if Constants.CLAIM_USER_EXTENSIONS in res:
            ext = res[Constants.CLAIM_USER_EXTENSIONS]
            if Constants.CLAIM_APP_ROLES in ext:
                for item in ext[Constants.CLAIM_APP_ROLES]:
                    appRoles.append(AppRole(item))

        return appRoles

    @deprecated
    def assertClaims(self, token):
        """
        This method asserts the identity with App Roles and Group Memberships for a given token
        :param token: Access Token or Id Token
        :return: a JSON Object with asserted Attributes else throws IDCSException
        """
        am = AuthenticationManager(self.options)
        jwt = am.verifyToken(token)
        id = None
        tenant = None
        claim_user_id = self.options[Constants.USER_ID_TOK_CLAIM] if Constants.USER_ID_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_USER_ID
        if "AT" == jwt[Constants.TOKEN_CLAIM_TOKEN_TYPE] and claim_user_id not in jwt:
            id = jwt[self.options[Constants.CLIENT_ID_TOK_CLAIM] if Constants.CLIENT_ID_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_CLIENT_ID]
            tenant = jwt[self.options[Constants.CLIENT_TENANT_TOK_CLAIM] if Constants.CLIENT_TENANT_TOK_CLAIM in self.options else Constants.TOKEN_CLAIM_CLIENT_TENANT]
        else:
            id = jwt[claim_user_id]
            tenant = jwt[self.options[Constants.USER_TENANT_TOKEN_CLAIM] if Constants.USER_TENANT_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_USER_TENANT]

        if six.PY2:
            id = id.encode("utf-8")

        if "AT" == jwt[Constants.TOKEN_CLAIM_TOKEN_TYPE] and not id.endswith("_APPID"):
            return jwt

        if Constants.ONLY_USER_TOK_CLAIM_ENABLED in self.options and not self.options[Constants.ONLY_USER_TOK_CLAIM_ENABLED]:
            group_claim = self.options[Constants.GROUP_TOKEN_CLAIM] if Constants.GROUP_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_GROUPS
            appRole_claim = self.options[Constants.APP_ROLE_TOKEN_CLAIM] if Constants.APP_ROLE_TOKEN_CLAIM in self.options else Constants.TOKEN_CLAIM_APP_ROLES
            if group_claim in jwt or appRole_claim in jwt:
                return jwt

        key = tenant + ":" + id
        if self.asserterCache.contains(key):
            self.logger.debug("Claims Found in Cache. Returning from cache")
            claims = self.asserterCache.get(key)
            jwt.update(claims)
            return jwt

        mdm = MetadataManager(self.options)
        md = mdm.getMetaData()
        url = md.getAsserterUrl()

        atm = AccessTokenManager(self.options)
        at = atm.getAccessToken()

        headers = {}
        headers[Constants.HEADER_AUTHORIZATION] = Constants.AUTH_BEARER % at
        headers[Constants.HEADER_CONTENT] = Constants.APPLICATION_JSON

        body = {}
        if Constants.APP_NAME in self.options:
            body[Constants.IDCS_APPNAME_FILTER_ATTRIB] = self.options[Constants.APP_NAME]
        if not id.endswith("_APPID"):
            body[Constants.IDCS_MAPPING_ATTRIBUTE] = self.options[Constants.USER_ID_RES_ATTR] if Constants.USER_ID_RES_ATTR in self.options else Constants.MAPPING_ATTR_ID
        body[Constants.IDCS_MAPPING_ATTRIBUTE_VALUE] = id
        schemas = [Constants.IDCS_ASSERTER_SCHEMA]
        body[Constants.IDCS_SCHEMAS] = schemas
        body[Constants.IDCS_INCLUDE_MEMBERSHIPS] = True

        response = None
        verify = True
        if Constants.IGNORE_SSL in self.options:
            verify = not bool(self.options[Constants.IGNORE_SSL])
        response = requests.post(url, json=body, headers=headers, verify=verify)
        if response.status_code != 201 and response.status_code != 200:
            self.logger.error("Unable to Assert Claims. Response Code from server %s", str(response.status_code))
            self.logger.error("Unable to Assert. Response text server %s", response.text)
            raise IdcsException("Failed to Assert Claims", response)
        res = response.json()
        self.asserterCache.put(key, res)
        jwt.update(res)
        return jwt


class AuthenticationResult:
    """
    This class represents the Authentication Result and provide methods to get claims returned in authentication
    """

    def __init__(self, result):
        """
        Default Constructor
        :param result: Authentication Result JSON received from OAuth Provider
        """
        self.result = result

    def getAccessToken(self):
        """
        It returns access token from the Authentication Result
        :return: Access Token
        """
        return self.result[Constants.ACCESS_TOKEN]

    def getRefreshToken(self):
        """
        It returns refresh token from the Authentication Result
        :return: Refresh Token
        """
        return self.result[Constants.REFRESH_TOKEN]

    def getIdToken(self):
        """
        It returns id token from the Authentication Result
        :return: Id Token
        """
        return self.result[Constants.ID_TOKEN]

    def getClaim(self, claim):
        """
        It returns any claim from the Authentication Result
        :param claim: The claim required from Authentication Result
        :return: The claim from Authentication Result
        """
        return self.result[claim]

    def getResult(self):
        """
        It returns the Authentication Result as a JSON object
        :return: JSON Object for Authentication Result
        """
        return self.result


class Jwk:
    """
    This class represents the JWK
    """
    def __init__(self, jwk):
        """
        Default Constructor
        :param jwk: Tenants JWK as a JSON Object
        """
        self.jwk = jwk
        self.expiry = round(time.time()) + Constants.META_DATA_CACHE_TTL_DEFAULT

    def getExpiry(self):
        return self.expiry

    def getJwk(self):
        return self.jwk


class Metadata:
    """
    This class represents the Metadata of the tenant
    """

    def __init__(self, metadata):
        """
        Default Constructor
        :param metadata: Tenant's Metadata JSON Object
        """
        self.metadata = metadata
        self.expiry = round(time.time()) + Constants.META_DATA_CACHE_TTL_DEFAULT

    def getExpiry(self):
        return self.expiry

    def getAuthorizationUrl(self):
        """
        This method returns the Authorization URL
        :return: The Authorization URL of the tenant
        """
        return self.metadata[Constants.META_OPENID_CONFIGURATION][Constants.META_OPENID_CONFIGURATION_AUTHORIZATION_ENDPOINT]

    def getTokenUrl(self):
        """
        This method returns the Token URL
        :return: The Token URL of the tenant
        """
        return self.metadata[Constants.META_OPENID_CONFIGURATION][Constants.META_OPENID_CONFIGURATION_TOKEN_ENDPOINT]

    def getJwksUrl(self):
        """
        This methods returns the JWKs URL
        :return: The JWKs URL of the tenant
        """
        return self.metadata[Constants.META_OPENID_CONFIGURATION][Constants.META_JWKS_URI]

    def getAsserterUrl(self):
        """
        This method returns the Asserter Endpoint
        :return: The Asserter URL of the Tenant
        """
        return self.metadata[Constants.META_ACCESS_CONFIGURATION][Constants.META_ACCESS_CONFIGURATION_ASSERTER_ENDPOINT]

    def getMetadata(self):
        """
        This method returns the JSON object of the tenant's metadata
        :return: JSON Object of Metadata
        """
        return self.metadata

    def getTokenIssuer(self):
        """
        This method returns the Token Issuer URL
        :return: The Token Issuer URL of the tenant
        """
        return self.metadata[Constants.META_OPENID_CONFIGURATION][Constants.META_OPENID_CONFIGURATION_ISSUER]


class Tags:

    def __init__(self, tags, ttl):
        self.tags = tags
        self.expiry = round(time.time()) + ttl

    def getTags(self):
        return self.tags

    def getExpiry(self):
        return self.expiry


class IdToken:
    """
    This class represents the IdToken and provide methods to get claims
    """

    def __init__(self, idToken):
        """
        Default Constructor
        :param idToken: The id token of user
        """
        self.idToken = idToken
        self.groups = []
        self.appRoles = []
        if Constants.CLAIM_GROUPS in idToken:
            for item in idToken[Constants.CLAIM_GROUPS] :
                self.groups.append(Group(item))

        if Constants.CLAIM_APP_ROLES in idToken:
            for item in idToken[Constants.CLAIM_APP_ROLES]:
                self.appRoles.append(AppRole(item))

    def getAudience(self):
        """
        Returns the Audience of the Id Token
        :return: A list if multiple Audience or a string if single
        """
        return self.idToken[Constants.TOKEN_CLAIM_AUDIENCE]

    def getIssuer(self):
        """
        Returns the Issuer of the Id Token
        :return: Name of the Issuer
        """
        return self.idToken[Constants.TOKEN_CLAIM_ISSUER]

    def getUserName(self):
        """
        Returns the Subject Claim of the Id Token
        :return: Subject claim
        """
        return self.idToken[Constants.ID_TOKEN_CLAIM_USERNAME_DEFAULT]

    def getDisplayName(self):
        """
        Returns the Display Name of the User
        :return: Display Name
        """
        return self.idToken[Constants.ID_TOKEN_CLAIM_DISPLAYNAME_DEFAULT]

    def getUserId(self):
        """
        User Id of the User whom this Id token belongs
        :return: User Id of the User
        """
        return self.idToken[Constants.ID_TOKEN_CLAIM_USERID_DEFAULT]

    def getIdentityDomain(self):
        """
        The tenant name to which this user belongs
        :return: Tenant Name
        """
        return self.idToken[Constants.ID_TOKEN_CLAIM_TENANT_DEFAULT]

    def getClaim(self, claim):
        """
        Returns value of any custom claim
        :param claim: Claim whose value is required
        :return: the value of the claim
        """
        return self.idToken[claim]

    def getGroups(self):
        """
        Return the List of Group objects this user is member of
        :return: List of Group objects this user is member of
        """
        return self.groups

    def getAppRoles(self):
        """
        Return the list of AppRole objects this user belong
        :return: list of AppRole objects this user belong
        """
        return self.appRoles

    def getIdToken(self):
        """
        Returns the Id Token in JSON format
        :return: ID Token
        """
        return self.idToken


class AccessToken:
    """
    This class represents the Access Token and provide methods to get claims
    """

    def __init__(self, accessToken):
        """
        Default Constructor
        :param accessToken: access token as a JSON Object
        """
        self.token = accessToken
        self.groups = []
        self.appRoles = []
        if Constants.CLAIM_GROUPS in accessToken:
            for item in accessToken[Constants.CLAIM_GROUPS]:
                self.groups.append(Group(item))

        if Constants.CLAIM_APP_ROLES in accessToken:
            for item in accessToken[Constants.CLAIM_APP_ROLES]:
                self.appRoles.append(AppRole(item))

    def getAudience(self):
        """
        Returns the Audience of the Access Token
        :return: A list if multiple Audience or a string if single
        """
        return self.token[Constants.TOKEN_CLAIM_AUDIENCE]

    def getIssuer(self):
        """
        Returns the Issuer of the Access Token
        :return: Name of the Issuer
        """
        return self.token[Constants.TOKEN_CLAIM_ISSUER]

    def getScope(self):
        """
        Returns the list of scopes for this access token
        :return: Space seperated list of scopes
        """
        return self.token[Constants.TOKEN_CLAIM_SCOPE]

    def getTenant(self):
        """
        Returns the tenant of the access token
        :return: The tenant name
        """
        return self.token[Constants.TOKEN_CLAIM_TENANT]

    def getSubject(self):
        """
        Returns the Subject of the Access Token
        :return: Subject Name
        """
        return self.token[Constants.TOKEN_CLAIM_SUBJECT]

    def getClientAppRoles(self):
        """
        Returns a list of client app roles
        :return: A list of client App Roles
        """
        if Constants.TOKEN_CLAIM_CLIENT_APPROLES in self.token:
            return self.token[Constants.TOKEN_CLAIM_CLIENT_APPROLES]
        else:
            return None

    def getUserAppRoles(self):
        """
        Returns a list of User App Roles
        :return: A list of user App Roles
        """
        if Constants.TOKEN_CLAIM_USER_APPROLES in self.token:
            return self.token[Constants.TOKEN_CLAIM_USER_APPROLES]
        else:
            return None

    def getToken(self):
        """
        Returns the access token as JSON Object
        :return: Access Token as JSON Object
        """
        return self.token

    def getAppRoles(self):
        """
        Return the list of AppRole objects this user belong
        :return: list of AppRole objects this user belong
        """
        return self.appRoles

    def getIdToken(self):
        """
        Returns the Id Token in JSON format
        :return: ID Token
        """
        return self.idToken


class User:
    """
    This class represents the User and provide methods to access its properties
    """

    def __init__(self, user):
        """
        Default Constructor
        :param user: The JSON representation of User
        """
        self.user = user
        self.groups = []
        self.appRoles = []
        if Constants.CLAIM_GROUPS in user:
            for item in user[Constants.CLAIM_GROUPS] :
                self.groups.append(Group(item))

        if Constants.CLAIM_USER_EXTENSIONS in user:
            ext = user[Constants.CLAIM_USER_EXTENSIONS]
            if Constants.CLAIM_APP_ROLES in ext:
                for item in ext[Constants.CLAIM_APP_ROLES]:
                    self.appRoles.append(AppRole(item))

        self.customAttributes = user.get(Constants.CLAIM_USER_CUSTOM_EXTENSIONS, {})

    def getUserName(self):
        """
        Returns The subject name of the user
        :return: Subject Name
        """
        return self.user[Constants.CLAIM_USER_NAME]

    def getDisplayName(self):
        """
        Returns the Display Name of the User
        :return: Display Name
        """
        return self.user[Constants.CLAIM_DISPLAY_NAME]

    def getUserId(self):
        """
        User Id of the User whom this Id token belongs
        :return: User Id of the User
        """
        return self.user[Constants.CLAIM_ID]

    def isActive(self):
        """
        Returns the active status of the user
        :return: True or False depending upon its active state
        """
        return self.user[Constants.CLAIM_ACTIVE]

    def getClaim(self, claim):
        """
        Returns value of any custom claim
        :param claim: Claim whose value is required
        :return: the value of the claim
        """
        return self.user[claim]

    def getGroups(self):
        """
        Return the List of Group objects this user is member of
        :return: List of Group objects this user is member of
        """
        return self.groups

    def getAppRoles(self):
        """
        Return the list of AppRole objects this user belong
        :return: list of AppRole objects this user belong
        """
        return self.appRoles

    def getUser(self):
        """
        Returns the User Object in JSON format
        :return: JSON format for User Object
        """
        return self.user

    def getCustomAttribute(self, attributeName=""):
        """
        Returns the value of attribute name if specified.
        Otherwise returns all custom attributes
        Returns null dict object if no custom attributes are defined
        """
        if attributeName:
            if self.customAttributes.get(attributeName, {}):
                return {"customAttribute":{attributeName:self.customAttributes.get(attributeName, {})}}
            else: return {"customAttribute": {}}
        else: return {"customAttribute":self.customAttributes}


class Group:
    """
    This Class represents the Group and provide methods to access its attribute
    """
    def __init__(self, group):
        """
        Default Constructor
        :param group: The JSON object of Group
        """
        self.group = group

    def getDisplayName(self):
        """
        Returns the Display Name of the Group
        :return: Display Name
        """
        return self.group[Constants.CLAIM_GROUP_DISPLAY_NAME]

    def getGroupId(self):
        """
        Returns Group Id of the Group
        :return: Group Id of the Group
        """
        return self.user[Constants.CLAIM_GROUP_ID]

    def getGroupLocation(self):
        """
        Returns the location uri of the group
        :return: the location uri of the group
        """
        return self.group[Constants.CLAIM_GROUP_LOCATION]

    def getGroup(self):
        """
        Returns the Group Object in JSON format
        :return: JSON format for Group Object
        """
        return self.group


class AppRole:
    """
    This Class represents the App Role and provide methods to access its attribute
    """
    def __init__(self, appRole):
        """
        Default Constructor
        :param appRole: The JSON object of app role
        """
        self.appRole = appRole

    def getName(self):
        """
        Returns the display name of the App Role
        :return: the display name of the App Role
        """
        return self.appRole[Constants.CLAIM_APP_ROLE_DISPLAY]


    def getId(self):
        """
        Returns the id of the App Role
        :return: the id of the App Role
        """
        return self.appRole[Constants.CLAIM_APP_ROLE_VALUE]

    def getLocation(self):
        """
        Returns the location uri of the App Role
        :return: the location uri of the App Role
        """
        return self.appRole[Constants.CLAIM_APP_ROLE_LOCATION]

    def getAppId(self):
        """
        Returns the App Id of the App Role
        :return: the App Id of the App Role
        """
        return self.appRole[Constants.CLAIM_APP_ROLE_APPID]

    def getAppName(self):
        """
        Returns the App Name of the App Role
        :return: the App name of the App Role
        """
        return self.appRole[Constants.CLAIM_APP_ROLE_APPNAME]

    def getRole(self):
        """
        Returns the App Role Object in JSON format
        :return: JSON format for App Role Object
        """
        return self.appRole


class CacheManager:
    metadata = {}
    tokens = {}
    keys = {}
    def __init__(self):
        self.asserterCache = Cache(Constants.ASSERTER_CACHE)
        self.userCache = Cache(Constants.USER_CACHE)
        self.fqsCache = Cache(Constants.FQS_CACHE)
        self.tokenCache = Cache(Constants.TOKEN_CACHE)

    def getAsserterCache(self):
        return self.asserterCache

    def getUserCache(self):
        return self.userCache

    def getFqsCache(self):
        return self.fqsCache

    def getTokenCache(self):
        return self.tokenCache

class Cache:
    def __init__(self, type):
        size = Constants.CACHE_MAX_SIZE_DEFAULT
        ## convert ttl to seconds
        self.ttl = Constants.CACHE_TTL_DEFAULT / 1000
        if type == Constants.USER_CACHE:
            size = Constants.USER_CACHE_MAX_SIZE_DEFAULT
            self.ttl = Constants.USER_CACHE_TTL_DEFAULT / 1000
        elif type == Constants.FQS_CACHE:
            self.ttl = Constants.FQS_RESOURCE_CACHE_TTL_DEFAULT / 1000
        self.cache = LRUCache(size)


    def put(self, key, val, ttl=None):
        if ttl is None:
            self.cache.set(key, val, self.ttl)
        else:
            ## convert ttl to seconds
            ttl = ttl/1000
            self.cache.set(key, val, ttl)

    def get(self, key):
        return self.cache[key]

    def contains(self,key):
        if key in self.cache:
            return True
        else:
            return False

    def remove(self, key):
        try:
            self.cache.cache.pop(key)
        except KeyError:
            # Ignore exception if key not found.
            pass


class Utils:
    logger = None

    @staticmethod
    def validateOptions(options):
        ret = dict(options)
        env = {}
        if Constants.ORA_IDCS_BASE_URL in os.environ:
            env[Constants.BASE_URL] = os.environ[Constants.ORA_IDCS_BASE_URL]
        if Constants.ORA_IDCS_CLIENT_ID in os.environ:
            env[Constants.CLIENT_ID] = os.environ[Constants.ORA_IDCS_CLIENT_ID]
        if Constants.ORA_IDCS_CLIENT_SECRET in os.environ:
            env[Constants.CLIENT_SECRET] = os.environ[Constants.ORA_IDCS_CLIENT_SECRET]
        if Constants.ORA_IDCS_AUDIENCE_URL in os.environ:
            env[Constants.AUDIENCE_SERVICE_URL] = os.environ[Constants.ORA_IDCS_AUDIENCE_URL]
        if Constants.ORA_IDCS_ISSUER_URL in os.environ:
            env[Constants.TOKEN_ISSUER] = os.environ[Constants.ORA_IDCS_ISSUER_URL]
        if Constants.ORA_IDCS_CROSS_TENANT in os.environ:
            env[Constants.CROSS_TENANT] = os.environ[Constants.ORA_IDCS_CROSS_TENANT]
        if Constants.ORA_IDCS_RESOURCE_TENANCY in os.environ:
            env[Constants.RESOURCE_TENANCY] = os.environ[Constants.ORA_IDCS_RESOURCE_TENANCY]
        if Constants.ORA_IDCS_TOKEN_VALIDATION_LEVEL in os.environ:
            env[Constants.TOKEN_VALIDATION_LEVEL] = os.environ[Constants.ORA_IDCS_TOKEN_VALIDATION_LEVEL]
        if Constants.ORA_IDCS_FQS_RESOURCE in os.environ:
            env[Constants.FULLY_QUALIFIED_SCOPES] = os.environ[Constants.ORA_IDCS_FQS_RESOURCE]

        if len(env) >= 5:
            ret.update(env)

        # not a mandatory option hence moved after mendatory check
        if Constants.CROSS_TENANT not in ret:
            ret[Constants.CROSS_TENANT] = False
        return ret

    @staticmethod
    def getTenant(options):
        """
        It parses tenant value from BaseUrl and returns it.
        :param options:
        :return: tenant value from BaseUrl
        """
        if Constants.BASE_URL not in options:
            raise ValueError("BaseUrl is missing in required options for fetching Metadata.")
        parsed = urlparse(options[Constants.BASE_URL])
        host = parsed.hostname
        tenant = host.split('.', 1)
        return tenant[0]

    @staticmethod
    def getTTLFromClaim(tokenDecoded):
        ttl = -1
        if tokenDecoded is not None:
            now = round(time.time())
            if Constants.TOKEN_CLAIM_EXPIRY in tokenDecoded:
                exp = tokenDecoded[Constants.TOKEN_CLAIM_EXPIRY]
            else:
                exp = 0
            ttl = (exp * 1000) - now
        return ttl

    @staticmethod
    def getTenantNameFromClaim(tokenDecode, options):
        if "AT" == tokenDecode[Constants.TOKEN_CLAIM_TOKEN_TYPE]:
            tenant = tokenDecode[options[Constants.CLIENT_TENANT_TOK_CLAIM] if Constants.CLIENT_TENANT_TOK_CLAIM in options else Constants.TOKEN_CLAIM_CLIENT_TENANT]
        else:
            tenant = tokenDecode[options[Constants.USER_TENANT_TOKEN_CLAIM] if Constants.USER_TENANT_TOKEN_CLAIM in options else Constants.TOKEN_CLAIM_USER_TENANT]
        return tenant

    @staticmethod
    def getErrorMessage(response):
        """
        It returns the Error Message and status from Http Response
        :param response: Response returned from requests library
        :return: Error Message from response
        """
        msg = "Status:" + str(response.status_code)
        msg+= " Message:" + response.text
        return msg

    @staticmethod
    def getLogger(options):
        """
        Get logger object with logging level set as mentioned in options
        :param options:
        :return: Logger object from logging library
        """
        if Utils.logger is None:
            Utils.logger = logging.getLogger("IdcsClient")
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

            if Constants.LOG_LEVEL in options:
                Utils.logger.setLevel(options[Constants.LOG_LEVEL])
            else:
                Utils.logger.setLevel(logging.WARNING)

            if Constants.CONSOLE_LOG in options:
                if options[Constants.CONSOLE_LOG] is True:
                    ch = logging.StreamHandler()
                    ch.setLevel(logging.DEBUG)
                    ch.setFormatter(formatter)
                    Utils.logger.addHandler(ch)
        return Utils.logger

    @staticmethod
    def isEmpty(string):
        if string is None:
            return True
        string = string.strip()
        if(len(string)==0):
            return True
        return False

    @staticmethod
    def getFqs(options):
        ret = []
        if Constants.FULLY_QUALIFIED_SCOPES in options:
            fqs = options[Constants.FULLY_QUALIFIED_SCOPES]
            scopes = fqs.split(",")
            for scope in scopes:
                if scope is not None and scope.strip() != "":
                    ret.append(scope.strip())
        return ret

    @staticmethod
    def getTokenIssuerUrl(options):
        mdm = MetadataManager(options)
        md = mdm.getMetaData()
        issuer = None

        try:
            issuer = md.getTokenIssuer()
        except KeyError:
            Utils.getLogger(options).warning("Issuer Not Found in OpenID configuration")

        if issuer is None or not issuer.strip():
            issuer = options[Constants.TOKEN_ISSUER]

        return issuer


class IdcsException(Exception):
    """
    Exception raised when some Error occurs while making call to IDCS
    """
    def __init__(self, message, response=None):
        self.message = message
        if response is not None:
            self.status = response.status_code
            self.response = response.text
