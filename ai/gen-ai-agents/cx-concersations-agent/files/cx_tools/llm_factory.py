from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI

from .config import OCIConfig

_KNOWN_PROVIDERS = {"cohere"}


def _infer_provider(model_id: str) -> str:
    prefix = model_id.split(".")[0].lower()
    return prefix if prefix in _KNOWN_PROVIDERS else "meta"


def build_llm(
    config: OCIConfig,
    model_id: str | None = None,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> ChatOCIGenAI:

    resolved_model = model_id or config.CHAT_MODEL_ID

    return ChatOCIGenAI(
        model_id=resolved_model,
        provider=_infer_provider(resolved_model),
        service_endpoint=config.ENDPOINT,
        compartment_id=config.COMPARTMENT_ID,
        auth_type="API_KEY",
        auth_profile=config.PROFILE_NAME,
        auth_file_location=config.CONFIG_FILE_PATH,
        model_kwargs={
            "temperature": temperature if temperature is not None else config.TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else config.MAX_TOKENS,
            "top_p": config.TOP_P,
            "top_k": config.TOP_K,
            "frequency_penalty": config.FREQUENCY_PENALTY,
            "presence_penalty": config.PRESENCE_PENALTY,
        },
    )