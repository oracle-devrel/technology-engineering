# OCI Landing Zone

Reviewed: 2026-08-03

Build and govern your OCI foundation through reviewed Git changes. Cloud
Operators establish tenancy IAM, shared networking, environments, the platform
foundation, and project compartments without giving Project Teams administrative
cloud access.

When a project foundation is ready, the solution produces a secure handoff for
the Multi-Cloud Control Plane. The handoff contains the compartment and network
references needed by the project, but no credentials or secrets.

Release status: MVP reference implementation. Complete your security review and
validate enabled capabilities before production rollout.

## Current MVP scope

This MVP supports the commercial OCI realm `oc1` and standard commercial
region identifiers such as `eu-frankfurt-1`. Dedicated Region Cloud@Customer,
government regions, and non-`oc1` realms are not yet accepted by the handoff
validators.

## What you get

- A private Git repository for your OCI foundation.
- Reviewed Terraform plans before foundation changes are applied.
- A read-only bootstrap readiness gate and separate state for OP00–OP04.
- The official OE `v3.1.0` hierarchy, including one compartment per project.
- JSON and Markdown handoff files after OP04.
- An optional Codex app assistant for Cloud Operators.

## Who uses it

Cloud Operators own bootstrap readiness through OP04 and approve foundation changes.
Project Teams start after the handoff and manage workloads through the
[Multi-Cloud Control Plane](../multi-cloud-control-plane/README.md).

## Get started

Prepare these tools before starting:

| Where | Required tools |
|---|---|
| Publication workstation | Git, `jq`, Jsonnet, ripgrep (`rg`), Perl, GitHub CLI (`gh`), and outbound HTTPS to GitHub |
| OCI bootstrap workstation | OCI CLI (`oci`), `jq`, `curl`, and browser access for short-lived OCI authentication |
| Foundation runner | Installed by the supplied cloud-init; no separate manual tool installation is expected |

You also need a private GitHub organization, an OCI tenancy, and an approved OCI
administrative identity. Initial setup needs a dedicated private foundation
runner, a foundation-state bucket, and a separate project-state bucket when
OP03 is enabled.

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
