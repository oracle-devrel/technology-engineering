"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

directory_selector.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import os
import questionary

class DirectorySelector:
    def __init__(self, parent_dir):
        """
        Initialize with the parent directory which contains subdirectories.
        :param parent_dir: Path to the parent directory.
        """
        if not os.path.isdir(parent_dir):
            raise ValueError(f"Provided path '{parent_dir}' is not a directory.")
        self.parent_dir = os.path.abspath(parent_dir)
        self.new_snapshot = "Create new snapshot of tenancy"


    def list_subdirectories(self):
        """
        List all subdirectories in the parent directory sorted by creation time (newest first).
        :return: A list of subdirectory names.
        """
        subdirs = [
            name for name in os.listdir(self.parent_dir)
            if os.path.isdir(os.path.join(self.parent_dir, name))
        ]
        
        # Sort by creation time, newest first
        subdirs.sort(key=lambda name: os.path.getctime(os.path.join(self.parent_dir, name)), reverse=True)
        return subdirs

    def select_directory(self):
        """
        Prompts the user to select a subdirectory using questionary.
        :return: The full path to the selected subdirectory or None if no selection is made.
        """
        subdirs = self.list_subdirectories()
        if not subdirs:
            print(f"No subdirectories found in {self.parent_dir}")
            return None

        # Prompt the user to select one of the subdirectories.
        subdirs.append(self.new_snapshot)
        selected = questionary.select(
            "Select a directory or create a new snapshot from the tenancy using showoci:",
            choices=subdirs
        ).ask()

        if selected is None:
            # User cancelled the selection.
            return None
        
        if selected == self.new_snapshot:
            return selected
        
        # Return the full directory path.
        return os.path.join(self.parent_dir, selected)
    
    def get_new_snapshot(self):
        return self.new_snapshot