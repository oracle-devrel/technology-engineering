#!/usr/bin/env bash
#
# Run benchmarks for generic models (Llama, Grok, Gemini, GPT, etc.)
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
ENDPOINT_EU="${ENDPOINT_EU:-https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com}"
ENDPOINT_US="${ENDPOINT_US:-https://inference.generativeai.us-chicago-1.oci.oraclecloud.com}"

echo "========================================"
echo "Generic Models Benchmark"
echo "========================================"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Llama 3.3 (EU endpoint)
if [ -n "${MODEL_LLAMA_3_3:-}" ]; then
    echo ">>> Running Llama 3.3 benchmark..."
    python generic_benchmark.py \
        --model-name "llama-3.3" \
        --model-id "$MODEL_LLAMA_3_3" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_EU" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_LLAMA_3_3 not set"
fi

# Grok-3 (US endpoint)
if [ -n "${MODEL_GROK_3:-}" ]; then
    echo ">>> Running Grok-3 benchmark..."
    python generic_benchmark.py \
        --model-name "grok-3" \
        --model-id "$MODEL_GROK_3" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_US" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_GROK_3 not set"
fi

# Gemini 2.5 Pro (EU endpoint)
if [ -n "${MODEL_GEMINI_25_PRO:-}" ]; then
    echo ">>> Running Gemini 2.5 Pro benchmark..."
    python generic_benchmark.py \
        --model-name "gemini-2.5-pro" \
        --model-id "$MODEL_GEMINI_25_PRO" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_EU" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_GEMINI_25_PRO not set"
fi

# GPT 5.2 Pro (EU endpoint)
if [ -n "${MODEL_GPT_52_PRO:-}" ]; then
    echo ">>> Running GPT 5.2 Pro benchmark..."
    python generic_benchmark.py \
        --model-name "gpt-5.2-pro" \
        --model-id "$MODEL_GPT_52_PRO" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_EU" \
        --output-dir "$OUTPUT_DIR" \
        --completions \
        "$@"
else
    echo "[SKIP] MODEL_GPT_52_PRO not set"
fi

# OpenAI o4-mini (EU endpoint)
if [ -n "${MODEL_OPENAI_O4_MINI:-}" ]; then
    echo ">>> Running OpenAI o4-mini benchmark..."
    python generic_benchmark.py \
        --model-name "openai-o4-mini" \
        --model-id "$MODEL_OPENAI_O4_MINI" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_EU" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_OPENAI_O4_MINI not set"
fi

# GPT OSS 120 (EU endpoint)
if [ -n "${MODEL_GPT_OSS_120:-}" ]; then
    echo ">>> Running GPT OSS 120 benchmark..."
    python generic_benchmark.py \
        --model-name "gpt-oss-120" \
        --model-id "$MODEL_GPT_OSS_120" \
        --compartment-id "$COMPARTMENT_ID" \
        --endpoint "$ENDPOINT_EU" \
        --output-dir "$OUTPUT_DIR" \
        "$@"
else
    echo "[SKIP] MODEL_GPT_OSS_120 not set"
fi

echo ""
echo "========================================"
echo "Generic benchmarks complete!"
echo "Results in: $OUTPUT_DIR"
echo "========================================"
