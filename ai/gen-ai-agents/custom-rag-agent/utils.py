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
import logging
import re
import json


def get_console_logger():
    """
    To get a logger to print on console
    """
    logger = logging.getLogger("ConsoleLogger")

    # to avoid duplication of logging
    if not logger.handlers:
        logger.setLevel(logging.INFO)

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

    pattern = r"```(.*?)```"  # Uses (.*?) to capture text between backticks in a non-greedy way
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
        raise ValueError(f"Invalid JSON format: {e}")


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
