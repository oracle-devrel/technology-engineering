"""
Base Node class for LangGraph nodes.

This module defines a base class `BaseNode` for all LangGraph nodes,
providing a standard logging interface via `log_info` and `log_error` methods.
Each subclass should implement the `invoke(input, config=None)` method.
"""

import logging
from langchain_core.runnables import Runnable


class BaseNode(Runnable):
    """
    Abstract base class for LangGraph nodes.

    All node classes in the graph should inherit from this base class.
    It provides convenient logging utilities and stores a unique node name
    for identification in logs and debugging.

    Attributes:
        name (str): Identifier for the node, used in logging.
        logger (logging.Logger): Configured logger instance for the node.
    """

    def __init__(self, name: str):
        """
        Initialize the base node with a logger.

        Args:
            name (str): Unique name of the node for logging purposes.
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Attach a default console handler if no handlers are present
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "[%(asctime)s] %(levelname)s in %(name)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def log_info(self, message: str):
        """
        Log an informational message.

        Args:
            message (str): The message to log.
        """
        self.logger.info("[%s] %s", self.name, message)

    def log_error(self, message: str):
        """
        Log an error message.

        Args:
            message (str): The error message to log.
        """
        self.logger.error("[%s] %s", self.name, message)
