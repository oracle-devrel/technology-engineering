"""
File name: mcp_oml_predictions.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP Server that calls an OML model for prediction.
    In the demo: F1 race predictions based on team budget, driver age, etc.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_oml_predictions import oml_predict

        result = oml_predict(race_year="2024", total_points="250", team_budget="100", driver_age="27")
        # Or run the server: python mcp_oml_predictions.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP‑OCI integration framework.
    The tool returns a dictionary with a single key "race_position".

Warnings:
    This module is in development and may change in future versions.
    Ensure the OML service is reachable and the input types are valid.
"""

from typing import Dict, Any

from oml_utils import get_predictions
from mcp_utils import create_server, run_server


mcp = create_server("OCI MCP OML Predictions")


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
@mcp.tool
def oml_predict(
    race_year: str = "2024",
    total_points: str = "250",
    team_budget: str = "100",
    driver_age: str = "27",
) -> Dict[str, Any]:
    """
    Return the result of OML predictions for
    the provided input parameters.

    Args:
        race_year (str): the race year.
        total_points (str): total points so far.
        team_budget (str): team budget in million $.
        driver_age (str): driver age in years.

    Returns:
        dict: prediction results from OML.

    """
    results = get_predictions(
        int(race_year), float(total_points), int(team_budget), int(driver_age)
    )

    return {"race_position": results}


#
# Run the MCP server
#
if __name__ == "__main__":
    run_server(mcp)
