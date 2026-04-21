import json

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from backend import prompts
from .config import OCIConfig
from .llm_factory import build_llm


# ── Internal chain builder ────────────────────────────────────────────────────

def _make_chain(config: OCIConfig, system_prompt: str, **llm_kwargs):
    llm = build_llm(config, **llm_kwargs)
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", "{input}")]
    )
    return prompt | llm | StrOutputParser()


def _safe_json(raw: str, fallback: dict) -> dict:
    try:
        # Strip accidental markdown fences the model may emit
        cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {**fallback, "_raw": raw}


# ── Tool factories ────────────────────────────────────────────────────────────

def build_sentiment_tool(config: OCIConfig):
    chain = _make_chain(
        config,
        system_prompt=prompts.SENTIMENT_SYSTEM,
        temperature=0.0,
        max_tokens=256,
    )

    @tool
    def analyze_sentiment(conversation_text: str) -> str:
        raw = chain.invoke({"input": conversation_text})
        result = _safe_json(raw, {"sentiment": "unknown", "confidence": 0.0, "explanation": ""})
        return json.dumps(result)

    return analyze_sentiment


def build_summary_tool(config: OCIConfig):
    chain = _make_chain(
        config,
        system_prompt=prompts.SUMMARY_SYSTEM,
        temperature=0.0,
        max_tokens=512,
    )

    @tool
    def summarize_conversation(conversation_text: str) -> str:
        summary = chain.invoke({"input": conversation_text}).strip()
        return json.dumps({"summary": summary})

    return summarize_conversation


def build_intent_tool(config: OCIConfig):
    chain = _make_chain(
        config,
        system_prompt=prompts.INTENT_SYSTEM,
        temperature=0.0,
        max_tokens=256,
    )

    @tool
    def extract_intent(conversation_text: str) -> str:
        raw = chain.invoke({"input": conversation_text})
        result = _safe_json(raw, {"intent": "unknown", "sub_intents": [], "confidence": 0.0})
        return json.dumps(result)

    return extract_intent


def build_topic_tool(config: OCIConfig, topics: list[str] | None = None):
    default_topics = prompts.TOPIC_DEFAULT_TOPICS
    topic_list = topics or default_topics
    topics_str = ", ".join(topic_list)

    chain = _make_chain(
        config,
        system_prompt=prompts.TOPIC_SYSTEM_TEMPLATE.format(topics=topics_str),
        temperature=0.0,
        max_tokens=128,
    )

    @tool
    def classify_topic(conversation_text: str) -> str:
        raw = chain.invoke({"input": conversation_text})
        result = _safe_json(raw, {"topic": "other", "confidence": 0.0})
        return json.dumps(result)

    return classify_topic


def build_full_analysis_tool(config: OCIConfig):
    chain = _make_chain(
        config,
        system_prompt=prompts.FULL_ANALYSIS_SYSTEM,
        temperature=0.0,
        max_tokens=1024,
    )

    @tool
    def analyze_conversation(conversation_text: str) -> str:
        raw = chain.invoke({"input": conversation_text})
        result = _safe_json(raw, {"error": "parse_failed", "_raw": raw})
        return json.dumps(result)

    return analyze_conversation