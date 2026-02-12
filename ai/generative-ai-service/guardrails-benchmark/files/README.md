# OCI Generative AI Safety Benchmark

Benchmark suite for testing LLM safety features and OCI Guardrails SDK efficacy.

## Overview

This benchmark tests:
1. **Model refusal behavior** - How well models refuse harmful prompts
2. **OCI Guardrails SDK** - Detection of harmful content, PII, and prompt injection

## Quick Start

```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your OCI model OCIDs and compartment ID

# 2. Install dependencies
python -m venv venv
source venv/bin/activate
pip install oci pandas python-dotenv openpyxl

# 3. Run benchmarks
./run_generic.sh      # Llama, Grok, Gemini, GPT models
./run_cohere.sh       # Cohere models (with STRICT/CONTEXTUAL modes)

# 4. Analyze results
python analyze_results.py
```

## Project Structure

```
.
├── cohere_benchmark.py      # Cohere models (STRICT/CONTEXTUAL modes)
├── generic_benchmark.py     # All other models (Llama, Grok, Gemini, GPT)
├── run_cohere.sh           # Run all Cohere models
├── run_generic.sh          # Run all generic models
├── analyze_results.py             # Unified analysis: charts + summary for refusal & guardrails
├── .env                    # Model IDs and configuration (not committed)
├── .env.example            # Template for .env
├── prompts/                # Test prompt sets
│   ├── harmful_prompts.py
│   ├── pii_prompts.py
│   ├── promptinjection_prompts.py
│   ├── ambiguous_prompts.py
│   └── edge_cases_prompts.py
├── results/                # Benchmark results (CSV)
├── results_v2/             # Benchmark results v2 (CSV)
└── charts*/                # Generated visualizations
```

## Configuration

### .env File

```bash
# OCI Configuration
COMPARTMENT_ID=ocid1.compartment.oc1..xxxxx
OCI_PROFILE=DEFAULT

# Endpoints
ENDPOINT_EU=https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com
ENDPOINT_US=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com

# Model OCIDs
MODEL_COHERE_COMMAND_R_PLUS=ocid1.generativeaimodel.oc1...
MODEL_LLAMA_3_3=ocid1.generativeaimodel.oc1...
MODEL_GROK_3=ocid1.generativeaimodel.oc1...
# ... etc
```

## Running Benchmarks

### Full Benchmark
```bash
./run_generic.sh    # All generic models
./run_cohere.sh     # All Cohere models
```

### Test Mode (2 prompts per set)
```bash
./run_generic.sh --test
./run_cohere.sh --test
```

### Single Model
```bash
python generic_benchmark.py \
    --model-name "my-model" \
    --model-id "ocid1.generativeaimodel..." \
    --compartment-id "$COMPARTMENT_ID" \
    --endpoint "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com"
```

### Options

| Flag | Description |
|------|-------------|
| `--test` | Run only 2 prompts per set |
| `--overwrite` | Overwrite existing result files |
| `--skip-guardrails` | Skip OCI guardrails calls (model-only) |
| `--skip-model` | Skip model inference (guardrails-only) |
| `--output-dir DIR` | Output directory (default: results_v2) |

## Adding New Prompts

Create a new file in `prompts/` following this pattern:

```python
# prompts/my_prompts.py

my_prompts = [
    "First test prompt...",
    "Second test prompt...",
    # Add more prompts
]
```

The benchmark automatically discovers all `*_prompts.py` files and variables ending with `_prompts`.

## Adding New Models

1. Add the model OCID to `.env`:
   ```bash
   MODEL_MY_NEW_MODEL=ocid1.generativeaimodel.oc1...
   ```

2. Add to the appropriate run script (`run_generic.sh` or `run_cohere.sh`):
   ```bash
   if [ -n "${MODEL_MY_NEW_MODEL:-}" ]; then
       python generic_benchmark.py \
           --model-name "my-new-model" \
           --model-id "$MODEL_MY_NEW_MODEL" \
           --compartment-id "$COMPARTMENT_ID" \
           --endpoint "$ENDPOINT_EU" \
           --output-dir "$OUTPUT_DIR" \
           "$@"
   fi
   ```

## Output Format

Results are saved as CSV with these columns:

| Column | Description |
|--------|-------------|
| `Prompt` | The test prompt |
| `Model` | Model name |
| `Mode` | Safety mode (Cohere only: STRICT/CONTEXTUAL) |
| `Refused` | Did model refuse? (yes/no/error) |
| `LatencyMs` | Response time in milliseconds |
| `ModelOutput` | Model's response |
| `Pre_OCIFlagged` | Guardrails flagged the prompt? (yes/no) |
| `Pre_FlaggedCategories` | Categories detected in prompt |
| `Pre_DetectedPIITypes` | PII types found in prompt |
| `Pre_PromptInjectionScore` | Prompt injection score (0-1) |
| `Post_OCIFlagged` | Guardrails flagged the response? (yes/no) |
| `Post_*` | Same fields for model response |

## Analyzing Results

A single script produces all charts and a printed summary:

```bash
python analyze_results.py                          # auto-detects results dir
python analyze_results.py --results-dir results_v2 # explicit dir
python analyze_results.py --output-dir my_charts   # custom output dir
```

Generates 6 charts:
1. Model self-refusal rate by model
2. Guardrails detection rate by model (Guardrails ON only)
3. Guardrails detection rate by prompt type
4. Model refusal vs Guardrails vs Combined comparison
5. Pre (prompt) vs Post (response) guardrails detection
6. Combined blocked-rate heatmap by model and prompt type

## Key Findings

The OCI Guardrails SDK detects:
- **PII**: ~80-86% detection (names, addresses, emails)
- **Prompt Injection**: ~70-75% detection
- **Violence**: Explicit violence keywords only (~15%)
- **Other harmful content**: Limited detection for drugs, CSAM, terrorism, etc.

The guardrails add value on top of model refusals:
- Model refusal alone: ~20-25%
- Guardrails detection alone: ~45-55%
- Combined (either): ~50-65%

## Requirements

- Python 3.11+
- OCI CLI configured (`~/.oci/config`)
- OCI Generative AI access with model deployments

## Dependencies

```
oci
pandas
python-dotenv
openpyxl
matplotlib
```
