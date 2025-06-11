"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

command_history.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import readline
import os
from typing import Optional, List
from .exceptions import ArgumentError

class CommandHistory:
    def __init__(self, history_file: str = ".sql_history"):
        """Initialize command history manager"""
        self.history_file = os.path.expanduser(history_file)
        self.load_history()

    def load_history(self):
        """Load command history from file"""
        try:
            readline.read_history_file(self.history_file)
        except FileNotFoundError:
            # Create history file if it doesn't exist
            self.save_history()

    def save_history(self):
        """Save command history to file"""
        try:
            readline.write_history_file(self.history_file)
        except Exception as e:
            print(f"Warning: Could not save command history: {e}")

    def add(self, command: str):
        """Add a command to history"""
        if command and command.strip():  # Only add non-empty commands
            readline.add_history(command)
            self.save_history()  # Save after each command for persistence

    def get_history(self, limit: Optional[int] = None) -> List[str]:
        """Get list of commands from history"""
        history = []
        length = readline.get_current_history_length()
        start = max(1, length - (limit or length))
        
        for i in range(start, length + 1):
            cmd = readline.get_history_item(i)
            if cmd:  # Only add non-None commands
                history.append((i, cmd))
        return history

    def get_command(self, reference: str) -> str:
        """
        Get a command from history using reference (e.g., !4 or !-1)
        Returns the resolved command
        """
        try:
            # Remove the '!' from the reference
            ref = reference.lstrip('!')
            
            # Handle negative indices
            if ref.startswith('-'):
                index = readline.get_current_history_length() + int(ref)
            else:
                index = int(ref)

            # Get the command
            command = readline.get_history_item(index)
            
            if command is None:
                raise ArgumentError(f"No command found at position {ref}")
                
            return command
            
        except ValueError:
            raise ArgumentError(f"Invalid history reference: {reference}")
        except Exception as e:
            raise ArgumentError(f"Error accessing history: {e}")

    def show_history(self, limit: Optional[int] = None):
        """Display command history"""
        history = self.get_history(limit)
        if not history:
            print("No commands in history.")
            return
            
        print("\nCommand History:")
        for index, command in history:
            print(f"{index}: {command}")