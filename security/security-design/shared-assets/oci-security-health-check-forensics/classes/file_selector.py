"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

file_selector.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import os
import questionary

class FileSelector:
    def __init__(self, directory):
        """Initialize FileSelector with the given directory."""
        self.directory = directory

    def get_yaml_files(self):
        """Retrieve a list of YAML files from the specified directory."""
        if not os.path.isdir(self.directory):
            print(f"Error: The directory '{self.directory}' does not exist.")
            return []

        # List only .yaml or .yml files
        return [f for f in os.listdir(self.directory) if f.endswith((".yaml", ".yml"))]

    def select_file(self):
        """Allows the user to select a YAML file interactively."""
        yaml_files = self.get_yaml_files()

        if not yaml_files:
            print("No YAML files found in the directory.")
            return None

        # Use questionary to allow the user to select a file
        selected_file = questionary.select(
            "Select a YAML file:", choices=yaml_files
        ).ask()

        if selected_file:
            return os.path.join(self.directory, selected_file)
        return None
