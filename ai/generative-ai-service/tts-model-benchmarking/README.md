# TTS Model Benchmarking on OCI Generative AI

*A benchmark toolkit for text-to-speech models hosted on OCI Generative AI (imported models such as OmniVoice on a dedicated AI cluster, or on-demand models on the same speech route). It measures time to first audio, end-to-end latency, real-time factor, throughput and error rate under concurrency, with and without streaming, in English and Arabic, and scores intelligibility with Whisper to find the input length at which single-pass synthesis degrades.*

Author: Brona Nilsson

Reviewed: 05.10.2026

# When to use this asset?

*Use this asset when you need numbers, not impressions, about a TTS endpoint on OCI: how fast it answers, how much load one hosting unit takes, and whether long inputs stay intelligible.*

### Who
- Data scientists and ML engineers evaluating a TTS model in an OCI Data Science notebook session
- Solution architects sizing a dedicated AI cluster (A10, A100, H100) for a voice workload
- Teams comparing hosting shapes, model versions or serving-stack upgrades with repeatable runs

### When
- Choosing a hosting shape: run the same suites on each shape and compare the CSVs
- Designing a voice application: pick streaming vs chunking from measured TTFA, not guesswork
- Validating a fix: OmniVoice served through vLLM-Omni on OCI garbles speech past ~30 s per request; the `long-text` suite shows the breaking point as a WER curve and confirms when an upgrade removes it
- Capacity planning: the concurrency sweep finds the knee where latency climbs and throughput flattens

# How to use this asset?

*Point the scripts at an endpoint, run a suite, read the report.*

1. `pip install -r files/requirements.txt`, copy `files/.env.example` to `files/.env` and set the endpoint and compartment OCIDs. In a Data Science notebook session the resource principal is picked up automatically.
2. `python files/tts_bench.py --suite quick --label <shape>` for a two-minute smoke test, then `--suite latency`, `--suite long-text`, `--suite concurrency` or `--suite full`.
3. `python files/wer.py results/<run>` to score the saved clips for intelligibility, and `python files/plots.py results/<run>` for charts. Or open `files/notebook/tts_benchmark.ipynb` and run the cells.

See the detailed [README](files/README.md) in the `files/` folder for setup on each platform, the metric definitions, the suites, reference numbers from an H100_X1 cluster and troubleshooting.

### Key Capabilities
- Industry-standard serving metrics: TTFA, E2E, RTF, p50/p90/p95/p99, error rate, requests per minute and audio seconds per second
- Three request modes: synchronous, streaming, and client-side sentence chunking (the workaround for long inputs)
- Closed-loop concurrency sweep (1, 2, 4, 8, 16 parallel requests) to find the capacity of one hosting unit
- Target durations in seconds (10 to 60 s) with per-language calibration of characters per second, so English and Arabic are compared at equal speech length
- Whisper-based WER/CER scoring with Arabic normalisation; CPU, CUDA or Apple Silicon backends
- Constant voice across all requests through a bundled synthetic reference clip; voice design and preset-voice modes for other models
- Works with API key, resource principal, instance principal, session token or bearer-key auth
- CSV, Markdown report, sample audio and PNG charts per run; runs are labelled by shape for side-by-side comparison

### File Structure
```
.
├── README.md                     # This file
├── LICENSE
└── files/
    ├── README.md                 # Detailed guide: setup, metrics, suites, reference numbers
    ├── tts_bench.py              # The benchmark
    ├── wer.py                    # Intelligibility scoring (Whisper WER / CER)
    ├── plots.py                  # Charts from a run folder
    ├── tts_client.py             # Client for the OCI speech route with OCI signing
    ├── requirements.txt
    ├── .env.example
    ├── notebook/tts_benchmark.ipynb
    ├── texts/                    # en_science, en_report, ar_coffee, ar_city
    ├── voices/ref_voice.wav      # synthetic reference voice + transcript
    └── results/                  # one folder per run (git-ignored)
```

# Useful Links

- [OCI Generative AI documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [Importing K2-FSA OmniVoice models](https://docs.oracle.com/en-us/iaas/Content/generative-ai/imported-k2-fsa-models.htm)
- [OCI OpenAI-compatible API](https://docs.oracle.com/en-us/iaas/Content/generative-ai/openai-compatible-api.htm)
- [OCI Data Science notebook sessions](https://docs.oracle.com/en-us/iaas/data-science/using/use-notebook-sessions.htm)

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
