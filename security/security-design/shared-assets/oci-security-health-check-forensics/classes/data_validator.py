"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

data_validator.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
class DataValidator:
    @staticmethod
    def validate_dataframe(df, required_columns):
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Warning: Missing columns {missing_columns} in DataFrame")
