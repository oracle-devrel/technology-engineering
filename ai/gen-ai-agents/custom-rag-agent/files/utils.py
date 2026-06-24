"""
File name: utils.py
Author: Luigi Saetta
Date last modified: 2025-03-31
Python Version: 3.11

Description:
    Utility functions here.

Usage:
    Import this module into other scripts to use its functions.
    Example:
      from utils import ...

License:
    This code is released under the MIT License.

Notes:
    This is a part of a demo showing how to implement an advanced
    RAG solution as a LangGraph agent.

Warnings:
    This module is in development, may change in future versions.
"""

import os
from typing import List
import logging
import re
import json
from langchain.schema import Document


def get_console_logger(name: str = "ConsoleLogger", level: str = "INFO"):
    """
    To get a logger to print on console
    """
    logger = logging.getLogger(name)

    # to avoid duplication of logging
    if not logger.handlers:
        logger.setLevel(level)

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False

    return logger


def extract_text_triple_backticks(_text):
    """
    Extracts all text enclosed between triple backticks (```) from a string.

    :param text: The input string to analyze.
    :return: A list containing the texts found between triple backticks.
    """
    logger = get_console_logger()

    # Uses (.*?) to capture text between backticks in a non-greedy way
    pattern = r"```(.*?)```"
    # re.DOTALL allows capturing multiline content

    try:
        _result = [block.strip() for block in re.findall(pattern, _text, re.DOTALL)][0]
    except Exception as e:
        logger.info("no triple backtickes in extract_text_triple_backticks: %s", e)

        # try to be resilient, return the entire text
        _result = _text

    return _result


def extract_json_from_text(text):
    """
    Extracts JSON content from a given text and returns it as a Python dictionary.

    Args:
        text (str): The input text containing JSON content.

    Returns:
        dict: Parsed JSON data.
    """
    try:
        # Use regex to extract JSON content (contained between {})
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            json_content = json_match.group(0)
            return json.loads(json_content)

        # If no JSON content is found, raise an error
        raise ValueError("No JSON content found in the text.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e


# for the loading utility
def remove_path_from_ref(ref_pathname):
    """
    remove the path from source (ref)
    """
    ref = ref_pathname
    # check if / or \ is contained
    if len(ref_pathname.split(os.sep)) > 0:
        ref = ref_pathname.split(os.sep)[-1]

    return ref


def docs_serializable(docs: List[Document]) -> dict:
    """
    Convert Langchain document in dict json serializable.

    (30/06/2025): this function has been introduced to transform Langchain Document in dict,
    that can be easily serializable (for the streaming API)
    Args:
        docs (List[Document]): Lista     di Document da convertire.
    Returns:
    """
    _docs_serializable = [
        {"page_content": doc.page_content, "metadata": doc.metadata or {}}
        for doc in docs
    ]
    return _docs_serializable


def print_mcp_available_tools(tools):
    """
    Print the available tools in a readable format.

    Args:
        tools (list): List of tools to print.
    """
    print("\n--- MCP Available tools:")
    for tool in tools:
        print(f"Tool: {tool.name} - {tool.description}")
        print("Input Schema:")
        pretty_schema = json.dumps(tool.inputSchema, indent=4, sort_keys=True)
        print(pretty_schema)
        print("")
