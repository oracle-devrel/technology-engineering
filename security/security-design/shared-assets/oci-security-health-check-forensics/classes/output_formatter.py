"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

output_formatter.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import pandas as pd
import json

class OutputFormatter:
    @staticmethod
    def format_output(data, output_format="DataFrame"):
        if data is None:
            return "No data to display"
            
        try:
            if isinstance(data, pd.DataFrame):
                with pd.option_context('display.max_rows', None,
                                     'display.max_columns', None,
                                     'display.width', 1000):
                    return str(data)
            elif isinstance(data, (list, tuple)):
                return "\n".join(map(str, data))
            elif isinstance(data, dict):
                return "\n".join(f"{k}: {v}" for k, v in data.items())
            else:
                return str(data)
        except Exception as e:
            return f"Error formatting output: {str(e)}"