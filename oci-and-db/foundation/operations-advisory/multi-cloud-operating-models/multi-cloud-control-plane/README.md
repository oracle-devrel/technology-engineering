# Multi-Cloud Control Plane

Give Project Teams a consistent, governed way to request infrastructure in OCI,
Azure, and Google without direct cloud credentials or local Terraform expertise.

Teams select an approved template, submit a JSON change, and review the
Terraform plan or Ansible check in a pull request. A trusted runner performs the
change only after human approval and merge. Paid GitHub plans can enforce that
approval with repository controls; the Free profile relies on restricted roles
and documented process. Use the
[GitHub plan capability matrix](docs/security.md#github-plan-capability-matrix)
before choosing a repository security profile.

For the operating-model background behind this implementation, see
[What is GitOps and why it is needed](../gitops/README.md).

Release status: MVP reference implementation. Complete your security review and
validate enabled capabilities before production rollout.

## What your teams can manage

- OCI Autonomous Database, Compute, and project network security groups.
- Private Azure Linux VMs and Oracle Autonomous Database.
- Private Google Cloud Linux VMs and Oracle Autonomous Database.
- OCI Autonomous Database start and stop operations.
- OCI Compute agent deployment as an SSH operations example.

Azure and Google Day 2 operations are outside this MVP.

Azure and Google qualification uses provider-schema validation and credential-free mocked
Terraform lifecycle tests. No live target-cloud apply was performed for this publication; do not
represent either adapter as live-cloud certified.

## What you get

Installation prepares four private repositories for your organization:

- `platform-ci` provides the approved Terraform and Ansible workflows.
- `nonprod-project-template` provides the standard shared non-production
  project repository structure.
- `prod-project-template` provides the separate production project structure.
- `gitops-templates` provides the approved resource and operation catalog.

The Codex app assistant is optional. GitHub pull requests remain the standard
path and require no additional user interface. A browser UI is outside the
scope of this MVP reference implementation.

## Get started

You need Git, `jq`, Perl, a private GitHub organization, an OCI Object Storage
state backend, trusted Linux runners, and a completed project-foundation handoff.
Runners need Git, `jq`, `rg`, Python 3.11 or later, outbound access for the
pinned Terraform installer, and the authentication required by each enabled
cloud. The workflow installs Terraform 1.12.1. Use the
[OCI Landing Zone](../oci-landing-zone/README.md) if you need to
establish the OCI foundation first.

Follow the [deployment runbook](docs/deployment.md) to prepare, verify, and pin
the four repositories with standard file, Git, `jq`, and Perl commands. No
custom installation program is required.

Platform administrators: [architecture](docs/architecture.md),
[deployment](docs/deployment.md), and [security](docs/security.md).

Project Teams: [first request](docs/first-request.md),
[day-to-day operations](docs/operations.md), and the
[optional Codex app assistant](docs/codex-app.md).

This initial-installation package supports the
[shared non-production repository model](docs/shared-nonproduction.md) and the
separate [production repository model](docs/production.md).

## Glossary

- **OP04**: Landing Zone project-foundation phase that creates the project
  compartments, groups, and policies.
- **Handoff**: verified foundation references delivered by the platform team;
  executable request intent stays in JSON manifests.
- **Orchestrator**: the pinned Terraform repository that consumes a manifest.
- **Day 1**: provisioning a resource. **Day 2**: a supported operation on an
  existing resource, such as an ADB lifecycle request.
- **Handed-off project**: a repository whose foundation and access conventions
  have been supplied and accepted by the platform team.
- **Codex app**: the optional Project GitOps assistant that prepares Git changes
  and pull requests; it never deploys cloud resources.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
