"""
MCP Server to query data regarding OCI usage and consumption
"""

from typing import Any, Dict

# here is the function that calls Select AI
from consumption_utils import (
    usage_summary_by_service_structured,
    usage_summary_by_compartment_structured,
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
    Return the consumption aggregated by service.

    Args:
        start_date: start date of the period. Format: YYYY-MM-DD
        end_date: end date of the period. Format: YYYY-MM-DD

    Returns:
        a structure with details of consumption.

    """
    if DEBUG:
        logger.info("Called generate_sql...")

    try:
        results = usage_summary_by_service_structured(start_date, end_date)
    except Exception as e:
        logger.error("Error generating consumption: %s", e)
        results = {"error": str(e)}

    return results


@mcp.tool
def usage_summary_by_compartment(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Return the consumption aggregated by compartment.

    Args:
        start_date: start date of the period. Format: YYYY-MM-DD
        end_date: end date of the period. Format: YYYY-MM-DD

    Returns:
        a structure with details of consumption.

    """
    if DEBUG:
        logger.info("Called generate_sql...")

    try:
        results = usage_summary_by_compartment_structured(start_date, end_date)
    except Exception as e:
        logger.error("Error generating consumption: %s", e)
        results = {"error": str(e)}

    return results


#
# Run the Select AI MCP server
#
if __name__ == "__main__":
    run_server(mcp)
