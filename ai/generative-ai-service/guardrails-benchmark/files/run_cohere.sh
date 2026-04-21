#!/usr/bin/env bash
#
# Run benchmarks for Cohere models (STRICT/CONTEXTUAL modes)
#
set -euo pipefail

# Activate virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

OUTPUT_DIR="${OUTPUT_DIR:-results_v2}"
ENDPOINT="${ENDPOINT_EU:-https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com}"

echo "========================================"
echo "Cohere Models Benchmark"
echo "========================================"
echo "Output directory: $OUTPUT_DIR"
echo "Endpoint: $ENDPOINT"
echo ""

# Command-R+
if [ -n "${MODEL_COHERE_COMMAND_R_PLUS:-}" ]; then
    echo ">>> Running Command-R+ benchmark..."
    python cohere_benchmark.py \
        --model-name "command-r-plus" \
        --model-id "$MODEL_COHERE_COMMAND_R_PLUS" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_COHERE_COMMAND_R_PLUS not set"
fi

# Command-A
if [ -n "${MODEL_COHERE_COMMAND_A:-}" ]; then
    echo ">>> Running Command-A benchmark..."
    python cohere_benchmark.py \
        --model-name "command-a" \
        --model-id "$MODEL_COHERE_COMMAND_A" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_COHERE_COMMAND_A not set"
fi

# Command-Vision (placeholder)
if [ -n "${MODEL_COHERE_COMMAND_VISION:-}" ]; then
    echo ">>> Running Command-Vision benchmark..."
    python cohere_benchmark.py \
        --model-name "command-vision" \
        --model-id "$MODEL_COHERE_COMMAND_VISION" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_COHERE_COMMAND_VISION not set"
fi

echo ""
echo "========================================"
echo "Cohere benchmarks complete!"
echo "Results in: $OUTPUT_DIR"
echo "========================================"
