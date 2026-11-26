# Security Policy

## Reporting Security Vulnerabilities

Use the customer organization's approved private security-reporting channel. Include the affected version, what you observed, steps to reproduce it and the potential impact. Keep credentials and secret values out of the report.

## Component Boundary

The UI uses GitHub authorization to prepare project changes on behalf of the signed-in user. Review and merge take place in GitHub. Trusted runners use their own cloud identities for execution.

Deploy with TLS, the exact registered callback URL and a strong, externally managed `SESSION_SECRET`. Limit the GitHub App to the catalog and served project repositories with the permissions listed in the [UI setup guide](README.md#installation). Rotate credentials and review component updates.

The optional chat runs on a trusted demo host with the presenter's Codex session. Use the host and account controls in the [local chat setup](README.md#local-chat-demo). See the canonical [security and GitHub controls](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/security.md).
