# MVP capabilities

This page lists the Day 1 resources and Day 2 operations included in the
supplied MCCP MVP, and the evidence behind them.

This is the currently qualified request surface, not an unrestricted catalog.
Use it only from a handed-off project repository and follow the
[request lifecycle](../usage/request-lifecycle.md) for its review and boundary
requirements.

## Resource requests (Day 1)

The GitHub interface, optional UI, and optional Codex plugin support every
resource in this table.

| Cloud | Resources |
| --- | --- |
| OCI | Project network security groups (NSGs), Compute, Autonomous Database |
| Azure | Private Linux VM, Oracle Autonomous Database |
| Google Cloud | Private Linux VM, Oracle Autonomous Database Serverless |

The Azure and Google Cloud implementations consume existing foundation
references. They do not create projects, resource groups, IAM, networks,
subnets, NSGs, service accounts, ODB Networks, or ODB Subnets.

## Lifecycle operations (Day 2)

| Operation | GitHub interface | Optional UI | Optional Codex plugin |
| --- | --- | --- | --- |
| OCI Autonomous Database start/stop | Yes | Yes | Yes |
| OCI Compute `deploy-agent` | Yes | Yes | No |

ADB start/stop operates the database. `deploy-agent` is the worked example of
the SSH execution path: it records `/opt/agents/<agent_type>.installed` on the
target instance and installs no third-party software. Replace its playbook with
a real installer as your first extension — the governed chain around it, from
catalog entry to evidence, is already complete. See the
[extension model](architecture.md#extension-model).

Azure and Google Cloud lifecycle operations are not supplied in this release.

## Qualification evidence

| Scope | Evidence |
| --- | --- |
| OCI resources and lifecycle operations | Live OCI smoke tests |
| Azure resources | Provider-schema validation and credential-free mocked Terraform lifecycle tests |
| Google Cloud resources | Provider-schema validation and credential-free mocked Terraform lifecycle tests |

Maintainer qualification also covered every supplied JSON file and catalog
schema, create/update/delete validation including invalid handoffs, public IPs,
secret placeholders, unknown clouds and mixed environments, and synthetic Git
repositories for requests, project handoff, and environment retirement.

No live Azure or Google Cloud apply was performed for this publication. Do not
represent either implementation as live-cloud certified. Customer extensions are
unqualified until the complete [extension model](architecture.md#extension-model)
is implemented and tested.

Before enabling requests, complete the installation, the cloud handoff, and the
[first-project acceptance check](verify-secret-isolation.md), then run one
request through the [GitHub interface](../usage/github-interface.md) on the
customer runners and identities.
