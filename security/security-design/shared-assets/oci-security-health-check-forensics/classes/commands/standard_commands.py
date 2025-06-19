"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

standard_commands.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from .base_command import Command
from classes.output_formatter import OutputFormatter


class ShowTablesCommand(Command):
    description = "Lists all available tables in the current database.\nUsage: show tables"

    def execute(self, args):
        tables = self.ctx.query_executor.show_tables()
        print("Available tables:")
        for t in tables:
            print(f"  - {t}")

class DescribeCommand(Command):
    description = "Shows the structure of a table, including column names and types.\nUsage: describe <table_name>"

    def execute(self, args):
        if not args:
            print("Usage: describe <table_name>")
            return
        info = self.ctx.query_executor.describe_table(args)
        if not info:
            print(f"Table '{args}' not found.")
        else:
            print(f"Columns in '{args}':")
            for name, typ in info:
                print(f"  - {name}: {typ}")

class ExecuteSqlCommand(Command):
    description = "Executes a SQL query and displays the results.\nUsage: <sql_query>"
    """Fallback for unrecognized commands: treat as SQL."""
    def execute(self, args):
        sql = args.strip()
        if not sql:
            return

        # log directly (no print around it)
        self.ctx.logger.log(f"Running SQL: {sql}", level="DEBUG")

        # execute the query
        df = self.ctx.query_executor.execute_query(sql)
        if df is not None:
            self.ctx.last_result = df

            fmt = self.ctx.config_manager.get_setting("output_format") or "dataframe"
            self.ctx.logger.log(f"Formatting output as {fmt}", level="DEBUG")

            # format and print the result
            output = OutputFormatter.format_output(df, fmt)
            print(output)

class ExitCommand(Command):
    description = "Exits the application.\nUsage: exit (or quit)"

    def execute(self, args):
        print("Bye.")
        raise SystemExit

class HistoryCommand(Command):
    description = """Shows command history.
Usage: history
- Shows all previously executed commands with their index numbers
- Use !n to re-run command number n from history
- Use !-n to re-run nth previous command"""

    def execute(self, args: str):
        # Fetch the list of (index, command) tuples
        history_items = self.ctx.history.get_history()
        if not history_items:
            print("No commands in history.")
            return

        print("\nCommand History:")
        for idx, cmd in history_items:
            print(f"{idx}: {cmd}")
class HelpCommand(Command):
    description = "Show help for available commands. Usage: help [command]"
    
    def execute(self, args):
        if not args:
            # Show all commands
            print("Available commands:")
            for name in self.ctx.registry.all_commands():
                cmd_cls = self.ctx.registry.get(name)
                brief_desc = cmd_cls.description.split('\n')[0]  # First line only
                print(f"  - {name:<20} - {brief_desc}")
            print("\nType 'help <command>' for detailed help on a specific command.")
        else:
            # Show help for specific command
            cmd_name = args.lower()
            cmd_cls = self.ctx.registry.get(cmd_name)
            if not cmd_cls:
                print(f"Unknown command: {cmd_name}")
                return
            
            print(f"\nHelp for '{cmd_name}':")
            print(f"\n{cmd_cls.description}")

class FilterCommand(Command):
    def __init__(self, query_executor, original_result=None):
        self.query_executor = query_executor
        self.original_result = original_result

    def execute(self, args: str, **kwargs):
        if self.original_result is None:
            print("No results to filter. Run a query first.")
            return

        try:
            filter_parts = args.strip().lower().split()
            if not filter_parts:
                print("Invalid filter command. Usage: filter <type> <args>")
                return

            filter_type = filter_parts[0]
            filter_args = filter_parts[1:]

            if filter_type == 'age':
                return self._handle_age_filter(filter_args)
            else:
                print(f"Unknown filter type: {filter_type}")

        except Exception as e:
            print(f"Error executing filter: {str(e)}")

    def _handle_age_filter(self, args):
        if len(args) != 2:
            print("Invalid age filter command. Usage: filter age <column_name> <age_days>")
            return

        column_name, age_days = args
        try:
            age_days = int(age_days)
            from ..api_key_filter import ApiKeyFilter
            
            api_key_filter = ApiKeyFilter(column_name=column_name, age_days=age_days)
            result = api_key_filter.filter(self.original_result.copy())
            
            if result is not None and not result.empty:
                print(OutputFormatter.format_output(result))
            else:
                print("No records found after applying the filter.")
        except ValueError:
            print("Age must be a number")
        except Exception as e:
            print(f"Error applying age filter: {str(e)}")
