#!/usr/bin/env python3
# Copyright (c) 2025 Oracle and/or its affiliates.
import argparse
import datetime
import json
import logging
import os
import requests
import shutil
import subprocess
import sys
import time

from pathlib import Path

MIN_THROUGHPUT_PER_REQUEST = 10.0
NUM_REQUEST_MULTIPLIER = 30
NUM_REQUEST_FOR_WARMUP = 3

SCENARIOS = {
    "chatbot": {
        "synthetic-input-tokens-mean": 100,
        "synthetic-input-tokens-stddev": 10,
        "output-tokens-mean": 100,
        "output-tokens-stddev": 10,
    },
    "gen_light": {
        "synthetic-input-tokens-mean": 100,
        "synthetic-input-tokens-stddev": 10,
        "output-tokens-mean": 350,
        "output-tokens-stddev": 50,
    },
    "gen_heavy": {
        "synthetic-input-tokens-mean": 100,
        "synthetic-input-tokens-stddev": 10,
        "output-tokens-mean": 1000,
        "output-tokens-stddev": 100,
    },
    "rag": {
        "synthetic-input-tokens-mean": 2000,
        "synthetic-input-tokens-stddev": 200,
        "output-tokens-mean": 100,
        "output-tokens-stddev": 10,
    },
}


def get_shape():
	"""Query for the current machine's shape."""
	url = "http://169.254.169.254/opc/v2/instance/"
	headers = {"Authorization": "Bearer Oracle"}
	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		data = response.json()
		return data.get("shape")

parser = argparse.ArgumentParser("Benchmark a LLM")
parser.add_argument(
    "--concurrency-multiplier",
    type=int,
    default=NUM_REQUEST_MULTIPLIER,
    help="Number to multiply concurrency with to get total requests for LLM",
)
parser.add_argument(
    "--concurrency",
    type=int,
    nargs="+",
    default=[1, 2, 4, 8, 16, 32, 64, 128, 256, 512],
    help="Concurrenct request(s) to benchmark",
)
parser.add_argument(
    "--scenario",
    type=str,
    nargs="+",
    default=sorted(k for k in SCENARIOS.keys() if k != "gen_light"),
    help="Which scenario(s) to benchmark",
)
parser.add_argument(
    "--output",
    type=Path,
    default=Path("results/"),
    help="Where to store the results",
)
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
    server_configuration = json.load(fd)

shape = get_shape()
logging.warning(f"started on {shape}")

model_name = server_configuration["model"].rsplit("/", 1)[-1]
model_stub = model_name.lower()

benchmark_command = [
    "genai-perf",
    "profile",
    "--service-kind=openai",
    "--endpoint-type=chat",
    "--streaming",
    f"--model={server_configuration['model']}",
    f"--tokenizer={server_configuration['model']}",
    "-u",
    f"http://llm:{args.port}",
]


timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
tmpdir = Path("/") / "mnt" / "localdisk"
if not tmpdir.exists():
    tmpdir = args.output

tmp_outdir = tmpdir  / f"tmp_{os.environ.get('SLURM_JOBID', timestamp)}"

for scenario in args.scenario:
    for concurrency in args.concurrency:
        outstub = f"{model_stub}_{scenario}_{concurrency}"
        scfg = SCENARIOS[scenario]

        # Note:
        # according to https://github.com/vllm-project/vllm/issues/1351, some
        # models may consider token count to be the total of input _and_
        # output.
        #
        # tokens_mean = sum(v for k, v in scfg.items() if k.endswith("mean"))
        # tokens_stddev = sum(v for k, v in scfg.items() if k.endswith("stddev"))
        tokens_mean = scfg["output-tokens-mean"]
        tokens_stddev = scfg["output-tokens-stddev"]

        cmd = benchmark_command + [
            f"--artifact-dir={tmp_outdir}",
            f"--profile-export-file={outstub}.json",
            f"--concurrency={concurrency}",
            f"--num-prompts={min(args.concurrency_multiplier * concurrency, 10_000)}",  # Default is only 100
            f"--num-requests={args.concurrency_multiplier * concurrency}",
            f"--extra-inputs=max_tokens:{tokens_mean + tokens_stddev}",
            f"--extra-inputs=min_tokens:{tokens_mean - tokens_stddev}",
        ] + [
            f"--{k}={v}" for k, v in scfg.items()
        ]

        logging.warning("running: %s", " ".join(cmd))
        subprocess.check_call(cmd)

        with (tmp_outdir / f"{outstub}_genai_perf.json").open() as fd:
            data = json.load(fd)

        data["server_configuration"] = server_configuration
        data["scenario"] = {
            k.replace("-", "_"): v for k, v in SCENARIOS[scenario].items()
        } | {
            "use_case": scenario,
            "concurrency": concurrency,
            "model": model_name,
            "shape": shape,
        }

        with (args.output / f"{outstub}_{timestamp}.json").open("w") as fd:
            json.dump(data, fd)

        # We don't want to run any longer if the token throughput per request is too low
        if data["output_token_throughput_per_request"]["avg"] < MIN_THROUGHPUT_PER_REQUEST:
            break

shutil.rmtree(tmp_outdir)

logging.warning("ALL DONE")
