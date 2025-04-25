"""
This module provides functions to manage the context within a Jupyter Notebook.
It includes utilities to retrieve user-defined variables from the user's namespace
and provide detailed information about them.
"""

import types
from typing import Any, Dict
from config import MAX_ROWS_IN_SAMPLE


def filter_variables(namespace: Dict[str, Any]):
    """
    Filter and return a dictionary of user-defined,
    non-private variables from the provided namespace.

    Args:
        namespace (Dict[str, Any]): The namespace dictionary
        containing variable names and their corresponding values.

    Returns:
        Dict[str, Any]: A dictionary containing variable names and values that are user-defined,
        non-private, not modules, not IPython's input/output history, and not callable objects.

    Example:
        >>> user_ns = {'_private_var': 1, 'public_var': 2, 'In': [], 'Out': {}, 'func': lambda x: x}
        >>> filter_variables(user_ns)
        {'public_var': 2}
    """
    variables_and_values = {}
    for name, value in namespace.items():
        # Exclude internal variables and modules
        if not name.startswith("_") and not isinstance(value, types.ModuleType):
            # Exclude IPython's In and Out history
            if name not in ["In", "Out"]:
                # Exclude functions and other callables
                if not callable(value):
                    variables_and_values[name] = value
    # return a dict ({k:v})
    return variables_and_values


def extract_variables_from_query(line: str) -> set:
    """
    Extract and return a set of potential variable names from the given query string.

    Args:
        line (str): The input query string from which to extract variable names.

    Returns:
        Set[str]: A set of unique strings that are valid Python identifiers,
        representing potential variable names.

    Example:
        >>> extract_variables_from_query("Analyze the data in df and plot the results.")
        {'df'}
    """
    variables = set()

    for word in line.split():
        # Only consider words that look like valid Python identifiers
        if word.isidentifier():
            variables.add(word)
    return variables


def get_variable_info(name: str, value: Any) -> str:
    """
    Generate and return a detailed string representation of a variable's information.

    Args:
        name (str): The name of the variable.
        value (Any): The value of the variable.

    Returns:
        str: A formatted string containing the variable's name, type, and additional details
        such as shape and columns for DataFrames, attributes for objects,
        or length and sample content for containers.

    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'A': [1, 2], 'B': [3, 4]})
        >>> print(get_variable_info('df', df))
        Variable: df
        Type: DataFrame
        Shape: (2, 2)
        Columns:
        - A (int64)
        - B (int64)
        Sample (first MAX_ROWS_IN_SAMPLE rows):
           A  B
        0  1  3
        1  2  4
    """
    info_parts = [f"Variable: {name}"]
    info_parts.append(f"Type: {type(value).__name__}")

    # dataframes
    if "DataFrame" in str(type(value)):
        if len(value) > MAX_ROWS_IN_SAMPLE:
            # does a random sub-sampling
            value = value.sample(n=MAX_ROWS_IN_SAMPLE, random_state=42)

        info_parts.append(f"Shape: {value.shape}")
        info_parts.append("Columns:")
        for col in value.columns:
            info_parts.append(f"- {col} ({value[col].dtype})")
        info_parts.append(f"\nSample (max {MAX_ROWS_IN_SAMPLE} rows):")

        info_parts.append(str(value))

    # objects
    elif hasattr(value, "__dict__"):
        try:
            attrs = dir(value)
            info_parts.append("Attributes:")
            for attr in attrs:
                if not attr.startswith("_"):
                    info_parts.append(f"- {attr}")
        except Exception:
            pass

    # containers
    elif hasattr(value, "__len__"):
        info_parts.append(f"Length: {len(value)}")
        try:
            sample = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
            info_parts.append(f"Sample: {sample}")
        except Exception:
            pass

    return "\n".join(info_parts)


def get_context(user_ns: Dict[str, Any], line: str) -> str:
    """
    Extract and return relevant context from the user's namespace
    based on the variables mentioned in the query line.

    Args:
        user_ns (Dict[str, Any]): The user's namespace containing variable names
            and their corresponding values.
        line (str): The input query string potentially referencing variables
            in the namespace.

    Returns:
        str: A formatted string containing detailed information about the variables
            referenced in the query line.

    Example:
        >>> user_ns = {'df': pd.DataFrame({'A': [1, 2]})}
        >>> line = "Show the summary of df"
        >>> print(get_context(user_ns, line))
        Variable: df
        Type: DataFrame
        Shape: (2, 1)
        Columns:
        - A (int64)
        Sample (first 5 rows):
           A
        0  1
        1  2
    """
    # include only non-private variables
    filtered_ns = filter_variables(user_ns)

    user_vars = extract_variables_from_query(line)
    context_parts = []

    for var_name in user_vars:
        if var_name in filtered_ns:
            # print("Adding: ", var_name)

            var_value = filtered_ns[var_name]
            context_parts.append(get_variable_info(var_name, var_value))

    return "\n".join(context_parts)
