# GitOps Repository Design and Lifecycle Governance

Reviewed: 2026-09-30

## Table of contents

- [GitOps Repository Design and Lifecycle Governance](#gitops-repository-design-and-lifecycle-governance)
  - [Table of contents](#table-of-contents)
  - [What is this asset?](#what-is-this-asset)
  - [How to use this asset?](#how-to-use-this-asset)
  - [Why not one stack?](#why-not-one-stack)
  - [Design Decisions](#design-decisions)
    - [Landing Zone Cloud-Native Operations (What) and Cloud Operations Teams (Who)](#landing-zone-cloud-native-operations-what-and-cloud-operations-teams-who)
  - [Repository layout at a glance](#repository-layout-at-a-glance)
  - [Minimum split for a small team](#minimum-split-for-a-small-team)
  - [Monolithic vs. multi-stack](#monolithic-vs-multi-stack)
  - [Documentation](#documentation)
  - [Related assets](#related-assets)
- [License](#license)


## What is this asset?

This asset is a reference design to manage OCI Landing Zones and Workloads lifecyle state using Infrastructure as Code (IaC) with GitOps. 
 
Use it when you need to design or follow a recommended approach to design and deploy complex Multi-Stack Terraform configurations for OCI Landing Zones and Workloads, managed by different teams. You'll learn how to organize the Git repositories, where each resource belongs (tenancy-wide or regional), how stacks share information, how to separate state files, and which runtime to use (OCI Resource Manager or CI/CD automation).

Managing resources with multiple Terraform Stacks allows you to avoid monolythic unmanageable configurations, remove blast radius on failure, aligns with complex organizations Operating Models and follows Operational Security best practices for Git and CICD security.

For Landing Zones already deployed in one stack, the [adoption path](docs/adoption.md) explains how to move to this design without recreating resources.

To know more about about these individual topics, click on each of them: [GitOps](../gitops/README.md), [Git Security](../operational-security/git-security/README.md), and [CI/CD Security](../operational-security/cicd-security/README.md).


## How to use this asset?

Read this page to understand the approach and decide whether it fits. The detailed guidance is in the `docs/` folder.

| If you... | Read |
|---|---|
| Are designing a complex Landing Zone Multi-Stack Deployment. | This page, then [Repository structure](docs/repository-structure.md), [Component distribution](docs/component-distribution.md), [dependencies and state](docs/dependencies-and-state.md), and [Runtime](docs/runtime.md) |
| Need to choose between one-stack and multi-stack. | [Monolithic vs. multi-stack](#monolithic-vs-multi-stack), and [minimum split](#minimum-split-for-a-small-team) |
| Are adding additional regions. | [Component distribution](docs/component-distribution.md) and [dependencies and state](docs/dependencies-and-state.md) |
| Want to see the design applied end to end. | [Working example](docs/worked-example.md) |
| Want to undestand risks and common mistakes. | [Anti-patterns and checklist](docs/checklist.md) |
| Already running the Landing Zone in one large stack and want to migrate to Multi-Stack. | [Adoption path](docs/adoption.md), to move to this design without recreating resources |

## Why not one stack?

Most organizations start with one Git repository, a few large configuration files and **one stack with one state file** for the whole Landing Zone. This is a good start: the Operating Entities repository offers a one-stack runtime for One-OE for exactly this reason. The same repository also recommends [one ORM stack per asset](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities/blob/master/commons/content/orm_bp.md) once the Landing Zone grows, because three problems appear during Day 2 operations:

| Problem | What happens |
|---|---|
| **Blast radius and state lock** | One state file means one lock. If one pipeline gets stuck, nobody can change anything else until it is fixed. A failed change in non-production can block an urgent change in production. |
| **Multi-region and DR** | A second region is added for DR or to run closer to users. Network, security and monitoring are regional. If the state of the second region lives in the first region, losing the first region also means losing the ability to manage the second. |
| **Git governance and file size** | Git permissions apply to a whole repository. With one set of files, anyone who can change a project can also change IAM, the hub or security. Files such as a `network.json` with the hub and all spokes grow to thousands of lines. |

## Design Decisions

| # | Principle |
|---|---|
| 1 | **Repeatable operations.** The Landing Zone is split into repeatible operations, aligned to user stories. |
| 2 | **Repositories follow separation of duties.** Folder and repository boundaries follow team boundaries. |
| 3 | **No monoliths.** Each operation has its own configuration files, state file and pipeline job. |
| 4 | **Everything through Git.** Changes are applied only after approval by a reviewer who is not the author. |
| 5 | **Separated by region.** Regional resources live in regional folders with regional state files. |
| 6 | **Segregated state.** No locking between environments, regions or projects. |
| 7 | **Independent project teams.** Projects work in their own repositories and state, inside a boundary handed off by Cloud Operations. They never manage IAM and never hold cloud deployment credentials. |


### Landing Zone Cloud-Native Operations (What) and Cloud Operations Teams (Who)

| Operation | Scope | Who |
|---|---|---|
| **OP.00 Manage Global Landing Zone** | Tenancy-wide: compartments, identity domain, groups, dynamic groups, IAM policies, tag namespaces, budgets, Cloud Guard enablement, IAM and Cloud Guard event rules | Central Cloud Operations |
| **OP.01 Manage Landing Zone Environment** | Per region: network hub, shared security, shared observability | Central Cloud Operations |
| **OP.02 Manage Environment** | Per environment and region: spokes, environment security and observability | Workload Environment Team or Central Cloud Operations |
| **OP.03 Manage Platform** | Platforms: the GitOps runner platform, or workload platforms such as ExaDB-D or OKE | Platform Team |
| **OP.04 Manage Project** | Project onboarding by Cloud Operations: project compartments, groups and policies, and the handoff to Project Team (manages workloads) | Central Cloud Operations -> Project Team |

In the diagram, colors show the layer (white tenancy-wide, white Landing Zone environment, green workload environment, dark grey platform, light grey project) and the owner team is in italics. Each arrow is a reviewed change; its label is what the next operation needs from the previous one.

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 320}}}%%
flowchart TB
    classDef tenancy fill:#ffffff,stroke:#000000,color:#1a1a1a
    classDef lz fill:#ffffff,stroke:#cc0000,color:#1a1a1a
    classDef env fill:#D5E8D4,stroke:#82B366,color:#1a1a1a
    classDef platform fill:#808080,stroke:#808080,color:#1a1a1a
    classDef project fill:#F5F5F5,stroke:#666666,color:#1a1a1a

    OP00["<b>OP.00 Global Landing Zone</b><br/>tenancy-wide<br/><i>Central Cloud Operations</i>"]:::tenancy
    OP01["<b>OP.01 Landing Zone Environment</b><br/>per region<br/><i>Cloud Operations</i>"]:::lz
    OP03a["<b>OP.03 Shared Platform</b><br/><i>Cloud Operations</i>"]:::platform
    OP02["<b>OP.02 Environment</b><br/>per environment and region<br/><i>Workload Environment Team</i>"]:::env
    OP03b["<b>OP.03 Environment Platform</b><br/><i>Platform Team</i>"]:::platform
    OP04["<b>OP.04 Manage Project</b><br/>project IAM and handoff<br/><i>Cloud Operations</i>"]:::project
    PRJ["<b>Project repository</b><br/>Day 1 and Day 2 requests<br/><i>Project Team</i>"]:::project

    OP00 -->|global groups and policies| OP01
    OP01 -->|dedicated security, network and observability| OP03a
    OP01 -->|DRG| OP02
    OP02 -->|subnets| OP03b
    OP02 -->|"spoke, topics"| OP04
    OP04 -->|handoff| PRJ
```

Every stack also reads the compartments output of the stack that owns its parent compartments.

> [!NOTE]
> **Reference implementation.** The [OCI Landing Zone reference implementation](https://github.com/multicloud-control-plane/oci-landing-zone) of the Multi-Cloud Control Plane implements OP00 to OP04 on the Operating Entities blueprint, with one GitHub workflow and one state key per phase, a private self-hosted runner with Instance Principal, and the project handoff. It targets a single region. This blueprint uses the same operations and adds the guidance for more regions, more environments and more teams. The main differences are called out where they apply. For a new tenancy, when the GitOps runner platform (OP03) is hosted in the same tenancy, deploy it before the first OP02: OP02 creates runner policies that refer to the OP03 dynamic group. The deployment order is therefore OP00, OP01, OP03, OP02, OP04.

The Operating Entities Multi-OE runtime uses the same idea with other names (OP.01 Shared Services to OP.04 Project Environment). Compartments, groups and the two ways to place IAM are described in [Component distribution](docs/component-distribution.md).

## Repository layout at a glance

```text
<org>-landing-zone/                  # Foundation configuration (Cloud Operations)
├── common/                          # OP.00  tenancy-wide, applied in the home region
├── lze_<ENV>/<REGION>/              # OP.01  one folder per Landing Zone environment and region
│   └── platform_<PTF>/              # OP.03  shared platform
├── workload_<ENV>/<REGION>/         # OP.02  one folder per workload environment and region
│   └── platform_<PTF>/              # OP.03  environment platform
└── projects/<PRJ>/handoff/          # OP.04  published project boundary

nonprod-<project>/  prod-<project>/  # Project repositories (Project Team)
```

Each leaf folder is one stack with one state file. Terraform code lives in separate repositories. The full layout, naming conventions and Git controls are in [Repository structure](docs/repository-structure.md).

## Minimum split for a small team

A small central team does not need dozens of stacks on day one. This split already removes the three problems above. Each box is one stack with its own state file; the dashed box is added when a second region is needed.

```mermaid
%%{init: {"flowchart": {"wrappingWidth": 320}}}%%
flowchart TB
    classDef tenancy fill:#ede7f6,stroke:#5e35b1,color:#1a1a1a
    classDef lz fill:#e3f2fd,stroke:#1e88e5,color:#1a1a1a
    classDef env fill:#e8f5e9,stroke:#43a047,color:#1a1a1a
    classDef platform fill:#eceff1,stroke:#546e7a,color:#1a1a1a
    classDef project fill:#fff3e0,stroke:#fb8c00,color:#1a1a1a
    classDef later fill:#ffffff,stroke:#9e9e9e,color:#555555,stroke-dasharray:4 3

    C["<b>common/</b><br/>OP.00 · IAM has one owner"]:::tenancy
    subgraph DR["Secondary region, when needed"]
        L2["<b>lze_ENV/secondary</b><br/>OP.01 · own hub"]:::later
    end
    subgraph HOME["Primary region"]
        L1["<b>lze_ENV/primary</b><br/>OP.01 · hub"]:::lz
        P1["<b>workload_prod/primary</b><br/>OP.02"]:::env
        N1["<b>workload_nonprod/primary</b><br/>OP.02"]:::env
    end
    C --> L1
    L1 --> P1
    L1 --> N1
    C -.-> L2
```

| Stack | Problem it removes |
|---|---|
| `common/` | IAM and tenancy-wide services have one owner, ready for a second region. |
| One `lze_<ENV>` stack per region | Each region is managed alone; the DR region does not depend on the primary. |
| `workload_prod` and `workload_nonprod` | A failure in non-production never locks production. |

Project, platform and extra environment stacks are added later with the same templates. The [worked example](docs/worked-example.md) shows this split with real configuration fragments. The order of changes and how to move existing resources without recreating them are in [Adoption path](docs/adoption.md).

## Monolithic vs. multi-stack

| Criteria | Monolithic | Multi-stack (this blueprint) |
|---|---|---|
| Number of stacks | One; easy to follow | Grows with environments, regions and projects |
| Initial effort | Low | Higher: design, templates, pipelines |
| Blast radius and state lock | Whole tenancy, including production | One operation, environment and region |
| Multi-region and DR | DR depends on the primary region | Each region is managed on its own |
| File size and reviews | Files of thousands of lines | Small files per domain and environment |
| Git governance | All or nothing | Per folder or per repository |
| Delegation to project teams | Only by giving access to everything | Own repositories inside a handoff, without IAM or credentials |
| Dependencies | Implicit, inside one state | Explicit output files and multi-step changes |
| Cross-cutting changes during the initial build | Same effort | Same effort |
| Fit with ORM | Good | Good with one stack per operation; runners recommended at scale |
| Cost of changing the design later | High: splitting in production | Paid once, at the start |

## Documentation

| Document | Content |
|---|---|
| [Repository structure](docs/repository-structure.md) | Repository map, full folder layout, conventions, folders vs. repositories, Git controls |
| [Component distribution](docs/component-distribution.md) | Tenancy-wide vs. regional resources, compartments and groups, IAM placement, service limits |
| [Dependencies and state](docs/dependencies-and-state.md) | Output files, project handoff, multi-step changes, state boundaries, naming and backends |
| [Runtime](docs/runtime.md) | ORM vs. CI/CD runners, Day-2 operations, runner boundaries |
| [Adoption path](docs/adoption.md) | For Landing Zones already deployed in one stack: order of changes, moving resources between stacks, splitting a network configuration into hub and spoke stacks |
| [Worked example](docs/worked-example.md) | From one stack to the minimum split and a DR region, with configuration fragments |
| [Anti-patterns and checklist](docs/checklist.md) | Common mistakes and a design review checklist |

## Related assets

- [OCI Landing Zone Operating Entities](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities) and its [ORM best practices](https://github.com/oci-landing-zones/oci-landing-zone-operating-entities/blob/master/commons/content/orm_bp.md)
- [OCI Landing Zones orchestrator](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator)
- [OCI Landing Zone reference implementation](https://github.com/multicloud-control-plane/oci-landing-zone) for OP00 to OP04 with GitHub Actions
- [GitOps](../gitops/README.md), [Multi-Cloud Control Plane](../multi-cloud-control-plane/README.md) and [Git Security](../operational-security/git-security/README.md)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
