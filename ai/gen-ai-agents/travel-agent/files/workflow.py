"""
Travel Planner Workflow Definition

Defines the LangGraph-based workflow for the travel planning AI agent.
This initial version includes only the input parsing step.
"""

from langgraph.graph import StateGraph, START, END
from travel_state import TravelState
from nodes.router_node import RouterNode
from nodes.parse_input_node import ParseInputNode
from nodes.transport_node import SearchTransportNode
from nodes.hotel_node import SearchHotelNode
from nodes.synthesize_plan_node import SynthesizePlanNode
from nodes.clarification_node import ClarificationNode
from nodes.answer_info_node import AnswerInfoNode
from nodes.generate_itinerary_node import GenerateItineraryNode


def create_travel_planner_graph():
    """
    Construct and compile the LangGraph workflow for the travel planning agent.

    The graph currently includes a single node:
        - "parse_input": Extracts structured travel details from raw user input.

    Returns:
        graph (CompiledGraph): A runnable LangGraph instance.
    """
    builder = StateGraph(TravelState)

    # the node for intent classification
    builder.add_node("router", RouterNode())
    # Add the node responsible for parsing the user input
    builder.add_node("parse_input", ParseInputNode())
    # node to check if there are missing fields
    builder.add_node("clarify", ClarificationNode())
    builder.add_node("search_transport", SearchTransportNode())
    builder.add_node("search_hotel", SearchHotelNode())
    builder.add_node("synthesize_plan", SynthesizePlanNode())
    builder.add_node("generate_itinerary", GenerateItineraryNode())
    # for the branch of the workflow that answers general information
    builder.add_node("answer_info", AnswerInfoNode())

    # Define the entry and exit points of the workflow: intent classification
    builder.add_edge(START, "router")

    builder.add_conditional_edges(
        "router",
        lambda state: state["intent"],
        {
            "booking": "parse_input",
            "info": "answer_info",
        },
    )

    builder.add_edge("parse_input", "clarify")

    # check if there are missing fields
    builder.add_conditional_edges(
        "clarify",
        lambda state: (
            "search_transport" if not state.get("clarification_needed") else "end"
        ),
        {"search_transport": "search_transport", "end": END},
    )

    # for now, sequential, could be in parallel
    builder.add_edge("search_transport", "search_hotel")
    builder.add_edge("search_hotel", "synthesize_plan")
    builder.add_edge("synthesize_plan", "generate_itinerary")
    builder.add_edge("generate_itinerary", END)

    # info
    builder.add_edge("answer_info", END)

    # Compile and return the runnable graph
    return builder.compile()
