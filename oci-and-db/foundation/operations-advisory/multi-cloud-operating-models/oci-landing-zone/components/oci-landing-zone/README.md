# OCI Landing Zone

Use reviewed Git changes to establish and operate your OCI foundation. A pull
request shows the Terraform plan; an approved merge applies the change through
a trusted self-hosted runner.

## Deployment sequence

Run the phases in order for a new tenancy:

| Phase | Outcome |
|---|---|
| Bootstrap | Permanent runner network, compute, dynamic group, and policy |
| OP00 | Tenancy-wide administrative groups and policies |
| OP01 | Shared landing-zone compartments, network, and security |
| OP02 | One governed environment and its project network |
| OP03 | Platform foundation, when hosted in this tenancy |
| OP04 | One project's compartments, groups, policies, and handoff |

Each phase has separate Terraform state and a dedicated workflow under
`.github/workflows/`. After initial deployment, change only the phase that owns
the resource.

## Before the first workflow

Bootstrap creates the permanent runner, so its first apply needs a temporary
trusted Linux execution host. An OCI administrator must also create the Object
Storage state bucket and provide approved tenancy-level authentication. See
[New tenancy setup](docs/new-tenancy.md) before changing any phase.

After Bootstrap, register the new runner with this repository and set these
GitHub repository variables:

| Variable | Value |
|---|---|
| `OCI_TF_STATE_BUCKET` | State bucket name |
| `OCI_TF_STATE_NAMESPACE` | Object Storage namespace |
| `REGION` | State bucket region |
| `OCI_TENANCY_OCID` | Tenancy used to validate the OP02 handoff |

The runner uses OCI Instance Principal authentication. Do not store API keys or
private keys in this repository.

## Operating rules

- Replace all example OCIDs, regions, CIDRs, names, images, and SSH keys before
  use.
- Use one focused pull request per phase and review replacement, deletion, and
  IAM changes before approval.
- Keep `.auto.tfvars.json` files enabled; files ending in `.disabled` do not run.
- Keep OP04 under Cloud Operator ownership. Project Teams start after handoff.
- Do not run local applies after the permanent GitOps flow is active.

After OP04, download `project-foundation-handoff.json` for the Multi-Cloud
Control Plane and `enviroment_information.md` for the project team. Neither file
contains credentials.

## Guides

1. [New tenancy setup](docs/new-tenancy.md)
2. [Architecture and state](docs/architecture.md)
3. [Phase operations](docs/operations.md)

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
