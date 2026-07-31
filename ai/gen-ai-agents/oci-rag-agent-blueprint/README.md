# OCI RAG Agent Blueprint

This asset is a blueprint for building and deploying a Retrieval-Augmented
Generation agent on OCI Enterprise AI.

It provides a practical starting point for teams that want to move from
document retrieval to a working agent experience, with local validation and a
path to OCI Hosted Applications.

Key features:

- 🔎 OCI Vector Store retrieval for grounded answers over enterprise documents.
- 💬 OpenAI-compatible Responses API integration for agent interactions.
- ⚡ Streaming and non-streaming request handling.
- 🧩 FastAPI backend with clear request and response contracts.
- 🖥️ Next.js reference UI for local and hosted validation.
- 🧪 Python CLI client, schemas, specs, and tests for repeatable checks.
- 🚀 Agent Factory workflow for OCI Enterprise AI Hosted Applications.

## Link to the original repo

[https://github.com/luigisaetta/oci-rag-agent-blueprint](https://github.com/luigisaetta/oci-rag-agent-blueprint)

Author: L. Saetta

Reviewed: 06.07.2026

## Who should use this asset

Use this asset if you want to prototype, validate, or bootstrap a RAG assistant
on OCI with a clear path from local development to OCI Enterprise AI Hosted
Applications.

It is intended for architects, developers, and field teams who need a reusable
starting point for grounded enterprise assistants backed by documents stored and
indexed through OCI services.

## When to use this asset?

Use this asset when you need to:

- Build an internal knowledge assistant over company documentation, policies,
  runbooks, or onboarding material.
- Demonstrate OCI Vector Store retrieval with an OpenAI-compatible Responses
  API agent.
- Validate streaming and non-streaming chat behavior before a production
  implementation.
- Test local and hosted invocation paths using a CLI client and a reference web
  UI.
- Deploy a RAG backend container to OCI Enterprise AI Hosted Applications.
- Use a blueprint that includes specifications, schemas, tests, deployment
  notes, and operational documentation.

You should not use this asset:

- As a drop-in production service without reviewing security, IAM,
  observability, scaling, and operational requirements for your environment.
- When you only need a minimal script or a one-off document search example.

In short: this asset accelerates learning, prototyping, and implementation of
RAG agents on OCI while keeping the architecture reviewable and extensible.

# How to use this asset?

Start from the main repository README and follow the Quickstart for an
end-to-end setup:

- Repository:
  [oci-rag-agent-blueprint](https://github.com/luigisaetta/oci-rag-agent-blueprint)
- Quickstart:
  [QUICKSTART.md](https://github.com/luigisaetta/oci-rag-agent-blueprint/blob/main/QUICKSTART.md)
- API usage:
  [docs/agent-api-usage.md](https://github.com/luigisaetta/oci-rag-agent-blueprint/blob/main/docs/agent-api-usage.md)
- Deployment guide:
  [docs/oci-enterprise-ai-deployment.md](https://github.com/luigisaetta/oci-rag-agent-blueprint/blob/main/docs/oci-enterprise-ai-deployment.md)
- Agent Factory:
  [agent-factory/README.md](https://github.com/luigisaetta/oci-rag-agent-blueprint/blob/main/agent-factory/README.md)

Typical usage flow:

1. Provision the required OCI resources, including OCI Vector Store and the OCI
   Enterprise AI runtime configuration.
2. Configure the repository environment variables.
3. Load or synchronize documents into the vector store.
4. Start the local backend and reference UI, or deploy through the Agent Factory
   workflow.
5. Validate the `/health` and `/responses` endpoints with the CLI client or the
   web UI.
6. Adapt the blueprint to your enterprise security, deployment, monitoring, and
   evaluation requirements.

## License

Licensed under the MIT license. See
[LICENSE](https://github.com/luigisaetta/oci-rag-agent-blueprint/blob/main/LICENSE).
