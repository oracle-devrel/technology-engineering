# Multi-Cloud Control Plane documentation

The Multi-Cloud Control Plane (MCCP) is a GitOps operating model for governed
OCI, Azure, and Google Cloud resource requests. Every request becomes a pull
request, receives human review, and runs through trusted automation owned by
Cloud Operations.

Cloud Operations installs the shared control-plane repositories, configures
trusted runners, and creates each project repository with its approved
environment handoff. The handoff records the cloud, environment, region,
network, and execution references that the Project Team may use. It is already
present when the Project Team receives the repository; the Project Team starts
from that handed-off boundary.

After handoff, Project Teams manage approved Day 1 resource changes and Day 2
lifecycle operations in their project repository. Day 1 means creating,
updating, or deleting desired infrastructure. Day 2 means running a supported
operation against an existing resource, such as starting or stopping an OCI
Autonomous Database.

## Cloud Operations

[Install MCCP](installation/README.md) to publish the shared repositories,
configure trusted runners, and verify the organization-level controls. For a
technical overview first, see [How the Control Plane works](reference/architecture.md).

## Project Teams

[Use MCCP](usage/README.md) to prepare approved Day 1 and Day 2 requests from
an already prepared project repository. The GitHub interface is always
available; the other two interfaces are optional ways to prepare the same pull
request.

| Interface | Entry point |
| --- | --- |
| GitHub interface | [GitHub interface](usage/github-interface.md) |
| Optional form-led interface | [Multi-Cloud Plane UI](usage/optional-ui.md) |
| Optional conversational interface | [Codex plugin](usage/codex-plugin.md) |

## Governance and reference

[Reference](reference/README.md) covers architecture, supported scope, testing,
security, and GitHub plan limitations. Check
[what MCCP supports](reference/support.md) before enabling a cloud or request
type.
