"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

command_parser.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
class CommandParser:
    ALIASES = {
        'ls': 'show tables',
        'desc': 'describe',
        '!': 'history',
    }

    def __init__(self, registry):
        self.registry = registry

    def parse(self, user_input: str) -> (str, str):
        text = user_input.strip()
        if not text:
            return None, None

        # 1) apply any aliases
        for alias, full in self.ALIASES.items():
            if text == alias or text.startswith(alias + ' '):
                text = text.replace(alias, full, 1)
                break

        text_lower = text.lower()

        # 2) try to match one of the registered multi‑word commands
        #    (longest first so “show tables” wins over “show”)
        for cmd in sorted(self.registry.all_commands(), key=len, reverse=True):
            if text_lower.startswith(cmd):
                args = text[len(cmd):].strip()
                return cmd, args

        # 3) nothing matched → treat the *entire* line as SQL
        return '<default>', text
