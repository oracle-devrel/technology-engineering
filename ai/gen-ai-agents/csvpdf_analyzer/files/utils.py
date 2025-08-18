"""
utils.py
"""

import json
import re
import logging


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


def remove_triple_backtics(input_text: str) -> str:
    """
    Remove triple backtics from a string
    """
    _text = input_text.replace("```python", "")
    _text = _text.replace("```", "")
    return _text


def extract_json_from_string(input_string):
    """
    Extracts the JSON part from a string that contains extra characters outside the JSON object.
    Converts the extracted JSON into a Python dictionary.
    """
    # Use regex to find the first JSON object inside `{}` in the string
    match = re.search(r"\{.*\}", input_string, re.DOTALL)
    if match:
        json_str = match.group(0)  # Extract the JSON part
        try:
            return json.loads(json_str)  # Convert JSON string to dictionary
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format found in the string")
    else:
        raise ValueError("No valid JSON object found in the string")
