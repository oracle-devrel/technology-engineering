"""
utils.py

Utility functions for text processing and JSON extraction from LLM outputs.
"""

import logging
import json
import re


def extract_json_from_text(text):
    """
    Extracts JSON content from a given text and returns it as a Python dictionary.

    Args:
        text (str): The input text containing JSON content.

    Returns:
        dict: Parsed JSON data.
    """
    try:
        # Remove triple backticks and leading/trailing whitespace
        text = remove_triple_backtics(text).strip()
        # Use regex to extract JSON content (contained between {})
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            json_content = json_match.group(0)
            return json.loads(json_content)

        # If no JSON content is found, raise an error
        raise ValueError("No JSON content found in the text.")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}") from e


def remove_triple_backtics(input_text: str) -> str:
    """
    Remove triple backticks and language markers (e.g., ```json, ```python) from LLM responses.

    Args:
        input_text (str): Text that may include markdown code fences.

    Returns:
        str: Cleaned text without triple backticks.
    """
    _text = re.sub(r"```(json|python)?", "", input_text, flags=re.IGNORECASE)
    _text = _text.replace("```", "")
    return _text


def get_console_logger(
    name: str = "console_logger", level=logging.INFO
) -> logging.Logger:
    """
    Create a console logger for debugging purposes.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
