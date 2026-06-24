import backend.config as config
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage


def initialize_model(model_id):
    return ChatOCIGenAI(
        model_id=model_id,
        service_endpoint=config.ENDPOINT,
        compartment_id=config.COMPARTMENT_ID,
        provider=config.PROVIDER,
        auth_type=config.AUTH_TYPE,
        auth_profile=config.CONFIG_PROFILE,
        model_kwargs={"temperature": 0, "max_tokens": 2000},
    )


def call_model(user_query, model_id):
    model = initialize_model(model_id)
    response = model.invoke(
        [
            HumanMessage(content=user_query),
        ]
    )
    return response.content
