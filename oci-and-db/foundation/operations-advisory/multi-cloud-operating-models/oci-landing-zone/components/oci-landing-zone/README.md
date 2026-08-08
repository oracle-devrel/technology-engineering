# OCI Landing Zone

Reviewed: 2026-07-25

Use reviewed Git changes to establish and operate your OCI foundation. A pull
request shows the Terraform plan; an approved merge applies the change through
a trusted self-hosted runner.

## Deployment sequence

Run the phases in order for a new tenancy:

| Phase | Outcome |
|---|---|
| Bootstrap readiness | Private foundation runner, Instance Principal, tools, and state access verified without changing OCI |
| OP00 | Tenancy-wide administrative groups and policies |
| OP01 | Shared landing-zone compartments, network, and security |
| OP02 | One governed environment and its project network |
| OP03 | Platform foundation, when hosted in this tenancy |
| OP04 | One official OE project compartment, group, policies, and handoff |

OP00–OP04 have separate Terraform state and dedicated workflows under
`.github/workflows/`. Bootstrap readiness is read-only and has no state. After
initial deployment, change only the phase that owns the resource.

## Before the first workflow

An OCI administrator must create one dedicated private foundation runner, its
exact-instance dynamic group and policy, and the private foundation-state
bucket before foundation automation can start. Create the separate
project-state bucket before enabling OP03. See
[New tenancy setup](docs/new-tenancy.md) before changing any phase.
Both state buckets must have Object Storage versioning enabled.

Register the runner with this repository and set these GitHub repository
variables:

| Variable | Value |
|---|---|
| `FOUNDATION_RUNNER_LABELS` | JSON runner-label array, for example `["self-hosted","linux","arm64","mccp-foundation"]` |
| `OCI_TF_STATE_BUCKET` | Foundation-state bucket name |
| `PROJECT_STATE_BUCKET` | Separate project-state bucket name used by OP03 IAM |
| `OCI_TF_STATE_NAMESPACE` | Object Storage namespace |
| `REGION` | State bucket region |
| `OCI_TENANCY_OCID` | Tenancy used to validate the OP02 handoff |
| `FOUNDATION_AUTOMATION_READY` | `false` until readiness passes, then `true` |

The runner uses OCI Instance Principal authentication. Do not store API keys or
private keys in this repository.

This installation supports only the commercial OCI realm `oc1` and standard
commercial region identifiers such as `eu-frankfurt-1`. Its validators reject
Dedicated Region Cloud@Customer, government, and other non-`oc1` identifiers.

## Operating rules

- Replace every customer token in `config/customer.jsonnet` before generation.
- Generate phase JSON with `scripts/generate_foundation.sh`; do not handcraft
  resources already supplied by OE.
- Use one focused pull request per phase and review replacement, deletion, and
  IAM changes before approval.
- Keep OP04 under Cloud Operator ownership. Project Teams start after handoff.
- Do not run local applies after the permanent GitOps flow is active.

The configuration pins the reviewed OCI Landing Zone Operating Entities
`master` revision and Orchestrator `release-2.1.4` to immutable revisions.
That official Orchestrator release resolves its OCI database module dependency;
this reference does not add a separate database-module pin. Workflows install Terraform `1.15.8`. The
official TBAC add-on creates a project root with Application, Database, and
Infrastructure child compartments; schema-3 handoffs provide their distinct
workload OCIDs.

After OP04, download `project-foundation-handoff.json` for the Multi-Cloud
Control Plane and `environment_information.md` for the project team. Neither file
contains credentials.

## Guides

1. [New tenancy setup](docs/new-tenancy.md)
2. [Architecture and state](docs/architecture.md)
3. [Phase operations](docs/operations.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
