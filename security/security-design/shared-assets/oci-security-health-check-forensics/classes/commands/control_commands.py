"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

control_commands.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from .base_command import Command
from classes.file_selector import FileSelector
from classes.query_selector import QuerySelector
from classes.output_formatter import OutputFormatter
from classes.commands.filter_commands import AgeFilterCommand, CompartmentFilterCommand

class SetQueriesCommand(Command):
    """
    Usage: set queries [<directory>]
    Launches an interactive YAML-file picker and loads the selected queries.
    """
    description = """Loads queries from a YAML file for batch execution.
Usage: set queries [directory]
- If directory is not specified, uses default query directory
- Opens an interactive file picker to select the YAML file
- Loads selected queries into the execution queue"""

    def execute(self, args: str):
        # allow optional override of query-directory via args
        directory = args or self.ctx.config_manager.get_setting("query_dir") or "query_files"
        selector = FileSelector(directory)
        yaml_path = selector.select_file()
        if not yaml_path:
            print("No YAML file selected.")
            return

        qs = QuerySelector(yaml_path)
        qs.select_queries()
        self.ctx.query_selector = qs
        print(f"Loaded queries from '{yaml_path}' into queue.")

class SetTenancyCommand(Command):
    """
    Usage: set tenancy
    Re‑runs the tenancy‑selection & CSV loading flow, replacing the active QueryExecutor.
    """
    description = """Changes the active tenancy and reloads CSV data.
Usage: set tenancy
- Prompts for tenancy selection
- Reloads CSV files for the selected tenancy
- Updates the query executor with new data"""

    def execute(self, args: str):
        if not callable(self.ctx.reload_tenancy):
            print("Error: tenancy reload not configured.")
            return
        new_executor = self.ctx.reload_tenancy()

        if new_executor:
            self.ctx.query_executor = new_executor
            self.ctx.last_result = None
            print("Switched to new tenancy data.")
        else:
            print("Failed to change tenancy.")

class RunQueriesCommand(Command):
    """
    Usage: run queries
    Executes all queries loaded by `set queries` in FIFO order.
    """
    description = """Executes all queries that were loaded using 'set queries'.
Usage: run queries
- Executes queries in FIFO order
- Displays results after each query
- Can include both SQL queries and filter operations"""

    def execute(self, args: str):
        qs = self.ctx.query_selector
        if not qs or qs.query_queue.empty():
            print("No queries loaded (or queue is empty).")
            return

        while True:
            item = qs.dequeue_item()
            if not item:
                break
            kind, val = item

            if kind == "Description":
                print(f"\n== {val} ==")

            elif kind == "SQL":
                print(f"Running SQL: {val}")
                df = self.ctx.query_executor.execute_query(val)
                if df is not None:
                    # store for potential filtering
                    self.ctx.last_result = df
                    fmt = self.ctx.config_manager.get_setting("output_format") or "dataframe"
                    # use the imported OutputFormatter
                    print(OutputFormatter.format_output(df, fmt))

            elif kind == "Filter":
                # val is something like "age api_keys 90" or "compartment tree_view"
                parts = val.split()
                filter_type = parts[0]               # "age" or "compartment"
                filter_args = " ".join(parts[1:])    # e.g. "api_keys 90"

                cmd_key = f"filter {filter_type}"
                cmd_cls = self.ctx.registry.get(cmd_key)
                if not cmd_cls:
                    print(f"Unknown filter command '{cmd_key}'")
                    continue

                # instantiate and run the filter command
                cmd = cmd_cls(self.ctx)
                cmd.execute(filter_args)
