from langchain.agents import create_agent

from .config import OCIConfig
from .genai_tools import (
    build_full_analysis_tool,
    build_intent_tool,
    build_sentiment_tool,
    build_summary_tool,
    build_topic_tool,
)
from .speech_tools import build_transcription_tool

_SYSTEM_PROMPT = (
    "You are a CX (customer experience) analysis assistant. "
    "You have access to tools that can transcribe audio, analyse "
    "sentiment, summarise conversations, extract customer intent, "
    "and classify topics. "
    "Use the most appropriate tool(s) to fulfil the user's request. "
    "When performing a full analysis on an already-transcribed "
    "conversation, prefer the analyze_conversation tool to minimise "
    "LLM calls. "
    "Always return structured JSON in your final answer."
)


def build_tool_registry(config: OCIConfig) -> list:
    return [
        build_transcription_tool(config),
        build_sentiment_tool(config),
        build_summary_tool(config),
        build_intent_tool(config),
        build_topic_tool(config),
        build_full_analysis_tool(config),
    ]


def build_cx_agent(config: OCIConfig):
    tools = build_tool_registry(config)

    return create_agent(
        model=config.CHAT_MODEL_ID,
        tools=tools,
        system_prompt=_SYSTEM_PROMPT,
    )