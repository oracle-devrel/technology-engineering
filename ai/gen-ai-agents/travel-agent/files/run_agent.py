"""
run_agent.py

Defines the asynchronous entry point to invoke the LangGraph-based travel planning agent.
This module prepares the initial state from user input, runs the workflow, and formats the output.
"""

from travel_state import TravelState
from workflow import create_travel_planner_graph

# Compile the LangGraph once at module level
travel_agent_graph = create_travel_planner_graph()


async def run_agent(user_input: str, config: dict = None) -> str:
    """
    Run the travel planning agent with the given user input.

    Args:
        user_input (str): A free-form natural language string describing the user's travel needs.

    Returns:
        str: A formatted Markdown string summarizing the extracted travel plan.
    """
    initial_state = TravelState(
        request_id=config.get("configurable", "").get("thread_id", ""),
        user_input=user_input,
    )

    final_state = await travel_agent_graph.ainvoke(initial_state, config=config or {})

    # Se è una richiesta di chiarimento, restituisci il messaggio al posto del piano
    if final_state.get("clarification_needed"):
        return {
            "final_plan": final_state.get(
                "clarification_prompt", "I need more details to proceed."
            ),
            "hotel_options": [],
            "clarification_needed": True,
        }

    # Final, complete answer
    return {
        "final_plan": final_state.get(
            "final_plan", "Sorry, I couldn't generate a travel plan."
        ),
        "itinerary": final_state.get("itinerary", ""),
        "hotel_options": final_state.get("hotel_options", []),
        "travel_options": final_state.get("travel_options", []),
        "clarification_needed": False,
    }
