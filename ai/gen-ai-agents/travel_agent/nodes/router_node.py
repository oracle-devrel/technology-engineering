# router_node.py
# -*- coding: utf-8 -*-
"""
RouterNode

This module defines the RouterNode class, which acts as an intent classifier in the LangGraph-based
travel assistant. It uses an LLM to determine whether the user's input is a travel booking request
or a general information query.

Author: L. Saetta
Date: 20/05/2025
"""
from langchain_core.runnables import Runnable
from langchain_core.output_parsers import StrOutputParser
from base_node import BaseNode
from model_factory import get_chat_model
from prompt_template import router_prompt
from config import MODEL_ID, SERVICE_ENDPOINT, DEBUG


class RouterNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for classifying the user's intent.

    This node invokes an LLM with a predefined prompt to determine whether the user's
    request is for booking a trip or asking for general travel information.

    It updates the state with a new key: 'intent', which can be either 'booking' or 'info'.

    Attributes:
        prompt (PromptTemplate): The classification prompt template.
        llm (Runnable): The language model used for intent classification.
        chain (Runnable): Composed chain of prompt → model → output parser.
    """

    def __init__(self):
        """
        Initialize the RouterNode with a classification prompt and a configured chat model.

        The prompt is used to elicit one of two intents: 'booking' or 'info'.
        The LLM is invoked with a temperature of 0.0 for deterministic intent classification.
        """
        super().__init__("router")

        self.prompt = router_prompt
        self.llm = get_chat_model(
            model_id=MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            temperature=0.0,
            max_tokens=2048,
        )
        self.chain: Runnable = self.prompt | self.llm | StrOutputParser()

    def invoke(self, state, config=None, **kwargs):
        """
        Classify the user's intent using the LLM and update the state accordingly.

        Args:
            state (dict): The current LangGraph state, which must include a 'user_input' key.
            config (optional): Reserved for compatibility; not used.

        Returns:
            dict: Updated state with a new key 'intent' set to either 'booking' or 'info'.
        """
        user_input = state["user_input"]
        intent = self.chain.invoke({"user_input": user_input}).strip().lower()

        self.log_info(f"Router classified intent as: {intent}")

        state["intent"] = intent
        return state
