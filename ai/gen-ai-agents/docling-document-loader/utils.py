"""
Author: Luigi Saetta
Date last modified: 2026-01-14
Python Version: 3.11
License: MIT

Description:
    Utility functions for logging, path manipulation, value checking,
    and statistical computations.

"""

import logging
import os
import numpy as np


def remove_path_from_ref(ref_pathname):
    """
    remove the path from source (ref)
    """
    ref = ref_pathname
    # check if / or \ is contained
    if len(ref_pathname.split(os.sep)) > 0:
        ref = ref_pathname.split(os.sep)[-1]

    return ref


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


def check_value_in_list(value, values_list):
    """
    to check that we don't enter a not supported value
    """
    if value not in values_list:
        raise ValueError(
            f"Value {value} is not valid: value must be in list {values_list}"
        )


def compute_stats(list_docs):
    """
    Compute stats for the distribution of chunks' lengths

    list_docs: LangChain list of Documents
    """
    lengths = [len(d.page_content) for d in list_docs]

    mean_length = int(round(np.mean(lengths), 0))
    std_dev = int(round(np.std(lengths), 0))
    perc_75_len = int(round(np.percentile(lengths, 75), 0))

    return mean_length, std_dev, perc_75_len
