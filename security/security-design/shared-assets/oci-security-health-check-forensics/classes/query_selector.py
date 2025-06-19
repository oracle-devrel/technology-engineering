"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

query_selector.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import yaml
import questionary
import queue
import os
import glob

class QuerySelector:
    def __init__(self, yaml_file=None):
        """Initialize QuerySelector with an optional YAML file path and a FIFO queue."""
        self.yaml_file = yaml_file
        self.query_queue = queue.Queue()  # Always initialize an empty FIFO queue
        self.snapshot_type = None
        self.snapshot_table = None

        if yaml_file:
            self.queries = self.load_queries()
        else:
            print("No YAML file provided. Initializing an empty queue.")
            self.queries = []  # Empty query list if no file is provided

    def load_queries(self):
        """Load queries from a YAML file and check for snapshot_type."""
        try:
            with open(self.yaml_file, "r") as file:
                data = yaml.safe_load(file)
                # Check for snapshot_type parameter
                self.snapshot_type = data.get("snapshot_type", None)
                return data.get("queries", [])
        except Exception as e:
            print(f"Error loading YAML file: {e}")
            return []

    def select_snapshot_file(self, snapshot_dir):
        """Select a snapshot file based on the snapshot_type."""
        if not self.snapshot_type:
            return None
            
        # Determine file pattern based on snapshot type
        if self.snapshot_type == "audit":
            pattern = os.path.join(snapshot_dir, "audit_events_*_*.json")
        elif self.snapshot_type == "cloudguard":
            pattern = os.path.join(snapshot_dir, "cloudguard_problems_*_*.json")
        else:
            print(f"Unknown snapshot type: {self.snapshot_type}")
            return None
            
        # Find matching files
        files = glob.glob(pattern)
        
        if not files:
            print(f"No {self.snapshot_type} snapshot files found in {snapshot_dir}")
            return None
            
        # Prepare choices with metadata
        file_choices = []
        for file_path in sorted(files, key=os.path.getmtime, reverse=True):
            filename = os.path.basename(file_path)
            stat = os.stat(file_path)
            file_size = self._format_file_size(stat.st_size)
            
            choice_text = f"{filename} ({file_size})"
            file_choices.append({
                'name': choice_text,
                'value': file_path
            })
            
        # Let user select
        selected = questionary.select(
            f"Select a {self.snapshot_type} snapshot file for queries:",
            choices=[{'name': c['name'], 'value': c['value']} for c in file_choices]
        ).ask()
        
        return selected

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 1)
        return f"{s} {size_names[i]}"

    def set_snapshot_table(self, table_name):
        """Set the snapshot table name for query substitution."""
        self.snapshot_table = table_name

    def select_queries(self):
        """Displays a list of query descriptions, allowing multiple selections, and pushes each item separately onto FIFO queue."""
        if not self.queries:
            print("No queries available.")
            return []

        # Prepare choices: Show description only
        choices = [query["description"] for query in self.queries]

        # Use questionary to allow multiple selections
        selected_descriptions = questionary.checkbox(
            "Select one or more queries:", choices=choices
        ).ask()

        for choice in selected_descriptions:
            for query in self.queries:
                if query["description"] == choice:
                    self.query_queue.put(("Description", query["description"]))
                    
                    # Substitute snapshot_table in SQL if needed
                    sql = query["sql"]
                    if self.snapshot_table and "{snapshot_data}" in sql:
                        sql = sql.replace("{snapshot_data}", self.snapshot_table)
                    
                    self.query_queue.put(("SQL", sql))
                    if query.get("filter") != None:
                        self.query_queue.put(("Filter", query.get("filter", "None")))
                    break  # Stop after adding matching query

    def dequeue_item(self):
        """Dequeues and returns the next item from the FIFO queue."""
        if not self.query_queue.empty():
            return self.query_queue.get()
        else:
            print("Queue is empty.")
            return None