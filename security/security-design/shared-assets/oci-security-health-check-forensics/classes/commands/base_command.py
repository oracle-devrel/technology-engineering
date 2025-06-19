"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

base_command.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
from abc import ABC, abstractmethod

class ShellContext:
    def __init__(self, query_executor, config_manager, logger, history, query_selector, reload_tenancy_fn=None):
        self.query_executor = query_executor
        self.config_manager = config_manager
        self.logger = logger
        self.history = history
        self.query_selector = query_selector
        self.reload_tenancy = reload_tenancy_fn

class Command(ABC):
    description = "No description available."  # Default description
    
    def __init__(self, ctx: ShellContext):
        self.ctx = ctx

    @abstractmethod
    def execute(self, args: str):
        """Perform the command; args is the raw string after the keyword."""
