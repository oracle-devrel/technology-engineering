# Multi-Cloud Control Plane

Give Project Teams a consistent, governed way to request infrastructure in OCI,
Azure, and Google without direct cloud credentials or local Terraform expertise.

Teams select an approved template, submit a JSON change, and review the
Terraform plan or Ansible check in a pull request. A trusted runner performs the
change only after human approval and merge. Paid GitHub plans can enforce that
approval with repository controls; the Free profile relies on restricted roles
and documented process.

Release status: preview. Evaluate the solution in non-production and complete
your security review before production rollout.

## What your teams can manage

- OCI Autonomous Database, Compute, and project network security groups.
- Azure project infrastructure and supported Day 1 resources.
- Oracle Autonomous Database on Google Cloud.
- OCI Autonomous Database start and stop operations.
- OCI Compute agent deployment as an SSH operations example.

Azure and Google Day 2 operations are not currently available.

## What you get

Installation prepares four private repositories for your organization:

- `platform-ci` provides the approved Terraform and Ansible workflows.
- `nonprod-project-template` provides the standard shared non-production
  project repository structure.
- `prod-project-template` provides the separate production project structure.
- `gitops-templates` provides the approved resource and operation catalog.

The Multi-Cloud Control Plane UI and Codex app assistant are optional. GitHub pull requests remain the
standard path, so neither option is required.

## Get started

You need Git, `jq`, Perl, a private GitHub organization, an OCI Object Storage
state backend, trusted Linux runners, and a completed project-foundation handoff.
Runners need Terraform 1.12 or later, Python 3.11 or later, and the
authentication required by each enabled cloud. Use the
[OCI Landing Zone](../oci-landing-zone/README.md) if you need to
establish the OCI foundation first.

Follow the [deployment runbook](docs/deployment.md) to prepare and pin the four
repositories with standard file, Git, `jq`, and Perl commands. No custom
installation program is required.

Platform administrators: [architecture](docs/architecture.md),
[deployment](docs/deployment.md), and [security](docs/security.md).

Project Teams: [first request](docs/first-request.md) and
[day-to-day operations](docs/operations.md). The
[Multi-Cloud Control Plane UI](components/multi-cloud-plane/README.md) and the
[optional Codex app assistant](docs/codex-app.md) are separate integrations.

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
