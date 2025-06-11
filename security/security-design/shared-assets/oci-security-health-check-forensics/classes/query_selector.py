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

class QuerySelector:
    def __init__(self, yaml_file=None):
        """Initialize QuerySelector with an optional YAML file path and a FIFO queue."""
        self.yaml_file = yaml_file
        self.query_queue = queue.Queue()  # Always initialize an empty FIFO queue

        if yaml_file:
            self.queries = self.load_queries()
        else:
            print("No YAML file provided. Initializing an empty queue.")
            self.queries = []  # Empty query list if no file is provided

    def load_queries(self):
        """Load queries from a YAML file."""
        try:
            with open(self.yaml_file, "r") as file:
                data = yaml.safe_load(file)
                return data.get("queries", [])
        except Exception as e:
            print(f"Error loading YAML file: {e}")
            return []

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
                    self.query_queue.put(("SQL", query["sql"]))
                    if query.get("filter") != None:
                        self.query_queue.put(("Filter", query.get("filter", "None")))  # Return filter as-is
                    break  # Stop after adding matching query

    def dequeue_item(self):
        """Dequeues and returns the next item from the FIFO queue."""
        if not self.query_queue.empty():
            return self.query_queue.get()
        else:
            print("Queue is empty.")
            return None


