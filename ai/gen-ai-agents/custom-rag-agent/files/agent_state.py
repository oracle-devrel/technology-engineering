"""
File name: agent_state.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module defines the class that handles the agent's State


Usage:
    Import this module into other scripts to use its functions.
    Example:
        from agent_state import State

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

from typing_extensions import TypedDict, Optional


class State(TypedDict):
    """
    The state of the graph
    """

    # the original user request
    user_request: str
    chat_history: list = []

    # the question reformulated using chat_history
    standalone_question: str = ""

    # similarity_search
    # 30/06: modified, now they're a dict with
    # page_content and metadata
    # populated with docs_serializable (utils.py)
    retriever_docs: Optional[list] = []
    # reranker
    reranker_docs: Optional[list] = []
    # Answer
    final_answer: str
    # Citations
    citations: list = []

    # if any step encounter an error
    error: Optional[str] = None
