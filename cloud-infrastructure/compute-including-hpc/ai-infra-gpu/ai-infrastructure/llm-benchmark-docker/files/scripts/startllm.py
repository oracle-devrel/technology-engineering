#!/usr/bin/env python3
# Copyright (c) 2025 Oracle and/or its affiliates.
import argparse
import json
import logging
import subprocess

from pathlib import Path

parser = argparse.ArgumentParser("Start a LLM")
parser.add_argument(
    "--port",
    type=int,
    default=30000,
    help="Port to use for sglang.",
)
parser.add_argument(
    "server_configuration",
    type=Path,
    default="config.json",
    nargs="?",
    help="The server configuration to use",
)
args = parser.parse_args()

with args.server_configuration.open() as fd:
    configuration = json.load(fd)

# Remove performance measurement parameters
configuration.pop("genai-perf", None)

model = configuration.pop("model")
server_command = [
    "python3",
    "-m",
    "sglang.launch_server",
    "--log-requests-level",
    "0",
    "--host=0.0.0.0",
    f"--port={args.port}",
    "--model-path",
    model,
] + [
    f"--{k}={v}" for k, v in configuration.items()
]
logging.warning("running: %s", " ".join(server_command))
subprocess.check_call(server_command)
