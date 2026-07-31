# OCI LangGraph A2A Blueprint

This asset is a blueprint for building and deploying a LangGraph agent on Oracle
Cloud Infrastructure and exposing it through an A2A-compatible server interface.

It provides a practical starting point for teams that want to move from a local
LangGraph workflow to an interoperable agent service, with a clear protocol
boundary, local validation clients, and a containerized deployment path.

Key features:

- 🧠 LangGraph sample agent with explicit state and replaceable workflow steps.
- 🔌 A2A-compatible HTTP/SSE server interface using the official A2A Python SDK.
- 🪪 Public Agent Card discovery endpoint for agent metadata.
- 📡 Server-Sent Events streaming for task status, artifact updates, and
  completion.
- 🧩 Reusable A2A framework layer for plugging in a custom LangGraph agent.
- 🖥️ Direct and A2A streaming Python clients for local validation.
- 🐳 Docker Compose deployment for running the A2A server in one container.
- 🧪 Specifications and unit tests for repeatable, reviewable evolution.

## Link to the original repo

[https://github.com/luigisaetta/oci-langgraph-a2a-blueprint](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint)

Author: L. Saetta

Reviewed: 07.07.2026

## Who should use this asset

Use this asset if you want to prototype, validate, or bootstrap an
A2A-compatible LangGraph agent service on OCI.

It is intended for architects, developers, and field teams who need a reusable
starting point for exposing agent workflows through a stable server contract
that other agents, applications, and orchestration layers can discover and call.

## When to use this asset?

Use this asset when you need to:

- Build a LangGraph agent that can be exposed through an A2A-compatible
  HTTP/SSE interface.
- Demonstrate Agent Card discovery and streaming task lifecycle updates.
- Validate direct in-process agent execution and public A2A streaming execution.
- Replace the sample agent with your own LangGraph workflow while keeping the
  protocol wrapper reusable.
- Run the service locally through Python or Docker Compose before adapting it to
  OCI deployment requirements.
- Use a blueprint that includes specifications, clients, tests, configuration
  notes, and operational documentation.

You should not use this asset:

- As a drop-in production service without reviewing security, IAM,
  observability, scaling, deployment, and operational requirements for your
  environment.
- When you only need a minimal standalone LangGraph script without an agent
  server boundary.
- When you need an unrelated deployment target, framework, or protocol wrapper
  that is outside the LangGraph-on-OCI and A2A-server scope.

In short: this asset accelerates learning, prototyping, and implementation of
LangGraph-based A2A services on OCI while keeping the architecture explicit,
testable, and easy to adapt.

# How to use this asset?

Start from the main repository README and follow the Quickstart for an
end-to-end local setup:

- Repository:
  [oci-langgraph-a2a-blueprint](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint)
- Main README:
  [README.md](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/README.md)
- Documentation index:
  [docs/README.md](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/docs/README.md)
- A2A server usage:
  [server/a2a/README.md](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/server/a2a/README.md)
- Custom agent guide:
  [docs/custom-agent.md](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/docs/custom-agent.md)
- A2A compliance notes:
  [docs/a2a-1-0-compliance.md](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/docs/a2a-1-0-compliance.md)

Typical usage flow:

1. Create or activate the `oci-langgraph-a2a-blueprint` Conda environment.
2. Install the project locally and configure the required environment variables,
   including the OpenAI-compatible OCI endpoint credentials.
3. Start the local A2A server with the sample LangGraph agent.
4. Validate `/.well-known/agent-card.json` and `POST /message:stream` with the
   A2A streaming client or a raw HTTP request.
5. Run the direct agent client when you need to test the LangGraph workflow
   without the A2A protocol boundary.
6. Replace the sample agent with your own LangGraph workflow using the custom
   agent guide.
7. Adapt configuration, security, monitoring, and deployment details to your OCI
   environment before production use.

## License

Licensed under the MIT license. See
[LICENSE](https://github.com/luigisaetta/oci-langgraph-a2a-blueprint/blob/main/LICENSE).
