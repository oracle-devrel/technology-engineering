#!/bin/bash
set -euo pipefail

unset -v CHART_PATH

while getopts p: flag; do
  case "${flag}" in
    p) CHART_PATH=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${CHART_PATH:-}" ]; then
  echo "Missing chart path parameter" >&2
  exit 1
fi

if [ ! -f "${CHART_PATH}/Chart.yaml" ]; then
  echo "Chart.yaml not found at ${CHART_PATH}" >&2
  exit 1
fi

python3 - "$CHART_PATH/Chart.yaml" <<'PY'
import sys
from pathlib import Path

for line in Path(sys.argv[1]).read_text().splitlines():
    if line.startswith("version:"):
        version = line.split(":", 1)[1].strip().strip("\"'")
        if version:
            print(version)
            sys.exit(0)

print("Chart.yaml is missing a top-level version", file=sys.stderr)
sys.exit(1)
PY
