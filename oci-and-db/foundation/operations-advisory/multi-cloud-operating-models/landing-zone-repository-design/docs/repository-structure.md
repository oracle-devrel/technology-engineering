# Repository Structure

[Back to overview](../README.md)

This page describes which repositories to create, the folder layout inside them, the naming conventions, and the Git controls that protect them.

## Repository map

Code and configuration are kept in different repositories, owned by different personas (see [GitOps](../../gitops/README.md)):

| Repository | Content | Write access |
|---|---|---|
| Terraform modules and orchestrator | Landing Zone modules and extension modules | IaC Developers |
| Shared pipelines (for example `platform-ci`) | Reusable Terraform and Ansible workflows | IaC Developers or Cloud Operations |
| `<org>-landing-zone` | Foundation configuration, OP.00 to OP.04 | Cloud Operations, with an owner per folder |
| `nonprod-<project>`, `prod-<project>` | Workload requests inside the project handoff | Project Team |

## Folder layout

```text
<org>-landing-zone/                          # Foundation configuration (Cloud Operations)
├── common/                                  # OP.00 - tenancy-wide, applied in the home region
│   ├── iam.json                             # compartments (all levels), identity domain, groups,
│   │                                        # dynamic groups, IAM policies
│   ├── governance.json                      # tag namespaces, budgets
│   ├── security.json                        # Cloud Guard enablement and reporting region
│   ├── observability.json                   # IAM and Cloud Guard event rules
│   └── outputs/                             # only when outputs are saved to Git
│       └── compartments_output.json
│
├── lze_<ENV>/                               # One folder per Landing Zone environment (prod, nonprod)
│   ├── <REGION_PRIMARY>/                    # OP.01 - primary region
│   │   ├── network.json                     # hub VCN, DRG, firewalls, load balancers
│   │   ├── security.json                    # Cloud Guard targets, VSS, vaults
│   │   ├── observability.json               # flow logs, events, alarms, logging integrations
│   │   ├── outputs/
│   │   │   └── network_output.json          # hub VCN, DRG and subnet keys and OCIDs
│   │   └── platform_<PTF>/                  # OP.03 - shared platform
│   │       ├── network.json
│   │       └── observability.json
│   └── <REGION_SECONDARY>/                  # OP.01 - secondary / DR region, regional resources only
│       ├── network.json                     # own hub, firewalls and load balancers
│       ├── security.json
│       └── observability.json
│
├── workload_<ENV>/                          # One folder per workload environment (prod, dev, test...)
│   ├── <REGION_PRIMARY>/                    # OP.02
│   │   ├── network.json                     # spokes
│   │   ├── security.json
│   │   ├── observability.json               # notification topics shared by the environment
│   │   ├── outputs/
│   │   │   ├── network_output.json          # spoke VCNs and subnets
│   │   │   └── topics_output.json           # notification topics
│   │   └── platform_<PTF>/                  # OP.03 - environment platform
│   │       ├── network.json
│   │       └── observability.json
│   └── <REGION_SECONDARY>/                  # OP.02 - DR region
│       └── ...
│
└── projects/<PRJ>/                          # OP.04 - project onboarding (Cloud Operations)
    ├── <ENV>/<REGION>/network.json          # baseline project network access, if needed
    └── handoff/
        └── project-foundation-handoff.json  # approved boundary published to the project repositories

nonprod-<project>/                           # Project repository for dev, test and uat (Project Team)
└── oci/<ENV>/<REGION>/
    ├── network/project-nsgs.json            # NSGs on the assigned spoke VCN
    ├── compute/compute.json
    ├── database/database.json
    └── lifecycle_operations/<operation>.json  # Day 2 operations

prod-<project>/                              # Isolated production project repository (Project Team)
└── oci/prod/<REGION>/
    └── ...
```

The [reference implementation](https://github.com/multicloud-control-plane/oci-landing-zone) uses phase folders instead (`op00_manage_global_landing_zone/`, `op02_manage_environment/<env>/`, `op04_manage_project/<env>/<project>/`) for a single region. Both layouts follow the same rule: one folder, one stack, one state key. The project repositories follow the layout of the [MCCP](../../multi-cloud-control-plane/README.md). Any equivalent layout works if it keeps one folder per cloud, environment and region.

## Conventions

| Item | Convention |
|---|---|
| Landing Zone environment folder | `lze_<ENV>`, for example `lze_prod`, `lze_nonprod` |
| Workload environment folder | `workload_<ENV>`, for example `workload_prod`, `workload_dev` |
| Platform folder | `platform_<PTF>`, inside the Landing Zone or workload environment that owns it |
| Region folder | OCI region identifier, for example `eu-frankfurt-1`. The home region is the primary folder. |
| Tenancy-wide folder | `common/`. It is never repeated per region. |
| Outputs | Read from the upstream state, or saved to `outputs/<name>_output.json` with the file names the orchestrator generates (see [Dependencies and state](dependencies-and-state.md#where-outputs-come-from)) |
| Project handoff | `project-foundation-handoff.json`, published by Cloud Operations during OP.04 and reviewed before use |
| Environment templates | Workload environments use the same file set. Only names (for example `vcn-prod` vs. `vcn-preprod`) and CIDR ranges change. |
| Pull requests | One operation, one environment and one region per pull request, so the plan under review matches one state file |
| State keys | The folder path, for example `workload_prod/eu-frankfurt-1/terraform.tfstate` |

## Folders or repositories?

Git access is per repository: users usually have read, write or admin rights on the whole repository. Folder separation alone does not stop a user with write access from changing another team's folder. Use this rule:

| Situation | Choice |
|---|---|
| Same team, different operations | Separate folders in the same repository. Protect the main branch, require reviewers, and use `CODEOWNERS` (GitHub, GitLab) so that each folder is approved by its owner team, for example network changes by network administrators. |
| Different teams that must not change each other's configuration | Separate repositories. This is the default for project teams, with production separated from non-production. |
| Code and configuration | Always separate repositories, so operators cannot change code and developers cannot change production configuration. |

A small core team can start with one foundation repository and many folders. What matters is that each folder has its own state file and its own pipeline job. Moving a folder to its own repository later is simple; splitting a monolithic file later is not.

## Git controls

- Every change is applied only after approval by a reviewer who is not the author.
- Reviewers reject a request instead of approving it with conditions: automation applies exactly what was merged.
- Apply the rest of the [Git Security](../../operational-security/git-security/README.md) practices: signed commits, MFA and SSO, and no passwords, keys or tokens in Git.
