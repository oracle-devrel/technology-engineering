"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

csv_loader_duckdb.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import duckdb
import pandas as pd
import os
import re

class CSVLoaderDuckDB:
    def __init__(self, csv_dir, prefix="csve", delimiter=',', case_insensitive_headers=False):
        self.csv_dir = csv_dir
        self.prefix = prefix  # No auto-underscore to allow flexibility
        self.delimiter = delimiter
        self.case_insensitive_headers = case_insensitive_headers
        self.conn = duckdb.connect(database=':memory:')  # In-memory DuckDB connection

    def load_csv_files(self):
        for filename in os.listdir(self.csv_dir):
            if filename.endswith(".csv") and filename.startswith(self.prefix):  # Ensure prefix check
                # Remove only the prefix from the beginning, keeping the rest intact
                table_name = filename[len(self.prefix):].removeprefix("_").removesuffix(".csv")

                # Ensure valid DuckDB table name
                table_name = table_name.replace("-", "_").replace(" ", "_")
                table_name = f'"{table_name}"'  # Quote it to allow special characters

                print(f"Loading CSV file into DuckDB: {filename} as {table_name}")

                # Read CSV into pandas DataFrame
                df = pd.read_csv(os.path.join(self.csv_dir, filename), delimiter=self.delimiter)

                # Replace dots in headers with underscores
                df.columns = [re.sub(r'[.-]', '_', col) for col in df.columns]

                # Optionally convert headers to lowercase
                if self.case_insensitive_headers:
                    df.columns = [col.lower() for col in df.columns]

                # Register DataFrame in DuckDB
                self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM df")

    def query(self, sql):
        return self.conn.execute(sql).fetchdf()  # Fetch result as a pandas DataFrame
