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
    default=8000,
    help="Port to use for vLLM.",
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

model = configuration.pop("model")
server_command = [
    "vllm",
    "serve",
    "--disable-log-requests",
    f"--port={args.port}",
    model,
] + [
    f"--{k}={v}" for k, v in configuration.items()
]
logging.warning("running: %s", " ".join(server_command))
subprocess.check_call(server_command)
