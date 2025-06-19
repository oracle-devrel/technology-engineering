"""
Copyright (c) 2025, Oracle and/or its affiliates.  All rights reserved.
This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

config_manager.py
@author base: Jacco Steur
Supports Python 3 and above

coding: utf-8
"""
import yaml
import argparse
import sys

class ConfigManager:
    def __init__(self):

        if len(sys.argv) == 1:
            sys.argv.extend(['--config-file=config.yaml', '--interactive'])
            
        # Parse arguments
        self.args = self.parse_arguments()

        # Load YAML configuration if specified
        if self.args.config_file:
            self.config = self.load_yaml_config(self.args.config_file)
        else:
            self.config = {}

    def load_yaml_config(self, config_file):
        with open(config_file, 'r') as file:
            return yaml.safe_load(file)

    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="OCI Query Tool")
        parser.add_argument("--config-file", type=str, help="Path to YAML config file")
        parser.add_argument("--csv-dir", type=str, help="Directory with CSV files")
        parser.add_argument("--prefix", type=str, help="File prefix for filtering CSV files")
        parser.add_argument("--output-format", type=str, help="Output format (DataFrame, JSON, YAML)")
        parser.add_argument("--query-file", type=str, help="Path to YAML query file")
        parser.add_argument("--delimiter", type=str, help="CSV delimiter")
        parser.add_argument("--case-insensitive-headers", action="store_true", help="Convert headers to lowercase")
        parser.add_argument("--output-dir", type=str, help="Directory to save query results")
        parser.add_argument("--interactive", action="store_true", help="Enable interactive mode")
        parser.add_argument("--log-level", type=str, help="Set log level")
        parser.add_argument("--debug", action="store_true", help="Enable debug mode")
        
        parser.add_argument("--train-model", type=str, help="Path to JSON file for training the username classifier")
        # New argument for testing the model
        parser.add_argument("--test-model", type=str, help="Username to test with the classifier")
        return parser.parse_args()

    def get_setting(self, key):
        # Return CLI argument if available, otherwise fallback to config file
        return getattr(self.args, key.replace('-', '_'), None) or self.config.get(key, None)
