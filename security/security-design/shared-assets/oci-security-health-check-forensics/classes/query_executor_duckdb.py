"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

query_executor_duckdb.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import duckdb

class QueryExecutorDuckDB:
    def __init__(self, conn):
        self.conn = conn  # DuckDB connection

    def execute_query(self, query):
        try:
            result = self.conn.execute(query).fetchdf()
            return result
        except Exception as e:
            print(f"Error executing query: {e}")
            return None

    def show_tables(self):
        """Use DuckDB's SHOW TABLES command to list all tables."""
        result = self.conn.execute("SHOW TABLES").fetchall()
        return [row[0] for row in result]

    def describe_table(self, table_name):
        """Use DuckDB's DESCRIBE command to get column names and types."""
        try:
            result = self.conn.execute(f"DESCRIBE {table_name}").fetchall()
            return [(row[0], row[1]) for row in result]
        except Exception as e:
            print(f"Error describing table '{table_name}': {e}")
            return None
