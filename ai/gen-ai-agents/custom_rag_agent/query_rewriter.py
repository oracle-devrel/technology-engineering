"""
File name: query_rewriter.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module implements the first step in the agent's workflow:
    query rewriting.

Usage:
    Import this module into other scripts to use its functions.
    Example:
        from query_rewriter import QueryRewriter

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

from langchain_core.runnables import Runnable
from langchain_core.messages import HumanMessage
from langchain.prompts import PromptTemplate

# integration with APM
from py_zipkin.zipkin import zipkin_span

from agent_state import State
from prompts import REFORMULATE_PROMPT_TEMPLATE
from oci_models import get_llm
from utils import get_console_logger
from config import DEBUG, AGENT_NAME

logger = get_console_logger()


class QueryRewriter(Runnable):
    """
    Takes the user request and the chat history and rewrite the user query
    in a standalone question that is used for the semantic search
    """

    def __init__(self):
        """
        Init
        """

    @zipkin_span(service_name=AGENT_NAME, span_name="query_rewriting")
    def invoke(self, input: State, config=None, **kwargs):
        """
        Rewrite the query

        Reformulate the question in a standalone question, using the chat_history
        """
        user_request = input["user_request"]
        error = None

        if len(input["chat_history"]) > 0:
            if DEBUG:
                logger.info("Reformulating the question...")

            try:
                llm = get_llm(temperature=0)

                _prompt_template = PromptTemplate(
                    input_variables=["user_request", "chat_history"],
                    template=REFORMULATE_PROMPT_TEMPLATE,
                )

                prompt = _prompt_template.format(
                    user_request=user_request, chat_history=input["chat_history"]
                )

                messages = [
                    HumanMessage(content=prompt),
                ]

                standalone_question = llm.invoke(messages).content

                if DEBUG:
                    logger.info("Standalone question: %s", standalone_question)
            except Exception as e:
                logger.error("Error in query_rewriting: %s", e)
                error = str(e)
        else:
            # no previous requests, don't reformulate
            standalone_question = user_request

        return {"standalone_question": standalone_question, "error": error}
