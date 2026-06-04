# Getting Started with OCI Generative AI Service — Developer Onboarding Guide

*A collection of step-by-step guides for developers onboarding to Oracle Cloud Infrastructure, covering how to connect applications to the OCI Generative AI Service using the OCI SDK, LangChain, and low-code platforms like n8n.*

Author: Dejan Vlasakov

Reviewed: 12.02.2026

# When to use this asset?

*Use this asset when onboarding developers to OCI Generative AI Service. It serves as both a walkthrough for the onboarding team and a reference handout for developers.*

### Who
- Developer onboarding teams introducing OCI Generative AI to new users
- Developers connecting applications to OCI Generative AI for the first time
- Solution architects evaluating integration patterns (SDK, LangChain, low-code)

### When
- Setting up a new project that calls OCI Generative AI (chat, embeddings, or RAG)
- Integrating LangChain with OCI-hosted models for AI application development
- Connecting low-code / no-code platforms (n8n, etc.) to OCI Generative AI via an OpenAI-compatible gateway
- Onboarding workshops and enablement sessions

# How to use this asset?

*Pick the guide that matches your integration approach. Each guide includes prerequisites, working code examples, and environment configuration.*

### Guide 1 — Oracle Database 26ai + OCI Generative AI (OCI SDK)

End-to-end RAG pattern: create an OCI GenAI inference client, generate embeddings, perform vector similarity search in Oracle Database 26ai, and call the chat API with grounded context — all using the OCI Python SDK directly.

**[Read the guide &rarr;](files/OracleDB-GenAIOCI-Connection.md)**

### Guide 2 — LangChain + OCI Generative AI (`langchain-oci`)

Set up the official `langchain-oci` package, instantiate chat and embedding models, and build prompt chains — using the dedicated LangChain integration for OCI.

**[Read the guide &rarr;](files/LangChainOCI-GenAIOCI-Connection.md)**

### Guide 3 — n8n + OCI Generative AI (OpenAI-compatible gateway)

Deploy an OpenAI-compatible gateway that proxies requests to OCI GenAI, configure n8n to use it, and build a sample AI-powered summarisation workflow — no custom code required.

**[Read the guide &rarr;](files/N8N-GenAIOCI-Connection.md)**

### Common Prerequisites

All three guides share the same foundational setup:

1. An active OCI tenancy with Generative AI enabled
2. IAM policies granting access to `generative-ai-family`
3. OCI API key authentication configured locally (`~/.oci/config`)

Each guide then adds tool-specific requirements (Python packages, LangChain, n8n, etc.).

### File Structure
```
.
├── README.md                              # This file
├── LICENSE
└── files/
    ├── OracleDB-GenAIOCI-Connection.md    # Guide 1 – OCI SDK + Oracle DB 26ai
    ├── LangChainOCI-GenAIOCI-Connection.md # Guide 2 – LangChain integration
    └── N8N-GenAIOCI-Connection.md          # Guide 3 – n8n / low-code integration
```

# Useful Links

- [OCI Generative AI Documentation](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)
- [OCI Generative AI — LangChain Integration](https://docs.oracle.com/en-us/iaas/Content/generative-ai/langchain.htm)
- [OCI IAM Policies — Getting Started](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policygetstarted.htm)
- [OCI API Key Authentication Setup](https://docs.oracle.com/en-us/iaas/Content/generative-ai/setup-oci-api-auth.htm)

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
