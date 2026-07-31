# OCI MCP Blueprint

This asset is a blueprint for building, customizing, packaging, and deploying a
Python MCP server on Oracle Cloud Infrastructure.

It provides a practical starting point for teams that want to move from a local
custom MCP server prototype to a cloud-ready service deployable on OCI
Enterprise AI Hosted Applications, with a clear protocol boundary, modular
sample code, local validation clients, and a guided deployment factory.

Key features:

- 🔌 Python FastMCP server using Streamable HTTP.
- 🧰 Two sample MCP tools, `get_schema` and `get_data`, backed by fake
  hard-coded database metadata and simulated rows.
- 🧩 Modular domain and MCP registration layers for replacing the sample tools
  with a custom MCP implementation.
- 🖥️ Command-line MCP client for local and remote endpoint validation.
- 🐳 Docker Compose deployment for running the MCP server locally in one
  container.
- 🏭 OCI Hosted Deployment Factory for building the server image, pushing it to
  OCIR, and creating an OCI Enterprise AI Hosted Application deployment.
- 🧪 Specifications, tests, and documentation for repeatable, reviewable
  evolution.

## Link to the original repo

[https://github.com/luigisaetta/oci-mcp-blueprint](https://github.com/luigisaetta/oci-mcp-blueprint)

Author: L. Saetta

Reviewed: 08.07.2026

## Who should use this asset

Use this asset if you want to prototype, validate, or bootstrap a custom MCP
server in Python and deploy it on OCI Enterprise AI Hosted Applications.

It is intended for architects, developers, and field teams who need a reusable
starting point for exposing custom tools through an MCP server contract that can
be tested locally, packaged as a container, and promoted to OCI.

## When to use this asset?

Use this asset when you need to:

- Build a Python MCP server with a clean FastMCP Streamable HTTP boundary.
- Replace sample tools with custom business, data, or integration tools.
- Validate MCP tool discovery and tool calls locally with a command-line client.
- Package the MCP server as a Docker image.
- Run the server locally through Python or Docker Compose.
- Deploy the MCP server to OCI Enterprise AI Hosted Applications through a
  guided local factory.
- Use a blueprint that includes specifications, tests, configuration notes,
  customization guidance, and operational documentation.

You should not use this asset:

- As a drop-in production service without reviewing security, IAM,
  observability, scaling, deployment, and operational requirements for your
  environment.
- When you only need a one-off local script without an MCP server boundary.
- When you need protocols other than MCP Streamable HTTP.
- When you need an unrelated deployment target or framework outside the
  Python-MCP-on-OCI scope.

In short: this asset accelerates learning, prototyping, and implementation of
custom MCP servers on OCI while keeping the architecture explicit, testable, and
easy to adapt.

# How to use this asset?

Start from the main repository README and follow the local setup instructions:

- Repository:
  [oci-mcp-blueprint](https://github.com/luigisaetta/oci-mcp-blueprint)
- Main README:
  [README.md](https://github.com/luigisaetta/oci-mcp-blueprint/blob/main/README.md)
- MCP customization guide:
  [docs/customizing-mcp-server.md](https://github.com/luigisaetta/oci-mcp-blueprint/blob/main/docs/customizing-mcp-server.md)
- Docker Compose deployment:
  [docs/docker-compose-deployment.md](https://github.com/luigisaetta/oci-mcp-blueprint/blob/main/docs/docker-compose-deployment.md)
- OCI Hosted Deployment Factory:
  [docs/oci-hosted-deployment-factory.md](https://github.com/luigisaetta/oci-mcp-blueprint/blob/main/docs/oci-hosted-deployment-factory.md)
- Specifications:
  [specs/](https://github.com/luigisaetta/oci-mcp-blueprint/tree/main/specs)

Typical usage flow:

1. Create or activate the `oci-mcp-blueprint` Conda environment.
2. Install the project locally with development dependencies.
3. Start the sample MCP server with FastMCP Streamable HTTP.
4. Validate tool discovery with `oci-mcp-blueprint-client list-tools`.
5. Call the sample `get_schema` and `get_data` tools.
6. Replace the fake domain logic and MCP tool registrations with your custom
   implementation.
7. Run tests and local Docker Compose validation.
8. Start the OCI Hosted Deployment Factory when you are ready to build, push,
   and deploy the MCP server image to OCI Enterprise AI Hosted Applications.
9. Adapt security, IAM, observability, scaling, and operations to your OCI
   environment before production use.

## License

Licensed under the MIT license. See
[LICENSE](https://github.com/luigisaetta/oci-mcp-blueprint/blob/main/LICENSE).
