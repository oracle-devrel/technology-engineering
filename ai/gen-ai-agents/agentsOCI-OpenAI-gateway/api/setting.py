import os, sys, yaml
import oci

current_dir = os.path.dirname(os.path.realpath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from config import *

CLIENT_KWARGS = {
    "retry_strategy": oci.retry.DEFAULT_RETRY_STRATEGY,
    "timeout": (10, 240),  # default timeout config for OCI Gen AI service
}

if AUTH_TYPE == "API_KEY":
    OCI_CONFIG = oci.config.from_file(OCI_CONFIG_FILE, OCI_CONFIG_FILE_KEY)
    signer = oci.signer.Signer(
        tenancy=OCI_CONFIG['tenancy'],
        user=OCI_CONFIG['user'],
        fingerprint=OCI_CONFIG['fingerprint'],
        private_key_file_location=OCI_CONFIG['key_file'],
        pass_phrase=OCI_CONFIG['pass_phrase']
    )
    CLIENT_KWARGS.update({'config': OCI_CONFIG})
    CLIENT_KWARGS.update({'signer': signer})
elif AUTH_TYPE == 'INSTANCE_PRINCIPAL':
    OCI_CONFIG = {}
    signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
    CLIENT_KWARGS.update({'config': OCI_CONFIG})
    CLIENT_KWARGS.update({'signer': signer})


def parse_model_settings(yaml_file):
    with open(yaml_file, 'r') as stream:
        models = yaml.safe_load(stream)
    model_settings = []
    for i in models:
        for k, v in i['models'].items():
            for m in v:
                m["region"] = i['region']
                m["compartment_id"] = i['compartment_id']
                m["type"] = k
                model_settings.append(m)
    return model_settings


MODEL_SETTINGS = parse_model_settings(os.path.join(parent_dir, 'models.yaml'))

SUPPORTED_OCIGENAI_EMBEDDING_MODELS = {}
SUPPORTED_OCIGENAI_CHAT_MODELS = {}
DEFAULT_EMBEDDING_MODEL, DEFAULT_MODEL = None, None
SUPPORTED_OCIODSC_CHAT_MODELS = {}

for m in MODEL_SETTINGS:
    if m['type'] == "embedding":
        if DEFAULT_EMBEDDING_MODEL is None:
            DEFAULT_EMBEDDING_MODEL = m["name"]
        SUPPORTED_OCIGENAI_EMBEDDING_MODELS[m['name']] = m
    elif m['type'] == "ondemand":
        if DEFAULT_MODEL is None:
            DEFAULT_MODEL = m["name"]
        if m["model_id"].startswith("cohere"):
            m["provider"] = "cohere"
        elif m["model_id"].startswith("meta"):
            m["provider"] = "meta"
        SUPPORTED_OCIGENAI_CHAT_MODELS[m['name']] = m        
    elif m['type'] == "dedicated":
        m["provider"] = "dedicated"
        SUPPORTED_OCIGENAI_CHAT_MODELS[m['name']] = m
    elif m['type'] == "datascience":
        SUPPORTED_OCIODSC_CHAT_MODELS[m['name']] = m
