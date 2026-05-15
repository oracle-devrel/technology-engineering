import logging
import time
import uuid

import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import (
    ChatDetails,
    GenericChatRequest,
    Message,
    OnDemandServingMode,
    TextContent,
)
from oci.retry import RetryStrategyBuilder

# ---------------------------------------------------------
# Config
# ---------------------------------------------------------
compartment_id = "ocid1.compartment.oc1..XXXXXXXXXXXXXXXXXXXXX" 
endpoint = "https://inference.generativeai.XXXXXXXXXXXXXXXXXXX"

# ---------------------------------------------------------
# Logging setup
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# OCI config + client init (with timeouts)
# ---------------------------------------------------------
CONFIG_PROFILE = "DEFAULT"
config = oci.config.from_file("~/.oci/config", CONFIG_PROFILE)

# You can also set a client-level retry_strategy here if you prefer
client = GenerativeAiInferenceClient(
    config,
    service_endpoint=endpoint,
    timeout=(3, 30),
)

# ---------------------------------------------------------
# Retry strategy (operation-level)
# ---------------------------------------------------------
retry_strategy = (
    RetryStrategyBuilder(
        max_attempts_check=True,
        max_attempts=3,
        retry_base_sleep_time_seconds=1,
        retry_exponential_growth_factor=2,
    )
    .add_service_error_check()
    .get_retry_strategy()
)

# ---------------------------------------------------------
# Model routing & fallback
# ---------------------------------------------------------
FAST_MODEL = "ocid1.generativeaimodel.oc1....fast" 
ROBUST_MODEL = "ocid1.generativeaimodel.oc1....large"

def select_model_id(prompt: str):
    return FAST_MODEL if len(prompt) < 200 else ROBUST_MODEL


# ---------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------
CIRCUIT_OPEN = False
CIRCUIT_OPEN_UNTIL = 0
CIRCUIT_COOLDOWN = 20  # seconds


def circuit_allows():
    global CIRCUIT_OPEN, CIRCUIT_OPEN_UNTIL
    now = time.time()
    if CIRCUIT_OPEN and now < CIRCUIT_OPEN_UNTIL:
        return False
    if CIRCUIT_OPEN and now >= CIRCUIT_OPEN_UNTIL:
        CIRCUIT_OPEN = False
    return True


def trip_circuit():
    global CIRCUIT_OPEN, CIRCUIT_OPEN_UNTIL
    CIRCUIT_OPEN = True
    CIRCUIT_OPEN_UNTIL = time.time() + CIRCUIT_COOLDOWN
    logger.error("Circuit breaker OPEN — pausing requests.")


# ---------------------------------------------------------
# Helper: normalize role and extract assistant text from ChatResult
# ---------------------------------------------------------
def _normalize_role(role: str) -> str:
    r = (role or "user").lower()
    if r == "system":
        return Message.ROLE_SYSTEM
    if r == "assistant":
        return Message.ROLE_ASSISTANT
    if r == "developer":
        return Message.ROLE_DEVELOPER
    # default
    return Message.ROLE_USER


def _extract_text_from_response(resp):
    """
    resp: Response[ChatResult]
    returns: concatenated assistant text (str) or "".
    """
    chat_result = resp.data  # ChatResult
    chat_response = chat_result.chat_response  # GenericChatResponse
    if not chat_response or not chat_response.choices:
        return ""

    first_choice = chat_response.choices[0]  # ChatChoice
    assistant_msg = first_choice.message  # Message
    contents = assistant_msg.content or []

    pieces = []
    for c in contents:
        # For generic format, each content 'c' usually has a 'text' attribute (string)
        text = getattr(c, "text", None)
        if isinstance(text, str):
            pieces.append(text)

    return "".join(pieces)


# ---------------------------------------------------------
# Chat-call handler
# ---------------------------------------------------------
def call_genai_chat(messages):
    """
    messages: list of dicts:
        { "role": "system"|"user"|"assistant", "content": str }
    returns: assistant response content (str)
    """
    if not circuit_allows():
        raise RuntimeError("Circuit breaker is open — service unavailable.")

    last_user_text = messages[-1].get("content", "") if messages else ""
    model_id = select_model_id(last_user_text)

    # Build the list of Message objects
    oci_messages = [
        Message(
            role=_normalize_role(msg.get("role", "user")),
            content=[TextContent(text=msg.get("content", ""))],
        )
        for msg in messages
    ]

    # Build the chat request (you can tune params here)
    chat_request = GenericChatRequest(
        messages=oci_messages,
        max_tokens=512,
        temperature=0.3,
    )

    # Wrap it all in ChatDetails
    chat_details = ChatDetails(
        compartment_id=compartment_id,
        serving_mode=OnDemandServingMode(model_id=model_id),
        chat_request=chat_request,
    )

    retry_token = str(uuid.uuid4())

    try:
        logger.info(f"Sending chat request (model={model_id})…")
        resp = client.chat(
            chat_details=chat_details,
            opc_retry_token=retry_token,
            retry_strategy=retry_strategy,
        )
        text = _extract_text_from_response(resp)
        logger.info("Response OK")
        return text

    except Exception as e:
        logger.error(f"Chat failed for model {model_id}: {e}")

        # Fallback to ROBUST model if we weren't already using it
        if model_id != ROBUST_MODEL:
            logger.warning("Retrying with fallback model…")
            try:
                chat_details.serving_mode.model_id = ROBUST_MODEL
                resp = client.chat(
                    chat_details=chat_details,
                    opc_retry_token=retry_token,
                    retry_strategy=retry_strategy,
                )
                text = _extract_text_from_response(resp)
                logger.info("Fallback success")
                return text
            except Exception as e2:
                trip_circuit()
                raise RuntimeError(f"Fallback model failed: {e2}") from e2

        trip_circuit()
        raise RuntimeError(f"Request failed after fallback: {e}") from e


# ---------------------------------------------------------
# Example usage
# ---------------------------------------------------------
if __name__ == "__main__":
    history = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "What are best practices to prevent timeouts when using OCI Generative AI?",
        },
    ]
    try:
        response = call_genai_chat(history)
        print("\nAssistant:", response)
    except Exception as err:
        print("Error:", err)
