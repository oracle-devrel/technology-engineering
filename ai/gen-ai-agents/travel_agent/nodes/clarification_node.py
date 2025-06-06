# clarification_node.py
# -*- coding: utf-8 -*-
"""
ClarificationNode

This module defines the ClarificationNode class, which is responsible for checking whether
the user's input is missing required travel information fields. If any fields are missing,
the node uses an LLM to generate a user-friendly clarification prompt.

Author: L. Saetta
Date: 20/05/2025

"""
import time
from base_node import BaseNode
from model_factory import get_chat_model
from translations import TRANSLATIONS
from config import MODEL_ID, SERVICE_ENDPOINT, REQUIRED_FIELDS, MAX_TOKENS, SLEEP_TIME


class ClarificationNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for identifying missing information
    in the user's travel request and generating a clarification prompt if necessary.

    This node checks for any fields listed in `REQUIRED_FIELDS` that are missing from the state.
    If any are missing, it uses an LLM to generate a natural-language follow-up question
    and sets flags in the state to trigger a clarification cycle.

    Attributes:
        llm (Runnable): The language model used to generate the clarification prompt.
    """

    def __init__(self):
        """
        Initialize the ClarificationNode with a configured chat model.

        The LLM is used to rephrase missing-field prompts into natural user questions.
        """
        super().__init__("ClarificationNode")

        self.llm = get_chat_model(
            model_id=MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            temperature=0.2,
            max_tokens=MAX_TOKENS,
        )

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Check for missing required fields and, if needed, generate a clarification prompt.

        Args:
            state (dict): The current shared workflow state containing user input and parsed fields.
            config (optional): Reserved for LangGraph compatibility; not used here.

        Returns:
            dict: Updated state with:
                - 'clarification_needed' (bool): True if any required field is missing.
                - 'clarification_prompt' (str): A user-friendly follow-up question
                   generated by the LLM (if needed).
        """
        missing = [field for field in REQUIRED_FIELDS if not state.get(field)]

        language = config.get("configurable", {}).get("language", "EN")
        # get the relevant translations
        t = TRANSLATIONS[language]

        if missing:
            self.log_info(f"Missing fields: {missing}")

            state["clarification_needed"] = True

            # Prompt localized for the missing fields
            question_prompt = t["clarification_prompt_template"].format(
                fields=", ".join(missing)
            )

            # to avoid to get throttled by the OCI API
            time.sleep(SLEEP_TIME)

            # Generate user-friendly clarification message using LLM
            followup_prompt = self.llm.invoke(question_prompt).content
            state["clarification_prompt"] = followup_prompt
        else:
            state["clarification_needed"] = False

        return state
