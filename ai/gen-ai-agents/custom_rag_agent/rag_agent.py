"""
File name: rag_agent.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    This module implements the orchestration in the Agent.
    Based on LanGraph.

Usage:
    Import this module into other scripts to use its functions.
    Example:


License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

from langgraph.graph import StateGraph, START, END

from agent_state import State

from content_moderation import ContentModerator
from query_rewriter import QueryRewriter
from vector_search import SemanticSearch
from reranker import Reranker
from answer_generator import AnswerGenerator


def create_workflow():
    """
    Create the entire workflow
    """
    workflow = StateGraph(State)

    # create nodes (each is a a Runnable)
    # step 0: content moderation
    moderator = ContentModerator()
    # step 1: rewrite the user request using history
    query_rewriter = QueryRewriter()
    # step 2: do semantic search
    semantic_search = SemanticSearch()
    # step 3: filter and rerank, using a LLM
    reranker = Reranker()
    # step 4: genereta final answer
    answer_generator = AnswerGenerator()

    # Add nodes
    workflow.add_node("Moderator", moderator)
    workflow.add_node("QueryRewrite", query_rewriter)
    workflow.add_node("Search", semantic_search)
    workflow.add_node("Rerank", reranker)
    workflow.add_node("Answer", answer_generator)

    # define edges
    workflow.add_edge(START, "Moderator")
    workflow.add_edge("Moderator", "QueryRewrite")
    workflow.add_edge("QueryRewrite", "Search")
    workflow.add_edge("Search", "Rerank")
    workflow.add_edge("Rerank", "Answer")
    workflow.add_edge("Answer", END)

    # create workflow executor
    workflow_app = workflow.compile()

    return workflow_app
