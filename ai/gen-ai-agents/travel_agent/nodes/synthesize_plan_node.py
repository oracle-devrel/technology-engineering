# hotel_node.py
# -*- coding: utf-8 -*-
"""
# SynthesizePlanNode
This module defines the SynthesizePlanNode class, which synthesizes a final travel plan

Author: L. Saetta
Date: 22/05/2025
"""
from base_node import BaseNode
from config import DEBUG


class SynthesizePlanNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for synthesizing the final travel plan.

    This class retrieves transport and hotel options from the workflow state and
    constructs a user-friendly travel plan summary in Markdown format. It supports
    multiple languages and separates concerns via helper methods.
    """

    def __init__(self):
        """
        Initialize the node with a descriptive name for logging.
        """
        super().__init__("SynthesizePlanNode")

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Entry point for the node logic. Builds the final travel plan string and updates the state.

        Args:
            state (dict): Workflow state dictionary, containing user inputs and search results.
            config (dict, optional): Configuration dictionary. May include language settings.
            **kwargs: Additional arguments (unused).

        Returns:
            dict: Updated state dictionary with 'final_plan' key added.
        """
        language = config.get("configurable", {}).get("language", "EN")

        self.log_info("Synthesizing final travel plan...")

        # do summaries and localize in the chosen language
        transport_summary = self._get_transport_summary(state, language)
        hotel_summary = self._get_hotel_summary(state, language)
        final_text = self._get_final_text(
            state, transport_summary, hotel_summary, language
        )

        if DEBUG:
            self.log_info(state)

        # here we update the graph state with the final plan
        state["final_plan"] = final_text

        if DEBUG:
            self.log_info("Final plan synthesized.")

        return state

    def _get_transport_summary(self, state: dict, language: str) -> str:
        """
        Build a summary string of the transport option in the requested language.

        Args:
            state (dict): The workflow state, containing 'travel_options' and 'return_travel_options'.
            language (str): Language code ("EN" or "IT").

        Returns:
            str: Formatted Markdown summary of the transport options.
        """
        transport = state.get("travel_options", [])
        return_transport = state.get("return_travel_options", [])

        if not transport and not return_transport:
            return (
                "_Nessuna opzione di trasporto trovata._"
                if language == "IT"
                else "_No transport options found._"
            )

        option = transport[0]
        option_back = return_transport[0]

        if language == "IT":
            return (
                "**Opzioni di Trasporto**\n\n"
                "**Andata**\n"
                f"- Tipo: {option.get('type')}\n"
                f"- Fornitore: {option.get('provider')}\n"
                f"- Partenza: {option.get('departure')}\n"
                f"- Arrivo: {option.get('arrival')}\n"
                f"- Prezzo: €{option.get('price')}\n\n"
                "**Ritorno**\n"
                f"- Tipo: {option_back.get('type')}\n"
                f"- Fornitore: {option_back.get('provider')}\n"
                f"- Partenza: {option_back.get('departure')}\n"
                f"- Arrivo: {option_back.get('arrival')}\n"
                f"- Prezzo: €{option_back.get('price')}"
            )

        # English version (default)
        return (
            "**Transport Options**\n\n"
            "**Outbound**\n"
            f"- Type: {option.get('type')}\n"
            f"- Provider: {option.get('provider')}\n"
            f"- Departure: {option.get('departure')}\n"
            f"- Arrival: {option.get('arrival')}\n"
            f"- Price: €{option.get('price')}\n\n"
            "**Return**\n"
            f"- Type: {option_back.get('type')}\n"
            f"- Provider: {option_back.get('provider')}\n"
            f"- Departure: {option_back.get('departure')}\n"
            f"- Arrival: {option_back.get('arrival')}\n"
            f"- Price: €{option_back.get('price')}"
        )

    def _get_hotel_summary(self, state: dict, language: str) -> str:
        """
        Build a summary string of the hotel option in the requested language.

        Args:
            state (dict): The workflow state, containing a 'hotel_options' key.
            language (str): Language code ("EN" or "IT").

        Returns:
            str: Formatted Markdown summary of the hotel option.
        """
        hotels = state.get("hotel_options", [])
        num_days = state.get("num_days", 0)
        if not hotels:
            return (
                "_Nessuna opzione di hotel trovata._"
                if language == "IT"
                else "_No hotel options found._"
            )

        hotel = hotels[0]
        total_price = hotel.get("price") * num_days

        if language == "IT":
            return (
                f"**Opzione di Hotel**\n"
                f"- Nome: {hotel.get('name')}\n"
                f"- Stelle: {hotel.get('stars')}\n"
                f"- Posizione: {hotel.get('location')}\n"
                f"- Servizi: {', '.join(hotel.get('amenities', []))}\n"
                f"- Prezzo per notte: €{hotel.get('price')}\n"
                f"- Totale per {num_days} notti: €{total_price}\n"
            )

        return (
            f"**Hotel Option**\n"
            f"- Name: {hotel.get('name')}\n"
            f"- Stars: {hotel.get('stars')}\n"
            f"- Location: {hotel.get('location')}\n"
            f"- Amenities: {', '.join(hotel.get('amenities', []))}\n"
            f"- Price per night: €{hotel.get('price')}\n"
            f"- Total for {num_days} nights: €{total_price}\n"
        )

    def _get_final_text(
        self, state: dict, transport_summary: str, hotel_summary: str, language: str
    ) -> str:
        """
        Compose the final travel plan text using transport and hotel summaries.

        Args:
            state (dict): The workflow state with all user input and options.
            transport_summary (str): Summary of the selected transport.
            hotel_summary (str): Summary of the selected hotel.
            language (str): Language code ("EN" or "IT").

        Returns:
            str: Final travel plan in Markdown format.
        """
        if language == "IT":
            return (
                f"### ✈️ Piano di Viaggio da {state.get('place_of_departure')} a {state.get('destination')}\n\n"
                f"📅 **Date**: {state.get('start_date')} → {state.get('end_date')}\n"
                f"👥 **Viaggiatori**: {state.get('num_persons')}\n\n"
                f"{transport_summary}\n\n"
                f"{hotel_summary}\n"
            )

        return (
            f"### ✈️ Travel Plan from {state.get('place_of_departure')} to {state.get('destination')}\n\n"
            f"📅 **Dates**: {state.get('start_date')} → {state.get('end_date')}\n"
            f"👥 **Travelers**: {state.get('num_persons')}\n\n"
            f"{transport_summary}\n\n"
            f"{hotel_summary}\n"
        )
