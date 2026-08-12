# OCI Landing Zone

Reviewed: 2026-08-11

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
- The reviewed OCI Landing Zone OE `master` revision with the official TBAC
  hierarchy: a project root plus Application, Database, and Infrastructure
  child compartments.
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

## First deployment path

For one new tenancy, use this path in order. It is intentionally a small,
reviewed MVP path: one initial environment and one initial project.

1. Record the approved organization, OCI region, non-overlapping hub and
   environment CIDRs, state-bucket names, initial environment, and initial
   project name. Decide whether the Multi-Cloud Control Plane is hosted in
   this tenancy.
2. Follow the [deployment runbook](docs/deployment.md) to stage the repository,
   set `config/customer.jsonnet`, leave `config/projects.json` empty, and run
   `scripts/generate_foundation.sh all`. Generated JSON is reviewed output;
   do not edit it by hand.
3. Follow the component's [new-tenancy setup](components/oci-landing-zone/docs/new-tenancy.md)
   to establish the private state and runner boundary, then pass bootstrap
   readiness.
4. Submit one reviewed pull request for each transition: OP00, OP01 `core`,
   OP03 `infrastructure` and `identity` when the platform is hosted here, one
   OP02 environment, OP01 `pre`, OP01 `final`, and one OP04 project.
5. Use the generated handoff after OP04 to create the project repository and
   begin Project GitOps. See [phase operations](components/oci-landing-zone/docs/operations.md)
   for the ownership, repeatability, and success condition of each transition.

## Two runners, two permission boundaries

The foundation and projects do **not** share a runner. They use two separate
VMs with separate OCI Instance Principals, dynamic groups, state access, and
responsibilities:

| Runner | Created by | Used by | May access | Must not access |
|---|---|---|---|---|
| Foundation runner | Bootstrap procedure | Cloud Operators for bootstrap through OP04 | Foundation state and approved Landing Zone operations | Project workload state or project repositories |
| Project runner | OP03 | Selected Project Team repositories after handoff | Project workload state and the fixed, environment-scoped Compute, ADB, and project-NSG permissions | Foundation state, tenancy administration, Security Zones, and Landing Zone administration |

A Project Team can change code in its own repository, but OCI IAM evaluates the
Project runner's Instance Principal for every API call. A workflow cannot gain
foundation privileges merely by changing project code. The validated OP04
handoff supplies only the project's permitted compartment and network
references; it never grants the team the foundation runner, foundation state,
or tenancy-administrative access.

The MVP uses one Project runner identity for the selected repositories. Its OCI
policies cover the environment's `PROJECTS` subtree, so this is a foundation
boundary, not OCI isolation between those projects. Use project-specific runner
identities and policies only when that stronger boundary is an approved future
requirement.

Continue with:

1. [How the foundation works](docs/architecture.md)
2. [Deployment](docs/deployment.md)
3. [Day-to-day operations](docs/operations.md)
4. [Security](docs/security.md)
5. [Optional Codex app assistant](docs/codex-app.md)
6. [Install and use the Codex GitOps skills](docs/codex-skills-installation.md)
7. [Customer organization adoption runbook](docs/customer-organization-runbook.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
