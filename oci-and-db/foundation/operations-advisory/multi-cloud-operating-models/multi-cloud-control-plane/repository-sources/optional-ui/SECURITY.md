# Security Policy

## Reporting Security Vulnerabilities

Do not open a public GitHub issue for a suspected vulnerability. Use the
customer organization's approved private security-reporting channel and
include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Affected version or revision

## Component Boundary

The UI uses GitHub OAuth and GitHub App authorization to create issues,
branches, commits, and pull requests on behalf of the signed-in user. It does
not store cloud-provider credentials or execute infrastructure changes.

Deploy it with:

- TLS and an exact registered callback URL.
- A strong, externally managed `SESSION_SECRET`.
- GitHub App access limited to the catalog and served project repositories.
- Only the GitHub permissions listed in the component README.
- Regular credential rotation and reviewed component updates.

The canonical MCCP
[security guidance](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/security.md)
defines the review, runner, secret, and GitHub control boundaries.
