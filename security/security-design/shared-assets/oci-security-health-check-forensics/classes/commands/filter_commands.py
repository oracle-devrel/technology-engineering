"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

filter_commands.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from .base_command import Command
from classes.api_key_filter import ApiKeyFilter
from classes.compartment_structure import HCCompartmentStructure

class AgeFilterCommand(Command):
    description = """Filters results based on age in days for a specified column.
Usage: filter age <column_name> <mode> <age_days>

Modes:
- older: Show only entries older than the specified days
- younger: Show only entries younger than or equal to the specified days

The column specified by <column_name> can contain dates in the following formats:
1. Direct date strings: 'YYYY-MM-DD HH:MM:SS' or 'YYYY-MM-DD HH:MM'
2. Comma-separated lists of dates
3. OCID entries with dates (separated by spaces or colons)

Examples:
- filter age creation_date older 90    (shows entries older than 90 days)
- filter age api_keys younger 30       (shows entries 30 days old or newer)
- filter age last_modified older 60    (shows entries older than 60 days)

The command will:
1. Parse all dates found in the specified column
2. For 'older' mode: Keep only rows where any date is older than the specified number of days
3. For 'younger' mode: Keep only rows where any date is younger than or equal to the specified number of days
4. Remove rows where no valid dates are found

Note: 
- The 'older' filter shows entries strictly older than <age_days>
- The 'younger' filter shows entries equal to or newer than <age_days>
- Rows where the date column is NULL/None or contains no valid dates will be excluded from the results
- If a row contains multiple dates, it will be included if ANY of its dates match the filter criteria"""

    def execute(self, args):
        parts = args.split()
        if len(parts) != 3:
            print("Usage: filter age <column> <older|younger> <days>")
            return
        
        col, mode, days = parts
        if mode.lower() not in ['older', 'younger']:
            print("Mode must be either 'older' or 'younger'")
            return
            
        if self.ctx.last_result is None:
            print("No prior result to filter.")
            return
            
        try:
            days = int(days)
            df = ApiKeyFilter(column_name=col, age_days=days, mode=mode.lower()).filter(self.ctx.last_result)
            self.ctx.last_result = df
            fmt = self.ctx.config_manager.get_setting("output_format")
            print(__import__('classes.output_formatter').OutputFormatter.format_output(df, fmt))
        except ValueError:
            print("Days must be an integer.")

class CompartmentFilterCommand(Command):
    description = """Filters and analyzes compartment structures.
Usage: filter compartment <subcommand> [arg]
Subcommands:
- root: Show root compartment
- depth: Show maximum depth
- tree_view: Display compartment tree
- path_to <comp>: Show path to specific compartment
- subs <comp>: Show sub-compartments
- comps_at_depth <n>: Show compartments at specific depth"""

    def execute(self, args):
        parts = args.split()
        if not parts:
            print("Usage: filter compartment <subcommand> [arg]")
            return
        sub = parts[0]; param = parts[1] if len(parts)>1 else None
        if self.ctx.last_result is None or 'path' not in self.ctx.last_result.columns:
            print("No 'path' column in last result.")
            return
        inst = HCCompartmentStructure(self.ctx.last_result['path'].tolist())
        method = {
            'root': inst.get_root_compartment,
            'depth': inst.get_depth,
            'tree_view': inst.get_comp_tree,
            'path_to': lambda: inst.get_path_to(param),
            'subs': lambda: inst.get_sub_compartments(param),
            'comps_at_depth': lambda: inst.get_compartments_by_depth(int(param)),
        }.get(sub)
        if not method:
            print(f"Unknown subcommand '{sub}'.")
            return
        out = method()
        print(out)
