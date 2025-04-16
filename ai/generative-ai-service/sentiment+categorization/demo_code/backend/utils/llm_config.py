# import utils.config as config
# from utils import prompts as prompts

import backend.utils.config as config
from backend.utils import prompts as prompts


def get_prompt(model_name: str, prompt_type: str) -> str:
    if model_name not in PROMPT_SETS:
        raise ValueError(f"No prompts defined for model {model_name}")
    if prompt_type not in PROMPT_SETS[model_name]:
        raise ValueError(f"Unknown prompt type: {prompt_type}")
    return PROMPT_SETS[model_name][prompt_type]


MODEL_REGISTRY = {
    "cohere_oci": {
        "model_id": config.GENERATE_MODEL_COHERE,
        "service_endpoint": config.ENDPOINT,
        "compartment_id": config.COMPARTMENT_ID,
        "provider": config.PROVIDER_COHERE,
        "auth_type": config.AUTH_TYPE,
        "auth_profile": config.CONFIG_PROFILE,
        "model_kwargs": {"temperature": 0, "max_tokens": 4000},
        "embedding_model": config.EMBEDDING_MODEL_COHERE,
    },
    "meta_oci": {
        "model_id": config.GENERATE_MODEL_LLAMA_33,
        "service_endpoint": config.ENDPOINT,
        "compartment_id": config.COMPARTMENT_ID,
        "provider": config.PROVIDER_LLAMA,
        "auth_type": config.AUTH_TYPE,
        "auth_profile": config.CONFIG_PROFILE,
        "model_kwargs": {"temperature": 0, "max_tokens": 2000},
    },
}

PROMPT_SETS = {
    "cohere_oci": {
        "SUMMARIZATION": prompts.SUMMARIZATION,
        "CATEGORIZATION_SYSTEM": prompts.CATEGORIZATION_SYSTEM,
        "CATEGORIZATION_USER": prompts.CATEGORIZATION_USER,
        "REPORT_GEN": prompts.REPORT_GEN,
    },
    "meta_oci": {
        "SUMMARIZATION_LLAMA": prompts.SUMMARIZATION_LLAMA,
        "CATEGORIZATION_LLAMA": prompts.CATEGORIZATION_LLAMA,
        "REPORT_GEN_LLAMA": prompts.REPORT_GEN_LLAMA,
    },
}
