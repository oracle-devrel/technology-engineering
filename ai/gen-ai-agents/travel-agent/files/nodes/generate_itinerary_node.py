# generate_itinerary_node.py
# -*- coding: utf-8 -*-
"""
GenerateItineraryNode

This LangGraph node uses an LLM to generate a personalized day-by-day travel itinerary
based on the selected destination, number of days, and user preferences.

Author: L. Saetta
Date: 20/10/2025
"""
import time
from base_node import BaseNode
from model_factory import get_chat_model
from config import MODEL_ID, SERVICE_ENDPOINT, MAX_TOKENS, DEBUG, SLEEP_TIME
from translations import TRANSLATIONS


class GenerateItineraryNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for generating a personalized travel itinerary.
    """

    def __init__(self):
        super().__init__("GenerateItineraryNode")

        self.llm = get_chat_model(
            model_id=MODEL_ID,
            service_endpoint=SERVICE_ENDPOINT,
            temperature=0.7,
            max_tokens=MAX_TOKENS,
        )

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Generate a personalized travel itinerary based on user preferences and destination.
        Args:
            state (dict): The shared workflow state containing user inputs and search results.
            config (dict, optional): Configuration dictionary. May include language settings.
            **kwargs: Additional arguments (unused).
        Returns:
            dict: Updated state dictionary with 'itinerary' key added,
            containing the generated itinerary.
        """
        self.log_info("Generating itinerary...")

        language = config.get("configurable", {}).get("language", "EN")
        t = TRANSLATIONS[language]

        destination = state.get("destination", "")
        num_days = state.get("num_days", 3)
        interests = state.get("hotel_preferences", {}).get("location", "central")
        hotel = state.get("hotel_options", [{}])[0].get("name", "a hotel")

        itinerary_prompt = t["itinerary_prompt_template"].format(
            destination=destination,
            num_days=num_days,
            hotel=hotel,
            location=interests,
        )

        # to avoid to get throttled by the OCI API
        time.sleep(SLEEP_TIME)

        response = self.llm.invoke(itinerary_prompt).content

        if DEBUG:
            self.log_info(state)

        state["itinerary"] = f"\n\n{t['suggested_itinerary_title']}\n{response}"

        if DEBUG:
            self.log_info("Itinerary generated.")

        return state
