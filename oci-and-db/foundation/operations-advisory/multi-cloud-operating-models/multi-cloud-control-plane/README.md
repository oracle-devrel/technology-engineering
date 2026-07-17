# Multi-Cloud Control Plane

Give Project Teams a consistent, governed way to request infrastructure in OCI,
Azure, and Google without direct cloud credentials or local Terraform expertise.

Teams select an approved template, submit a JSON change, and review the
Terraform plan or Ansible check in a pull request. A trusted runner performs the
change only after the required approval and merge.

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

Installation prepares three private repositories for your organization:

- `platform-ci` provides the approved Terraform and Ansible workflows.
- `oe-env-project-template` provides the standard project repository structure.
- `gitops-templates` provides the approved resource and operation catalog.

The web UI and Codex app assistant are optional. GitHub pull requests remain the
standard path, so neither option is required.

## Get started

You need Git, `jq`, Perl, a private GitHub organization, an OCI Object Storage
state backend, trusted Linux runners, and a completed project-foundation handoff.
Runners need Terraform 1.12 or later, Python 3.11 or later, and the
authentication required by each enabled cloud. Use the
[OCI Landing Zone](../oci-landing-zone/README.md) if you need to
establish the OCI foundation first.

Follow the [deployment runbook](docs/deployment.md) to prepare and pin the three
repositories with standard file, Git, `jq`, and Perl commands. No custom
installation program is required.

Continue with:

1. [How the Control Plane works](docs/architecture.md)
2. [Deployment](docs/deployment.md)
3. [Day-to-day operations](docs/operations.md)
4. [Security](docs/security.md)
5. [Optional Codex app assistant](docs/codex-app.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
