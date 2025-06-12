"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

logger.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import logging

class Logger:
    def __init__(self, level='INFO'):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)

    def log(self, message, level='INFO'):
        if hasattr(self.logger, level.lower()):
            getattr(self.logger, level.lower())(message)
