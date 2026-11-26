# OCI Workload Identity Federation for GitHub Actions <!-- omit in toc -->

Reviewed: 2026-11-19

# Table of Contents <!-- omit in toc -->

- [What is this asset?](#what-is-this-asset)
- [How to use this asset?](#how-to-use-this-asset)
- [Examples](#examples)
- [Authentication](#authentication)
- [License](#license)

# What is this asset?

This asset provides examples of OCI Workload Identity Federation (WIF) for GitHub Actions using Terraform and Ansible. They show how a pipeline can access OCI with short-lived resource principal session tokens (RPST), without an OCI user API key.

# How to use this asset?

Use these examples as a reference when designing authentication for your own pipelines. The [setup guide](./SETUP.md) explains the Identity Domain, OAuth application, Resource trust, IAM policies, and GitHub settings used by the examples. Adapt these settings and the workflows to your repository and OCI environment.

For guidance on choosing an authentication method, see [Programmatic Access to OCI for CI/CD Pipelines](../programatic-access-cicd/README.md).

# Examples

Each example uses one private Object Storage bucket to demonstrate authentication and resource creation and deletion. The Terraform workflows also offer a plan-only option.

| Example | Description |
| --- | --- |
| [Terraform](./examples/terraform/simple/README.md) | A simple configuration using the OCI provider's native WIF authentication. |
| [Terraform with OCI Landing Zones Orchestrator](./examples/terraform/orchestrator/README.md) | The same authentication pattern with the official Orchestrator as the Terraform root. |
| [Ansible](./examples/ansible/bucket/README.md) | A credential action exchanges the GitHub OIDC token for an RPST, used by the OCI collection with `resource_principal` authentication. |

The workflow definitions and supporting actions are in [.github](./.github/). Paths in the workflows are relative to the example's root. GitHub only discovers workflows in the repository's root `.github/workflows` directory.

# Authentication

GitHub Actions issues an OIDC token identifying the executing workflow. OCI validates it against a Resource trust and exchanges it for an RPST bound to a temporary signing key. Terraform handles this exchange through the OCI provider; Ansible uses the supplied credential action.

The trust propagates the `repository` and `workflow_ref` claims. The example IAM policies restrict access to the executing repository and the selected compartment. The OAuth client secret is used for token exchange; no service user or group is required for the runtime identity.

Credentials, Terraform plans, and state are kept in the runner's temporary directory and removed at the end of the job. These are short demonstrations: Terraform state is not retained between runs. Review state storage and credential renewal requirements when adapting the pattern to longer pipelines.

The examples were originally published in [oci-terraform-github-actions-wif-example](https://github.com/dgutierrezcolodra/oci-terraform-github-actions-wif-example/tree/c0596cce71bdc16be70f2c04ac6fc31973df31cd).

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](./LICENSE) for more details.
