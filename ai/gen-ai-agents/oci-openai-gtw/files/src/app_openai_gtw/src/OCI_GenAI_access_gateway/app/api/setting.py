from typing import Literal
import os, sys, yaml
current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from oci.config import from_file
from oci.signer import Signer
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner,get_resource_principals_signer
from oci.retry import DEFAULT_RETRY_STRATEGY
from oci.retry import RetryStrategyBuilder

import config
from oci.circuit_breaker import DEFAULT_CIRCUIT_BREAKER_STRATEGY
PORT = os.environ.get("PORT", config.PORT)
RELOAD = os.environ.get("RELOAD", config.RELOAD)
DEBUG = os.environ.get("DEBUG", config.DEBUG)
DEFAULT_API_KEYS = os.environ.get("DEFAULT_API_KEYS", config.DEFAULT_API_KEYS)
API_ROUTE_PREFIX = os.environ.get("API_ROUTE_PREFIX", config.API_ROUTE_PREFIX)



exponential_backoff_retry_strategy = RetryStrategyBuilder(
    max_attempts=5,  # Initial call + 4 retries
    total_elapsed_time_seconds=600,  # Max retry duration
    retry_base_wait_time_seconds=1,  # Initial delay
    retry_max_wait_between_calls_seconds=60,  # Max delay
    should_retry_on=lambda response: response.status in [429, 500, 502, 503, 504]  # Retry on throttling/server errors
).get_retry_strategy()


CLIENT_KWARGS = {
    # "retry_strategy": DEFAULT_RETRY_STRATEGY,
    "retry_strategy": exponential_backoff_retry_strategy,
    "circuit_breaker_strategy": DEFAULT_CIRCUIT_BREAKER_STRATEGY,
    # "timeout": (10, 240),  # default timeout config for OCI Gen AI service
}

AUTH_TYPE = os.environ.get("AUTH_TYPE", config.AUTH_TYPE)
if AUTH_TYPE=="API_KEY":
    OCI_CONFIG_FILE = os.environ.get("OCI_CONFIG_FILE", config.OCI_CONFIG_FILE)
    OCI_CONFIG_FILE_KEY = os.environ.get("OCI_CONFIG_FILE_KEY", config.OCI_CONFIG_FILE_KEY)
    OCI_CONFIG = from_file(OCI_CONFIG_FILE, OCI_CONFIG_FILE_KEY)
    signer = Signer(
        tenancy=OCI_CONFIG['tenancy'],
        user=OCI_CONFIG['user'],
        fingerprint=OCI_CONFIG['fingerprint'],
        private_key_file_location=OCI_CONFIG['key_file'],
        pass_phrase=OCI_CONFIG['pass_phrase']
    )
elif AUTH_TYPE == 'INSTANCE_PRINCIPAL':
    OCI_CONFIG = {}
    signer = InstancePrincipalsSecurityTokenSigner()
elif AUTH_TYPE == 'RESOURCE_PRINCIPAL':
    OCI_CONFIG = {}
    signer = get_resource_principals_signer()
    
CLIENT_KWARGS.update({'config': OCI_CONFIG})
CLIENT_KWARGS.update({'signer': signer})
CLIENT_KWARGS.update({'region': config.REGION})

INFERENCE_ENDPOINT_TEMPLATE = "https://inference.generativeai.{region}.oci.oraclecloud.com/20231130"


# One of NONE|START|END to specify how the API will handle inputs longer than the maximum token length.
EMBED_TRUNCATE = os.environ.get("EMBED_TRUNCATE", "END")


OCI_REGION = os.environ.get("OCI_REGION", config.REGION)
OCI_COMPARTMENT = os.environ.get("OCI_COMPARTMENT", config.OCI_COMPARTMENT)

if OCI_REGION and OCI_COMPARTMENT:
    SUPPORTED_OCIGENAI_EMBEDDING_MODELS = {}
    SUPPORTED_OCIGENAI_CHAT_MODELS = {}
    SUPPORTED_OCIODSC_CHAT_MODELS = {}
else:
    def get_models_from_yaml(yaml_file):
        with open(yaml_file, 'r') as stream:
            models = yaml.safe_load(stream)
        model_settings = []
        for i in models:
            for k, v in i['models'].items():
                for m in v:
                    m["region"] = i['region']
                    m["compartment_id"] = i['compartment_id']
                    m["type"] = k
                    if "provider" in i:
                        m["provider"] = i["provider"]
                    model_settings.append(m)
        return model_settings


    def get_supported_models(
        model_settings: list[dict], 
        capability: Literal["embedding", "ondemand", "dedicated", "datascience"]
        ) -> dict:
        models = {}
        for model in model_settings:
            if model['type'] == capability:
                if "model_id" in model:
                    if "." in model["model_id"]:
                        model["provider"] = model["model_id"].split(".")[0]
                    else:
                        model["provider"] = "UNKNOWN"            
                models[model['name']] = model
        return models
    MODEL_FILE = "models.yaml"
    MODEL_SETTINGS = get_models_from_yaml(os.path.join(parent_dir, MODEL_FILE))

    SUPPORTED_OCIGENAI_EMBEDDING_MODELS = get_supported_models(MODEL_SETTINGS,"embedding")
    SUPPORTED_OCIGENAI_CHAT_MODELS = get_supported_models(MODEL_SETTINGS,"ondemand") | get_supported_models(MODEL_SETTINGS,"dedicated")
    SUPPORTED_OCIODSC_CHAT_MODELS = get_supported_models(MODEL_SETTINGS,"datascience")


# print(SUPPORTED_OCIGENAI_CHAT_MODELS)
TITLE = "OCI Generative AI Proxy APIs"
SUMMARY = "OpenAI-Compatible RESTful APIs for OCI Generative AI Service"
VERSION = "0.1.0"
DESCRIPTION = """
Use OpenAI-Compatible RESTful APIs for OCI Generative AI Service models and OCI Data Science AI quick actions models.

Please edit "models.yaml" to specify your models and their call endpoints.
"""

print(f"Server start variables: ")
print("-"*40)
print(f"OCI_REGION: {OCI_REGION}")
print(f"OCI_COMPARTMENT: {OCI_COMPARTMENT}")
print(f"AUTH_TYPE: {AUTH_TYPE}")
if AUTH_TYPE=="API_KEY":
  print(f"OCI_CONFIG_FILE: {OCI_CONFIG_FILE}")
  print(f"OCI_CONFIG_FILE_KEY: {OCI_CONFIG_FILE_KEY}")
print("-"*40)
print(f"PORT: {PORT}")
print(f"RELOAD: {RELOAD}")
print(f"DEBUG: {DEBUG}")
print(f"DEFAULT_API_KEYS: {DEFAULT_API_KEYS}")
print(f"API_ROUTE_PREFIX: {API_ROUTE_PREFIX}")
print("-"*40)