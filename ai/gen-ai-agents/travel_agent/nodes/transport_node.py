# search_transport_node.py
# -*- coding: utf-8 -*-
"""
SearchTransportNode

This module defines the SearchTransportNode class, which is responsible for retrieving
transport options (e.g., flights or trains) based on user-provided travel details.

It queries a mock or real API and stores the results in the workflow state under 'travel_options'.

Author: L. Saetta
Date: 22/05/2025

"""
import requests
from base_node import BaseNode
from config import DEBUG, TRANSPORT_API_URL


class SearchTransportNode(BaseNode):
    """
    Node in the LangGraph workflow responsible for retrieving transport options.

    This node uses an HTTP API to search for available transport (e.g., flights or trains)
    based on destination, start date, and preferred transport type. The results are stored
    in the shared workflow state for further processing.

    Attributes:
        name (str): Node identifier for logging purposes.
    """

    def __init__(self):
        """
        Initialize the SearchTransportNode and configure its name for logging.
        """
        super().__init__("SearchTransportNode")

    def _get_travel_option(
        self,
        place_of_departure: str,
        destination: str,
        start_date: str,
        transport_type: str,
    ) -> dict:
        """
        Helper method to query the transport API for travel options.

        Args:
            place_of_departure (str): The starting location for the travel.
            destination (str): The destination location.
            transport_type (str): The type of transport (e.g., flight, train).

        Returns:
            dict: Parsed JSON response from the transport API.
        """
        response = requests.get(
            TRANSPORT_API_URL,
            params={
                "place_of_departure": place_of_departure,
                "destination": destination,
                "start_date": start_date,
                "transport_type": transport_type,
            },
            timeout=5,
        )
        return response

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Query a transport search API and update the state with transport options.

        Args:
            state (dict): The shared workflow state containing travel preferences.
            config (optional): Reserved for compatibility; not used here.

        Returns:
            dict: Updated state with 'travel_options' key containing a list of transport results.
        """
        self.log_info("Searching for transport options...")

        try:
            # first find travel to destination
            response = self._get_travel_option(
                state.get("place_of_departure"),
                state.get("destination"),
                state.get("start_date"),
                state.get("transport_type"),
            )

            data = response.json()
            state["travel_options"] = data.get("options", [])

            # then find the travel back
            response = self._get_travel_option(
                state.get("destination"),
                state.get("place_of_departure"),
                state.get("end_date"),
                state.get("transport_type"),
            )

            data = response.json()
            state["return_travel_options"] = data.get("options", [])

            if DEBUG:
                self.log_info(f"Found transport: {data}")
        except Exception as e:
            self.log_error(f"Transport search failed: {e}")

        return state
