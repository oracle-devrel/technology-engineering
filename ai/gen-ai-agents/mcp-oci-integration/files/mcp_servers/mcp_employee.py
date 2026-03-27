"""
File name: mcp_employee.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for querying employee information.
    It provides tools to retrieve data for individual employees by ID or name, as well as lists of all employees,
    with structured outputs including details like department, location, and vacation days.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_employee import get_employee_info

        employee_data = get_employee_info("1010")
        # Or run the server: python mcp_employee.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and uses mock or database-backed data for employee queries.
    Tools return dictionaries with 'ok', 'employees', and 'error' keys for easy integration with MCP agents.

Warnings:
    This module is in development and may change in future versions. Handle sensitive employee data with care
    to ensure privacy compliance, and note that real-world implementations should use secure data sources.
"""

from typing import Any, Dict

from employee_api import get_employee, list_employees
from mcp_utils import create_server, run_server
from utils import get_console_logger

from config import (
    DEBUG,
)


logger = get_console_logger()

mcp = create_server("OCI HCM MCP server")


#
# MCP tools definition
# add and write the code for the tools here
# mark each tool with the annotation
#
# results are wrapped
#
@mcp.tool
def get_employee_info(identifier: str) -> Dict[str, Any]:
    """
    Return employee data.

    Args:
        identifier: employee id or full name.

    Returns:
        dict: data regarding employee.

    Examples:
        >>> get_employee_info("1010")
        {
            "employee_id": "1010",
            "employee_name": "Jakob Johansson",
            "dept_name": "Security Engineering",
            "location": "Stockholm, Sweden",
            "employee_level": "IC3",
            "vacation_days_taken": 9,
        }
    """
    if DEBUG:
        logger.info("Called get_employee_info...")

    try:
        # in a real case we should call here HCM API
        results = get_employee(identifier)
    except Exception as e:
        logger.error("Error getting data for employee: %s, error: %s", identifier, e)
        results = {"error": str(e)}

    return results


@mcp.tool
def get_all_employees_info() -> dict:
    """
    Return the list of all employees.

    Returns:
        dict: with this structure:
        {"ok": bool, "employees": list[dict], "error": str | None}

    Examples:
        >>> get_all_employees_info()
        {
            "ok": True,
            "employees":
            [
                {
                    "employee_id": 1001,
                    "employee_name": "Alice Johnson",
                    "dept_name": "Engineering",
                    "location": "New York, USA",
                    "employee_level": "IC5",
                    "vacation_days_taken": 15,
                },
                ...
            ],
            "error": None
        }
    """
    if DEBUG:
        logger.info("Called get_all_employees_info...")

    try:
        # in a real case we should call here HCM API
        employees = list_employees()

        # be careful the format of the output must be the same in the two branches!
        # otherwise you get a serialization error
        result = {"ok": True, "employees": employees, "error": None}
    except Exception as e:
        logger.error("Error getting data for all employees: %s", e)
        result = {"ok": False, "employees": [], "error": str(e)}

    return result


#
# Run the Employee MCP server
#
if __name__ == "__main__":
    run_server(mcp)
