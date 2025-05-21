"""
Defines the shared state structure used by all nodes in the travel planner LangGraph workflow.

This state is passed between nodes and incrementally filled as the workflow progresses.
"""

from typing import TypedDict, Dict, List


class TravelState(TypedDict, total=False):
    """
    Shared state for the travel planning agent.

    Each field in this structure represents a piece of information extracted,
    enriched, or used by the AI agent during the travel planning process.

    Fields:
        user_input (str): Raw natural language input from the user.
        place_of_departure (str): Starting city or region for the trip.
        destination (str): Target destination city or region.
        start_date (str): Start date of the trip in 'YYYY-MM-DD' format.
        end_date (str): End date of the trip in 'YYYY-MM-DD' format.
        num_persons (int): Number of travelers.
        transport_type (str): Preferred transport method ("airplane", "train", etc.).
        hotel_preferences (Dict): Preferences for hotel (e.g., stars, location).
        flight_options (List): Available or suggested flight options.
        hotel_options (List): Available or suggested hotel options.
        final_plan (str): Generated summary plan to return to the user.
    """

    # unique_identifier for the request
    request_id: str
    # the string with user input
    user_input: str

    # the structured output
    place_of_departure: str
    destination: str
    start_date: str
    end_date: str
    num_days: int
    num_persons: int
    transport_type: str
    hotel_preferences: Dict
    flight_options: List
    hotel_options: List

    # the final plan to return to the user
    final_plan: str

    # new fields for clarification loop
    clarification_needed: bool
    clarification_prompt: str
