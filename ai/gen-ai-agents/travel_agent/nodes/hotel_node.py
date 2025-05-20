# hotel_node.py
# -*- coding: utf-8 -*-
"""
SearchHotelNode

This module defines the SearchHotelNode class, which queries available hotel options
for a given destination and preferences, and stores the result in the LangGraph state.

Author: L. Saetta
Date: 20/05/2025
"""

import requests
from base_node import BaseNode
from config import HOTEL_API_URL


class SearchHotelNode(BaseNode):
    """
    Hotel node in the LangGraph workflow responsible for searching hotel options.
    """

    def __init__(self):
        super().__init__("SearchHotelNode")

    def invoke(self, state: dict, config=None, **kwargs) -> dict:
        self.log_info("Searching for hotels")
        try:
            prefs = state.get("hotel_preferences", {})

            # here we call the API
            response = requests.get(
                HOTEL_API_URL,
                params={
                    "destination": state.get("destination"),
                    # default 3 stars
                    "stars": prefs.get("stars", 3),
                },
                timeout=5,
            )
            data = response.json()
            state["hotel_options"] = data.get("hotels", [])
            self.log_info(f"Found hotels: {data}")
        except Exception as e:
            self.log_error(f"Hotel search failed: {e}")
        return state
