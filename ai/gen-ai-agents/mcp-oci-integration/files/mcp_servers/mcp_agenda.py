"""
File name: mcp_agenda.py
Author: Luigi Saetta
Date last modified: 2025-12-04
Python Version: 3.11

Description:
    This module implements an MCP (Model Context Protocol) server for agenda and calendar management.
    It provides tools to list events overlapping with a given time interval, create new events with automatic conflict detection,
    and delete events by unique ID, using ISO date formats and structured JSON outputs for events and conflicts.

Usage:
    Import this module to use its tools or run it as a standalone MCP server.
    Example:
        from mcp_servers.mcp_agenda import create_event

        event = create_event(title="Meeting", start_date="2025-12-05T10:00:00", end_date="2025-12-05T11:00:00")
        # Or run the server: python mcp_agenda.py

License:
    This code is released under the MIT License.

Notes:
    This is part of the MCP-OCI integration framework and uses in-memory storage for events (persistent options can be added).
    Tools return dictionaries with details like event IDs, conflicts, and messages for easy integration with MCP agents.

Warnings:
    This module is in development and may change in future versions. Ensure date inputs are in valid ISO formats to avoid errors,
    and note that events are created even with conflicts—handle them appropriately in applications.
"""

from typing import List, Dict, Any, Optional
from mcp_utils import create_server, run_server
from agenda_utils import add_event, get_events, delete_event as delete_event_util
from agenda_utils import init_random_events_for_current_week

mcp = create_server("Agenda MCP")


@mcp.tool()
def list_events(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    List all events in the agenda that overlap with the given interval.

    Parameters
    ----------
    start_date : str
        Start of the desired interval.
        Accepted formats:
        - 'YYYY-MM-DDTHH:MM:SS'
        - 'YYYY-MM-DD HH:MM'
        - 'YYYY-MM-DD'
    end_date : str
        End of the desired interval.
        Same accepted formats as start_date.

    Returns
    -------
    dict
        JSON object with a single key "events":

        {
          "events": [
            {
              "id": int,
              "title": str,
              "start": str,  # ISO 8601
              "end": str,     # ISO 8601
              "notes": str
            },
            ...
          ]
        }

    Notes
    -----
    - Use the 'id' field from each event when you need to delete it.
    """
    events = get_events(start_date, end_date)

    return {"events": events}


@mcp.tool()
def create_event(
    title: str,
    start_date: str,
    end_date: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new event in the agenda and report any scheduling conflicts.

    Parameters
    ----------
    title : str
        Short human-readable title of the event.
    start_date : str
        Start of the event.
        Accepted formats:
        - 'YYYY-MM-DDTHH:MM:SS'
        - 'YYYY-MM-DD HH:MM'
        - 'YYYY-MM-DD'
    end_date : str
        End of the event.
        Must be strictly after start_date.
        Same accepted formats as start_date.
    notes : str, optional
        Optional longer description or notes for the event.

    Returns
    -------
    dict
        JSON object describing the created event and any conflicts:

        {
          "id": int,
          "title": str,
          "start": str,         # ISO 8601
          "end": str,           # ISO 8601
          "notes": str | None,
          "has_conflict": bool,
          "conflicts": [
            {
              "id": int,
              "title": str,
              "start": str,     # ISO 8601
              "end": str,        # ISO 8601
              "notes": str | None
            },
            ...
          ]
        }

    Notes
    -----
    - The event is always created, even if there are conflicts.
    - If dates are invalid or end_date <= start_date, a ValueError is raised.
    - The returned 'id' is the unique identifier to use for deletion.
    """
    return add_event(title, start_date, end_date, notes=notes)


@mcp.tool()
def delete_event(event_id: int) -> Dict[str, Any]:
    """
    Delete a single event by its unique ID.

    Parameters
    ----------
    event_id : int
        The unique identifier of the event, as returned by create_event or
        list_events (field 'id').

    Returns
    -------
    dict
        JSON-safe result object:

        {
          "deleted": bool,
          "event": {
              "id": int,
              "title": str,
              "start": str,  # ISO 8601
              "end": str,     # ISO 8601
              "notes": str | None
          } | None,
          "message": str
        }

    Notes
    -----
    - If no event with the given ID exists, 'deleted' will be False and
      'event' will be null.
    """
    return delete_event_util(event_id)


if __name__ == "__main__":
    # initialise the agenda with some random events for the current week
    init_random_events_for_current_week()

    run_server(mcp)
