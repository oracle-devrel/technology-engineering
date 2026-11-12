import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from oci._vendor.requests import Request
from assistant.model import config_and_signer


class SigningTests(unittest.TestCase):
    def test_api_key_configuration_signs_real_sdk_request(self):
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        config={'tenancy':'ocid1.tenancy.test','user':'ocid1.user.test',
                'fingerprint':'aa:bb','region':'eu-frankfurt-1',
                'key_content':key.private_bytes(serialization.Encoding.PEM,
                    serialization.PrivateFormat.TraditionalOpenSSL,
                    serialization.NoEncryption()).decode()}
        with patch.dict('os.environ',{'OCI_AUTH_TYPE':'api_key'}),patch('assistant.model.oci.config.from_file',return_value=config):
            _,signer=config_and_signer()
        self.assertIsNotNone(signer)
        request=Request('GET','https://identity.eu-frankfurt-1.oci.oraclecloud.com/20160918/compartments/test').prepare()
        signer(request)
        self.assertTrue(request.headers['Authorization'].startswith('Signature '))
        self.assertIn('rsa-sha256',request.headers['Authorization'])
