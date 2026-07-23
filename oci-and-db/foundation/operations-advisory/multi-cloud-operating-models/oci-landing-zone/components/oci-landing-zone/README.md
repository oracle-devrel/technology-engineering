# OCI Landing Zone

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
exact-instance dynamic group and policy, and the private Object Storage state
bucket before foundation automation can start. See
[New tenancy setup](docs/new-tenancy.md) before changing any phase.

Register the runner with this repository and set these GitHub repository
variables:

| Variable | Value |
|---|---|
| `FOUNDATION_RUNNER_LABELS` | JSON runner-label array, for example `["self-hosted","linux","arm64","mccp-foundation"]` |
| `OCI_TF_STATE_BUCKET` | State bucket name |
| `OCI_TF_STATE_NAMESPACE` | Object Storage namespace |
| `REGION` | State bucket region |
| `OCI_TENANCY_OCID` | Tenancy used to validate the OP02 handoff |
| `FOUNDATION_AUTOMATION_READY` | `false` until readiness passes, then `true` |

The runner uses OCI Instance Principal authentication. Do not store API keys or
private keys in this repository.

## Operating rules

- Replace every customer token in `config/customer.jsonnet` before generation.
- Generate phase JSON with `scripts/generate_foundation.sh`; do not handcraft
  resources already supplied by OE.
- Use one focused pull request per phase and review replacement, deletion, and
  IAM changes before approval.
- Keep OP04 under Cloud Operator ownership. Project Teams start after handoff.
- Do not run local applies after the permanent GitOps flow is active.

The configuration pins OE `v3.1.0`, Orchestrator `release-2.1.4`, and Exadata
modules `release-1.2.0` to immutable revisions. Workflows install Terraform
`1.15.8`; the Orchestrator's `>= 1.5.0` declaration is its OCI Resource Manager
compatibility floor, not a cap on this CLI execution path. OE `v3.1.0` creates
one compartment per project. The three
workload-role fields in the handoff all reference that same compartment; no
retired OE `v2.x` child hierarchy is recreated.

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
