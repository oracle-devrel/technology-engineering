# hotel_node.py
# -*- coding: utf-8 -*-
"""
# SynthesizePlanNode
This module defines the SynthesizePlanNode class, which synthesizes a final travel plan

Author: L. Saetta
Date: 20/05/2025
"""

from base_node import BaseNode
from config import DEBUG


class SynthesizePlanNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for synthesizing the final travel plan.
    This node collects transport and hotel options from the state and formats them into
    a user-friendly markdown response.
    It also includes the travel dates, number of travelers, and other relevant details.
    Attributes:
        name (str): Node identifier for logging purposes.
    """

    def __init__(self):
        super().__init__("SynthesizePlanNode")

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Synthesize the final travel plan based on transport and hotel options.
        This method retrieves the transport and hotel options from the state,
        formats them into a markdown response, and updates the state with the final plan.
        Args:
            state (dict): The shared workflow state containing travel preferences and options.
            config (optional): Reserved for compatibility; not used here.
        Returns:
            dict: Updated state with 'final_plan' key containing the synthesized travel plan.
        """
        language = config.get("configurable", {}).get("language", "EN")

        if DEBUG:
            self.log_info("Synthesizing final travel plan")

        transport = state.get("flight_options", [])
        hotels = state.get("hotel_options", [])

        num_days = state.get("num_days", 0)

        transport_summary = ""
        if transport:
            option = transport[0]  # use the first result

            if language == "IT":
                transport_summary = (
                    f"**Opzione di Trasporto**\n"
                    f"- Tipo: {option.get('type')}\n"
                    f"- Fornitore: {option.get('provider')}\n"
                    f"- Partenza: {option.get('departure')}\n"
                    f"- Arrivo: {option.get('arrival')}\n"
                    f"- Prezzo: €{option.get('price')}\n"
                )
            else:
                # Default to English if not Italian
                transport_summary = (
                    f"**Transport Option**\n"
                    f"- Type: {option.get('type')}\n"
                    f"- Provider: {option.get('provider')}\n"
                    f"- Departure: {option.get('departure')}\n"
                    f"- Arrival: {option.get('arrival')}\n"
                    f"- Price: €{option.get('price')}\n"
                )
        else:
            transport_summary = "_No transport options found._"

        hotel_summary = ""
        if hotels:
            hotel = hotels[0]

            if language == "IT":
                hotel_summary = (
                    f"**Opzione di Hotel**\n"
                    f"- Nome: {hotel.get('name')}\n"
                    f"- Stelle: {hotel.get('stars')}\n"
                    f"- Posizione: {hotel.get('location')}\n"
                    f"- Servizi: {', '.join(hotel.get('amenities', []))}\n"
                    f"- Prezzo per notte: €{hotel.get('price')}\n"
                    f"- Totale per {num_days} notti: €{hotel.get('price') * num_days}\n"
                )
            else:
                # Default to English if not Italian
                hotel_summary = (
                    f"**Hotel Option**\n"
                    f"- Name: {hotel.get('name')}\n"
                    f"- Stars: {hotel.get('stars')}\n"
                    f"- Location: {hotel.get('location')}\n"
                    f"- Amenities: {', '.join(hotel.get('amenities', []))}\n"
                    f"- Price per night: €{hotel.get('price')}\n"
                    f"- Total for {num_days} nights: €{hotel.get('price') * num_days}\n"
                )
        else:
            hotel_summary = "_No hotel options found._"

        if language == "IT":
            final_text = (
                f"### ✈️ Piano di Viaggio da {state.get('place_of_departure')} a {state.get('destination')}\n\n"
                f"📅 **Date**: {state.get('start_date')} → {state.get('end_date')}\n"
                f"👥 **Viaggiatori**: {state.get('num_persons')}\n\n"
                f"{transport_summary}\n\n"
                f"{hotel_summary}\n"
            )
        else:
            # Default to English if not Italian
            final_text = (
                f"### ✈️ Travel Plan from {state.get('place_of_departure')} to {state.get('destination')}\n\n"
                f"📅 **Dates**: {state.get('start_date')} → {state.get('end_date')}\n"
                f"👥 **Travelers**: {state.get('num_persons')}\n\n"
                f"{transport_summary}\n\n"
                f"{hotel_summary}\n"
            )

        state["final_plan"] = final_text

        if DEBUG:
            self.log_info("Final plan synthesized.")

        return state
