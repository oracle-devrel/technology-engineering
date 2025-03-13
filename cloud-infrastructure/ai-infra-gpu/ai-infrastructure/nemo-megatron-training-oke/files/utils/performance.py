"""Generate a small performance report from PyTorch logs.
"""
import argparse
import re
import textwrap
import yaml
from pathlib import Path


SETTINGS_RE = re.compile(r'^\s*(devices|num_nodes|global_batch_size|encoder_seq_length): ([0-9]*)$')
TIMING_RE = re.compile(r'train_step_timing in s: \[((?:[0-9.]+(?:, )?)+)\]')


parser = argparse.ArgumentParser("calculate training performance based on log files and configuration")
parser.add_argument("logfile", type=Path, help="the log file of the training run")

args = parser.parse_args()

num_gpus = 1
num_tokens = 1

settings = set()

try:
    with args.logfile.open() as fd:
        for line in fd:
            if m := TIMING_RE.search(line):
                timings = [float(n) for n in m.group(1).split(", ")]
            elif m := SETTINGS_RE.match(line):
                setting = m.group(1)
                value = int(m.group(2))
                settings.add(setting)
                if setting in ("devices", "num_nodes"):
                    num_gpus *= value
                else:
                    num_tokens *= value
except Exception as e:
    parser.error(f"failed to parse log: {e}")

timing_avg = sum(timings) / len(timings)
throughput = num_tokens / timing_avg

print(
    textwrap.dedent(
        f"""\
        Number of GPUs: {num_gpus}
        Training step time (seconds per step): {timing_avg}
        Total token throughput per second: {throughput}
        Total token throughput per GPU per second: {throughput / num_gpus}\
        """
    )
)
