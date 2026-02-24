# OCI Generative AI Safety Benchmark — Guardrails SDK & Model Refusal Testing

*A benchmark suite for evaluating LLM safety features on OCI, testing both model self-refusal behaviour and the OCI Guardrails SDK's ability to detect harmful content, PII, and prompt injection across multiple models (Cohere Command, Llama, Grok, Gemini, GPT).*

Author: Brona Nilsson

Reviewed: 12.02.2026

# When to use this asset?

*Use this asset when you need to evaluate OCI Generative AI model safety behaviour and the effectiveness of the OCI Guardrails SDK.*

### Who
- AI/ML engineers evaluating OCI Generative AI model safety
- Security teams assessing guardrails effectiveness for content moderation
- Solution architects comparing safety features across OCI-hosted models

### When
- Benchmarking model refusal rates for harmful, PII, or prompt-injection prompts
- Evaluating OCI Guardrails SDK detection accuracy (pre- and post-inference)
- Comparing safety behaviour across models (Cohere, Llama, Grok, Gemini, GPT)
- Demonstrating the added value of guardrails on top of model self-refusal

# How to use this asset?

*The asset runs benchmark prompts against OCI-hosted models and analyses the results with charts and summaries.*

1. Configure OCI credentials and model OCIDs in `.env` (see `.env.example`)
2. Run benchmarks using the provided shell scripts
3. Analyse results with the unified analysis script

See the detailed [README](files/README.md) in the `files/` folder for full setup and usage instructions.

### Key Capabilities
- Tests 5 prompt categories: harmful, PII, prompt injection, ambiguous, and edge cases
- Supports Cohere models with STRICT/CONTEXTUAL safety modes
- Measures both model refusal and OCI Guardrails SDK detection (pre- and post-inference)
- Generates 6 analysis charts and a summary report

### File Structure
```
.
├── README.md              # This file
├── LICENSE
└── files/
    ├── README.md          # Detailed setup and usage guide
    ├── cohere_benchmark.py
    ├── generic_benchmark.py
    ├── analyze_results.py
    ├── run_cohere.sh
    ├── run_generic.sh
    ├── .env.example
    ├── prompts/           # Test prompt sets
    ├── results/           # Benchmark results (CSV)
    └── charts/            # Generated visualisations
```

# Useful Links

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Generative AI Guardrails](https://docs.oracle.com/en-us/iaas/Content/generative-ai/guardrails.htm)

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
