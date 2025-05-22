# search_transport_node.py
# -*- coding: utf-8 -*-
"""
SearchTransportNode

This module defines the SearchTransportNode class, which is responsible for retrieving
transport options (e.g., flights or trains) based on user-provided travel details.

It queries a mock or real API and stores the results in the workflow state under 'flight_options'.

Author: L. Saetta
Date: 20/05/2025

"""
import time
import requests
from base_node import BaseNode
from config import TRANSPORT_API_URL


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

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        """
        Query a transport search API and update the state with transport options.

        Args:
            state (dict): The shared workflow state containing travel preferences.
            config (optional): Reserved for compatibility; not used here.

        Returns:
            dict: Updated state with 'flight_options' key containing a list of transport results.
        """
        self.log_info("Searching for transport options")

        # Simulate network delay or latency
        time.sleep(2)

        try:
            response = requests.get(
                TRANSPORT_API_URL,
                params={
                    "destination": state.get("destination"),
                    "start_date": state.get("start_date"),
                    "transport_type": state.get("transport_type"),
                },
                timeout=5,
            )
            data = response.json()
            state["flight_options"] = data.get("options", [])
            self.log_info(f"Found transport: {data}")
        except Exception as e:
            self.log_error(f"Transport search failed: {e}")

        return state
