"""
Single source of truth for LLM construction.

Replaces the 3-layer stack (OCIModelHandler -> LocalLLM -> llm_client)
with a single factory that returns an OCIChat wrapper around ChatOCIGenAI.

Usage:
    from llm_factory import create_llm

    llm = create_llm("grok-3")        # cached singleton
    text = llm("What is 2+2?")        # backward-compat __call__
    msg  = llm.invoke([HumanMessage(content="hi")])  # LangChain style
    structured = llm.with_structured_output(MySchema)  # Pydantic parsing
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model registry -- single place for all model configs
# ---------------------------------------------------------------------------

MODEL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "grok-3": {
        "model_id_env": ["OCI_GROK_3_MODEL_ID", "GROK_MODEL_ID"],
        "provider": "generic",
        "region": "us-chicago-1",
        "max_output_tokens": 8000,
        "model_kwargs": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    "grok-3-fast": {
        "model_id_env": ["OCI_GROK_3_FAST_MODEL_ID", "GROK_MODEL_ID"],
        "provider": "generic",
        "region": "us-chicago-1",
        "max_output_tokens": 4000,
        "model_kwargs": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    "grok-4": {
        "model_id_env": ["OCI_GROK_4_MODEL_ID"],
        "provider": "generic",
        "region": "us-chicago-1",
        "max_output_tokens": 8000,
        "model_kwargs": {
            "temperature": 1,
            "top_p": 1,
        },
    },
    "gemini-2.5-pro": {
        "model_id_env": ["OCI_GEMINI_2_5_PRO_MODEL_ID"],
        "provider": "generic",
        "region": "us-chicago-1",
        "max_output_tokens": 8000,
        "model_kwargs": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    "gpt-5-2": {
        "model_id_env": ["OCI_GPT_5_2_MODEL_ID"],
        "provider": "generic",
        "region": "us-chicago-1",
        "max_output_tokens": 8000,
        "model_kwargs": {
            "temperature": 0.7,
            "top_p": 0.9,
        },
    },
    "llama3.3": {
        "model_id_env": ["OCI_LLAMA_3_3_MODEL_ID"],
        "provider": "meta",
        "region": "us-chicago-1",
        "max_output_tokens": 4000,
        "model_kwargs": {
            "temperature": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "top_p": 0.75,
        },
    },
    "cohere-command-a": {
        "model_id_env": ["OCI_COHERE_COMMAND_A_MODEL_ID"],
        "provider": "cohere",
        "region": "us-chicago-1",
        "max_output_tokens": 4000,
        "model_kwargs": {
            "temperature": 1,
            "frequency_penalty": 0,
            "top_p": 0.75,
            "top_k": 0,
        },
    },
    "dac-cluster": {
        "model_id_env": [],
        "endpoint_id": "ocid1.generativeaiendpoint.oc1.eu-frankfurt-1.amaaaaaa2xxap7yaj6ki7iooezw6yrkj5lj6l2y43xekiekg2jxu4li2tnna",
        "provider": "generic",
        "region": "eu-frankfurt-1",
        "compartment_env": "COMPARTMENT_ID_DAC",
        "max_output_tokens": 600,
        "model_kwargs": {
            "temperature": 1,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "top_p": 0.75,
        },
    },
}


# ---------------------------------------------------------------------------
# Singleton cache
# ---------------------------------------------------------------------------

_cache: Dict[str, "OCIChat"] = {}
_cache_lock = threading.Lock()


# ---------------------------------------------------------------------------
# OCIChat -- backward-compatible wrapper around ChatOCIGenAI
# ---------------------------------------------------------------------------

class OCIChat:
    """
    Thin wrapper that provides backward-compatible interfaces on top of
    ChatOCIGenAI.

    - ``__call__(prompt) -> str`` for the ``llm(prompt)`` pattern
    - ``.invoke(messages) -> AIMessage`` for agents
    - ``.with_structured_output(schema)`` proxy to ChatOCIGenAI
    - ``.chat`` property for direct access to the underlying model
    """

    def __init__(self, chat_model: Any, model_name: str = "unknown"):
        self._chat = chat_model
        self.model_name = model_name
        self.model_config = MODEL_REGISTRY.get(model_name, {})

    @property
    def chat(self) -> Any:
        return self._chat

    # -- backward compat: llm(prompt) -> str --
    def __call__(self, prompt: str, **kwargs) -> str:
        msg = self._chat.invoke([HumanMessage(content=prompt)])
        return (msg.content or "").strip()

    # -- LangChain style: llm.invoke([msg]) -> AIMessage --
    def invoke(self, messages: Union[List[Any], Any], **kwargs) -> AIMessage:
        if not isinstance(messages, list):
            messages = [messages]

        # Accept both LangChain BaseMessage and legacy objects with .content
        lc_messages: List[BaseMessage] = []
        for m in messages:
            if isinstance(m, BaseMessage):
                lc_messages.append(m)
            elif hasattr(m, "content"):
                lc_messages.append(HumanMessage(content=m.content))
            else:
                lc_messages.append(HumanMessage(content=str(m)))

        return self._chat.invoke(lc_messages, **kwargs)

    # -- structured output proxy --
    def with_structured_output(self, schema, **kwargs):
        return self._chat.with_structured_output(schema, **kwargs)

    def __repr__(self) -> str:
        return f"OCIChat(model={self.model_name!r})"


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_available_models() -> List[str]:
    """Return list of model names that have their env vars configured."""
    available = []
    for name, cfg in MODEL_REGISTRY.items():
        if cfg.get("endpoint_id"):
            # Dedicated cluster -- needs compartment env
            comp_env = cfg.get("compartment_env", "COMPARTMENT_ID_DAC")
            if os.getenv(comp_env):
                available.append(name)
        else:
            env_vars = cfg.get("model_id_env", [])
            if any(os.getenv(ev) for ev in env_vars):
                available.append(name)
    return available or ["grok-3"]


def create_llm(model_name: str = "grok-3", *, singleton: bool = True) -> OCIChat:
    """
    Create (or retrieve cached) OCIChat instance for the given model.

    Args:
        model_name: Key into MODEL_REGISTRY.
        singleton: If True, return a cached instance for repeat calls.

    Returns:
        OCIChat wrapping ChatOCIGenAI.
    """
    if singleton:
        with _cache_lock:
            if model_name in _cache:
                return _cache[model_name]

    if model_name not in MODEL_REGISTRY:
        raise ValueError(
            f"Unknown model {model_name!r}. "
            f"Available: {', '.join(MODEL_REGISTRY.keys())}"
        )

    cfg = MODEL_REGISTRY[model_name]

    # Resolve model_id
    model_id: Optional[str] = None
    endpoint_id: Optional[str] = cfg.get("endpoint_id")

    if endpoint_id:
        model_id = endpoint_id
    else:
        for env_var in cfg.get("model_id_env", []):
            model_id = os.getenv(env_var)
            if model_id:
                break
        if not model_id:
            raise ValueError(
                f"No model ID configured for {model_name!r}. "
                f"Set one of: {cfg.get('model_id_env', [])}"
            )

    # Resolve compartment_id
    comp_env = cfg.get("compartment_env")
    if comp_env:
        compartment_id = os.getenv(comp_env)
    else:
        compartment_id = os.getenv("OCI_COMPARTMENT_ID") or os.getenv("COMPARTMENT_ID")
    if not compartment_id:
        raise ValueError("Compartment ID not found. Set OCI_COMPARTMENT_ID in .env.")

    # Build service_endpoint
    region = cfg.get("region", "us-chicago-1")
    service_endpoint = f"https://inference.generativeai.{region}.oci.oraclecloud.com"

    # Build model_kwargs with max_tokens
    model_kwargs = dict(cfg.get("model_kwargs", {}))
    model_kwargs["max_tokens"] = cfg.get("max_output_tokens", 4000)

    # Construct ChatOCIGenAI (langchain-oci supports generic provider)
    from langchain_oci import ChatOCIGenAI

    is_dedicated = bool(endpoint_id)

    chat = ChatOCIGenAI(
        model_id=model_id,
        provider=cfg["provider"],
        service_endpoint=service_endpoint,
        compartment_id=compartment_id,
        is_stream=is_dedicated,
        model_kwargs=model_kwargs,
        auth_type="API_KEY",
        auth_profile="DEFAULT",
    )

    wrapped = OCIChat(chat, model_name=model_name)
    logger.info("Created LLM: %s (provider=%s, region=%s)", model_name, cfg["provider"], region)

    if singleton:
        with _cache_lock:
            _cache[model_name] = wrapped

    return wrapped
