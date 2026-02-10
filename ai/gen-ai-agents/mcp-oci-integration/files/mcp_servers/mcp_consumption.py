"""
File name: mcp_consumption.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for querying OCI (Oracle Cloud Infrastructure)
    usage and consumption data. It provides tools for generating usage summaries by service or compartment,
    detailed breakdowns, and listing Autonomous Databases (ADBs) in specified compartments.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_consumption import usage_summary_by_service

        results = usage_summary_by_service("2025-01-01", "2025-03-31")
        # Or run the server: python mcp_consumption.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and relies on utilities from consumption_utils and oci_utils.
    Tools are designed for integration with MCP agents and handle errors with structured dictionary outputs.

Warnings:
    This module is in development and may change in future versions. Ensure date ranges do not exceed 93 days
    to avoid API errors, and handle potential exceptions in production use.
"""

from typing import Any, Dict, List

# here are functions calling OCI API
from consumption_utils import (
    usage_summary_by_service_structured,
    usage_summary_by_compartment_structured,
    fetch_consumption_by_compartment,
    usage_summary_by_service_for_compartment,
)
from oci_utils import (
    list_adbs_in_compartment,
    get_compartment_id_by_name,
    list_adbs_in_compartment_list,
)
from mcp_utils import create_server, run_server
from utils import get_console_logger

from config import DEBUG

logger = get_console_logger()

mcp = create_server("OCI Consumption MCP server")


#
# MCP tools definition
#
# results are wrapped
#
@mcp.tool
def usage_summary_by_service(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Return the total consumption aggregated by service within a specified time period.

    Args:
        start_date (str): Start date of the period, in ISO format (YYYY-MM-DD).
        end_date (str): End date of the period, in ISO format (YYYY-MM-DD).
            The time window between start_date and end_date must not exceed 93 days.

    Returns:
        dict: A structured dictionary containing consumption details aggregated by service.

    Raises:
        Error: If the time period exceeds 93 days, or any other errors occurs.
    """

    if DEBUG:
        logger.info("Called usage_summary_by_service...")

    try:
        results = usage_summary_by_service_structured(start_date, end_date)
    except Exception as e:
        logger.error("Error generating consumption: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def usage_summary_by_compartment(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Return the total consumption aggregated by compartment within a specified period.

    Args:
        start_date (str): Start date of the period, in ISO format (YYYY-MM-DD).
        end_date (str): End date of the period, in ISO format (YYYY-MM-DD).
            The time window between start_date and end_date must not exceed 93 days.

    Returns:
        dict: A structured dictionary containing consumption details aggregated by compartment.

    Raises:
        Error: If the time period exceeds 93 days, or any other errors occurs.
    """
    if DEBUG:
        logger.info("Called usage_summary_by_compartment...")

    try:
        results = usage_summary_by_compartment_structured(start_date, end_date)
    except Exception as e:
        logger.error("Error generating consumption: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def usage_breakdown_for_service_by_compartment(
    start_date: str, end_date: str, service_name: str
) -> Dict[str, Any]:
    """
    Return the consumption for a specific service within a given time period,
    broken down by compartment.

    Args:
        start_date (str): Start date of the period, in ISO format (YYYY-MM-DD).
        end_date (str): End date of the period, in ISO format (YYYY-MM-DD).
            The time window between start_date and end_date must not exceed 93 days.
        service_name (str): Name of the service to filter by.
            Case-insensitive and substring matches are allowed.

    Returns:
        dict: A structured dictionary containing consumption details by compartment.
            Each entry corresponds to one compartment.

    Raises:
        Error: If the time period exceeds 93 days, or any other errors occurs.
    """
    try:
        results = fetch_consumption_by_compartment(start_date, end_date, service_name)
    except Exception as e:
        logger.error("Error generating breakdown: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def usage_breakdown_for_compartment_by_service(
    start_date: str, end_date: str, compartment_name: str
) -> Dict[str, Any]:
    """
    Return the consumption for a specific compartment within a given time period,
    broken down by service.

    Args:
        start_date (str): Start date of the period, in ISO format (YYYY-MM-DD).
        end_date (str): End date of the period, in ISO format (YYYY-MM-DD).
            The time window between start_date and end_date must not exceed 93 days.
        compartment_name (str): Name of the compartment to filter by.
            Case-insensitive and substring matches are allowed.

    Returns:
        dict: A structured dictionary containing consumption details by service.
            Each entry corresponds to one service.
    Raises:
        Error: If the time period exceeds 93 days, or any other errors occurs.
    """
    try:
        results = usage_summary_by_service_for_compartment(
            start_date, end_date, compartment_name
        )
    except Exception as e:
        logger.error("Error generating breakdown: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def list_adb_for_compartment(compartment_name: str) -> Dict[str, Any]:
    """
    Return the list of Autonomous Databases in a given compartment.

    Args:
        compartment_name (str): Name of the compartment to filter by.
            Case-insensitive and substring matches are allowed.

    Returns:
        dict: A structured dictionary containing Autonomous Database details.
            Each entry corresponds to one Autonomous Database.
    Raises:
        Error: If any error occurs.
    """
    try:
        compartment_id = get_compartment_id_by_name(compartment_name)
        if not compartment_id:
            raise ValueError(f"Compartment '{compartment_name}' not found")

        adbs = list_adbs_in_compartment(compartment_id)

        results = {"autonomous_databases": adbs}
    except Exception as e:
        logger.error("Error listing Autonomous Databases: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def list_adb_for_compartments_list(compartments_list: List[str]) -> Dict[str, Any]:
    """
    Return the list of Autonomous Databases for a list of compartments.

    Args:
        compartments_lists (list): List of the names of the compartments

    Return:
        dicts: A structured dictionary containing Autonomous Database details for each compartment.
            Each entry corresponds to a compartment.

    """
    try:
        results = list_adbs_in_compartment_list(compartments_list)
    except Exception as e:
        logger.error("Error listing Autonomous Databases for compartments: %s", e)
        results = {"error": str(e)}

    return results


#
# Run the Select AI MCP server
#
if __name__ == "__main__":
    run_server(mcp)
