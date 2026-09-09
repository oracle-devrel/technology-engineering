# Reference capabilities

This page lists the Day 1 resources and Day 2 operations included in the
supplied MCCP reference.

The supplied reference implementation includes these patterns. New resource
families can be added through the [extension model](architecture.md#extension-model)
without changing the [target operating model](architecture.md#target-operating-model).
Use the supplied patterns only from a handed-off project repository and follow the
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

The supplied OCI Compute example uses `eu-frankfurt-1`. A reference deployment
in another region needs a region-specific Compute template and image reference.

The Azure and Google Cloud reference patterns consume existing foundation
references. They do not create projects, resource groups, IAM, networks,
subnets, NSGs, service accounts, ODB Networks, or ODB Subnets.

## Lifecycle operations (Day 2)

| Operation | GitHub interface | Optional UI | Optional Codex plugin |
| --- | --- | --- | --- |
| OCI Autonomous Database start/stop | Yes | Yes | Yes |
| OCI Compute `deploy-agent` | Yes | Yes | Yes |

ADB start/stop operates the database. `deploy-agent` is the worked example of
the SSH execution path: it records `/opt/agents/<agent_type>.installed` on the
target instance and installs no third-party software. Replace its playbook with
a real installer as your first extension — the governed chain around it, from
catalog entry to execution, is already complete. See the
[extension model](architecture.md#extension-model).

Azure and Google Cloud lifecycle operations are not supplied in this reference.

Before submitting requests, complete the installation, the cloud handoff, and the
[first-project acceptance check](verify-secret-isolation.md), then run one
request through the [GitHub interface](../usage/github-interface.md) on the
customer runners and identities.
