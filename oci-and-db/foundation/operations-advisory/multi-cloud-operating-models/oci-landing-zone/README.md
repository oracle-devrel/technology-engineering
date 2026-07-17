# OCI Landing Zone

Build and govern your OCI foundation through reviewed Git changes. Cloud
Operators establish tenancy IAM, shared networking, environments, the platform
foundation, and project compartments without giving Project Teams administrative
cloud access.

When a project foundation is ready, the solution produces a secure handoff for
the Multi-Cloud Control Plane. The handoff contains the compartment and network
references needed by the project, but no credentials or secrets.

Release status: preview. Evaluate the solution in a non-production environment
and complete your security review before production rollout.

## What you get

- A private Git repository for your OCI foundation.
- Reviewed Terraform plans before foundation changes are applied.
- Separate state and workflows for Bootstrap and OP00–OP04.
- A consistent project foundation with application, database, and
  infrastructure compartments.
- JSON and Markdown handoff files after OP04.
- An optional Codex app assistant for Cloud Operators.

## Who uses it

Cloud Operators own Bootstrap through OP04 and approve foundation changes.
Project Teams start after the handoff and manage workloads through the
[Multi-Cloud Control Plane](../multi-cloud-control-plane/README.md).

## Get started

You need Git, Perl, a private GitHub organization, an OCI tenancy, and an
approved OCI administrative identity. The first Bootstrap run also needs a
trusted execution host and an OCI Object Storage state bucket.

Follow the [deployment runbook](docs/deployment.md) to copy the foundation
repository, review its customer values, create the initial Git commit, and
configure GitHub and OCI. No custom installation program is required.

Continue with:

1. [How the foundation works](docs/architecture.md)
2. [Deployment](docs/deployment.md)
3. [Day-to-day operations](docs/operations.md)
4. [Security](docs/security.md)
5. [Optional Codex app assistant](docs/codex-app.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
