# CX Conversations Analyzer Agent

The **CX Conversations Analyzer** is an AI agent that listens to your call center recordings and tells you what happened, why customers called, whether their issues were resolved, and how they felt — automatically, at scale.

Drop in one audio file or a full batch. The agent transcribes each call using **OCI AI Speech**, identifies the two speakers, and then uses **OCI Generative AI** with OpenAI GPT-OSS models to extract a structured summary, sentiment score, call reason, resolution status, and the information the agent requested. When processing a batch, it goes further: it groups calls into topic categories and generates an aggregated report with resolution rates, sentiment trends, and actionable insights across all calls.

Example dataset to test it out: [Gridspace-Stanford Harper Valley Dataset](https://github.com/cricketclub/gridspace-stanford-harper-valley)

Reviewed: 27.02.2026

Authors: Yainuvis Socarras and Cristina Granes

# How to use this asset?

See the full setup and usage guide in [`files/README.md`](./files/README.md).

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.