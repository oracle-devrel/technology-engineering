# Validation of the sanitized deployment package

## Local checks

- 69 existing application tests passed against the copied source, using the available Python 3.13 development dependency environment. These cover authorization, isolated MCP transport, conversations, model adapters, SQL routing, evidence handling and gateway boundaries.
- Both browser JavaScript files passed `node --check`.
- Python source parses; JSON examples and Kubernetes YAML parse; local Markdown links resolve.
- The new configuration helper was exercised in temporary storage: it generates fresh session/encryption values, creates private working files and refuses to overwrite an existing configuration.
- The distribution was checked for original project identifiers, full OCI resource identifiers, personal details, private-key blocks and forbidden runtime files. Source selection excludes live configuration, credentials, logs, databases, caches, dependency environments and deployment records.

Synthetic IDs, fake credentials in unit tests, public vendor endpoints and `example.com` addresses are illustrative. They are not usable deployment credentials.

## What still needs verification in the reader's environment

- Fresh dependency installation and full container build for the selected worker architecture.
- Cluster/CNI compatibility, persistent-volume provisioning, LB subnet/NSG settings, TLS and network reachability.
- OIDC app registration, verified claims, portal grants and backend IAM permissions.
- GenAI model availability, inference entitlement and actual tool-calling behavior.
- Both MCPs retrieving real evidence in the selected compartment, with correct timestamps and inventory IDs.
- APM span ingestion, retention and correlation for a two-message conversation.

No cloud resources were created or modified while preparing this package. The replacement configuration was not deployed to OCI. This reference source is a single-replica prototype and does not imply production readiness or guaranteed monitoring coverage.

Checks are a publication aid, not a guarantee that future edits remain free of sensitive data. Share the supplied sanitized archive rather than a configured working directory.
