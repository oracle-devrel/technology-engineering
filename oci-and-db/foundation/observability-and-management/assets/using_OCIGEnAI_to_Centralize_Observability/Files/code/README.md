# DB Assistant — sanitized reference source

Start with the [OCI deployment guide](../../Deploy-DB-Assistant-on-OCI.md).

This source package contains the FastAPI application, browser interface, governed MCP gateway, OCI GenAI adapters, four workflow skills and OKE templates. It uses a shared backend service principal, separately authorized human sign-in, one replica and SQLite on persistent storage.

All configuration is illustrative. No real tenant OCIDs, service endpoints, credentials, keys, deployment state or conversation databases are included. Short synthetic OCID-format strings in tests are test fixtures. Do not use example identities as real resources.

## Local preview

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m scripts.preview
```

Open `http://localhost:8000`. The labelled demonstration makes no OCI calls and must remain bound to loopback.

## Prepare a live deployment

```sh
.venv/bin/python -m scripts.prepare_config
```

This generates private working copies and fresh local secrets. Follow the guide to configure your own OCI service identity, OIDC registration, environment grants and deployment. The supplied ingress CIDR is a documentation example and must be replaced before deployment.

## Local checks

```sh
.venv/bin/python -m unittest discover -s tests -v
node --check static/app.js
node --check static/configuration.js
```

Tests mock cloud/model behavior; they do not establish that your target tenancy is configured. Run the guide's live acceptance checks after deploying. See [VALIDATION.md](VALIDATION.md).

## Boundaries

- Operational evidence uses MCP. The model receives curated read-only gateway tools, with exact compartment authorization and bounded time windows.
- The backend calls OCI-hosted GenAI directly for reasoning; project-owned identity/model-catalog MCP adapters provide metadata.
- Additional MCPs can be registered only by authorized administrators. New tool families require explicit gateway and skill implementation.
- Conversation content is persisted privately. APM export is optional and records execution metadata rather than prompt, answer or raw log text.
- Keep a single replica/worker. This is not a production HA deployment and does not provide automatic remediation.

The Dockerfile downloads pinned upstream MCP projects at build time. Review [third-party notices](THIRD-PARTY-NOTICES.md), ownership and licensing before publishing or distributing a built image.
