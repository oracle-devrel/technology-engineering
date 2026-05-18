"""
ParseInputNode

LangGraph node responsible for parsing natural language travel requests
into structured data using an LLM hosted on Oracle Cloud Infrastructure (OCI).
"""

import time
from datetime import date
from prompt_template import input_parser_prompt
from model_factory import get_chat_model

from base_node import BaseNode
from utils import extract_json_from_text
from config import MODEL_ID, SERVICE_ENDPOINT, DEBUG, MAX_TOKENS, SLEEP_TIME


class ParseInputNode(BaseNode):
    """
    LangGraph node that uses an OCI-hosted LLM to extract structured travel planning
    data from a user's natural language input.

    It parses values such as destination, dates, number of persons, transport type,
    and hotel preferences.
    """

    def __init__(self):
        """
        Initialize the node and configure the LLM (Meta Llama 3.3 via OCI Generative AI).
        """
        super().__init__("ParseInputNode")

        self.llm = get_chat_model(
            model_id=MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            temperature=0.0,
            max_tokens=MAX_TOKENS,
        )

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Invoke the node: parse user input using the LLM and update the state with structured values.

        Args:
            state (dict): The current shared workflow state, must contain the key 'user_input'.
            config (optional): Unused config passed by LangGraph.

        Returns:
            dict: Updated state with extracted travel fields added.
        """
        # to tell to the LLM that we are using the current date
        # in the prompt, we need to pass it as a string
        # in ISO format (YYYY-MM-DD)
        today_str = date.today().isoformat()

        # Format the input using the prompt template
        formatted_prompt = input_parser_prompt.format(
            user_input=state["user_input"], today=today_str
        )

        try:
            # to avoid to get throttled by the OCI API
            time.sleep(SLEEP_TIME)

            # Call the LLM with the formatted prompt
            result = self.llm.invoke(formatted_prompt)

            if DEBUG:
                self.log_info(f"LLM response: {result.content}")

            # Extract JSON structure from model response
            structured_data = extract_json_from_text(result.content)

            if DEBUG:
                self.log_info(f"Extracted JSON: {structured_data}")

            # Update state with parsed values
            state.update(structured_data)

            if DEBUG:
                self.log_info("Parsed user input successfully.")

        except Exception as e:
            self.log_error(f"Failed to parse user input: {e}")
            raise e

        return state
