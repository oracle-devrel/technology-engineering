# answer_info_node.py
# -*- coding: utf-8 -*-
"""
AnswerInfoNode

This module defines the AnswerInfoNode class, which is responsible for handling
general travel information queries within the LangGraph-based travel assistant.

When a user request is classified as an "info" intent by the router node,
this node generates a markdown-formatted response using a language model.

Author: L. Saetta
Date: 20/05/2025

"""
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from base_node import BaseNode
from model_factory import get_chat_model
from prompt_template import answer_prompt
from config import MODEL_ID, SERVICE_ENDPOINT, MAX_TOKENS, DEBUG


class AnswerInfoNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for handling general travel information queries.

    This node is used when the user's intent is classified as an information request
    (rather than a booking).
    It uses a language model to generate a helpful, markdown-formatted response
    based on the user's input.

    Attributes:
        prompt (PromptTemplate): The prompt template for generating the informational response.
        llm (Runnable): The configured language model used for generation.
        chain (Runnable): Composed chain of prompt → model → output parser.
    """

    def __init__(self):
        """
        Initialize the AnswerInfoNode with a pre-defined prompt and LLM configuration.

        The chain is constructed from:
        - `answer_prompt` (PromptTemplate)
        - A chat model initialized via `get_chat_model`
        - A `StrOutputParser` for plain string output
        """
        super().__init__("answer_info")

        self.prompt = answer_prompt
        self.llm = get_chat_model(
            model_id=MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            temperature=0.5,
            max_tokens=MAX_TOKENS,
        )
        self.chain: Runnable = self.prompt | self.llm | StrOutputParser()

    def invoke(self, state, config=None, **kwargs):
        """
        Generate a general travel information response from the user's question.

        Args:
            state (dict): The current LangGraph state, which must include a 'user_input' key.
            config (optional): Reserved for compatibility; not used.

        Returns:
            dict: Updated state with the 'final_plan' field set to the LLM-generated response.
        """
        response = self.chain.invoke({"user_input": state["user_input"]}).strip()

        if DEBUG:
            self.log_info("Generated informational response.")

        state["final_plan"] = response
        return state
