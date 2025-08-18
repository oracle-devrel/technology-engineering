"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

registry.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
class CommandRegistry:
    def __init__(self):
        # maps normalized command names to Command subclasses
        self._commands = {}

    def register(self, name: str, command_cls):
        """
        Register a Command subclass under a given name.
        e.g. registry.register('show tables', ShowTablesCommand)
        """
        self._commands[name.lower()] = command_cls

    def get(self, name: str):
        """
        Look up a Command subclass by name; returns None if not found.
        """
        return self._commands.get(name.lower())

    def all_commands(self):
        """
        Returns a sorted list of all registered command names.
        """
        return sorted(self._commands.keys())
