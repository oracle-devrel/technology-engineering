# Reference capabilities

Use this page to see what the MCCP reference includes. Cloud Operations enables the relevant foundation and runner access for each project. Each request follows the [same review and execution process](../usage/request-lifecycle.md).

| Cloud | Resources you can request | Operations you can request |
| --- | --- | --- |
| Oracle Cloud Infrastructure (OCI) | Project network security groups and approved rules, Compute virtual machines, Autonomous Database | Start or stop Autonomous Database. Run the Compute `deploy-agent` demonstration. |
| Azure | Private Linux VM, Oracle Autonomous Database with private access or public access using a client certificate | — |
| Google Cloud | Private Linux VM, Oracle Autonomous Database Serverless | — |

The Compute `deploy-agent` example writes a marker to show that the approved operation reached its target over SSH. See the [operation catalog](../../repository-sources/gitops-templates/operations-catalog/README.md) for the exact behavior.

## Choose a profile

- **OCI** uses the reviewed environment handoff. The Compute example uses Frankfurt. Other regions need a reviewed regional template and image. [OCI profiles](../../repository-sources/gitops-templates/resources-catalog/README.md#oci--compute)
- **Azure** uses existing foundation resources. The Autonomous Database catalog lists fixed Small, Medium and Large profiles, the networking inputs and the adapter required for public mTLS. [Azure database profiles](../../repository-sources/gitops-templates/resources-catalog/README.md#azure--databases)
- **Google Cloud** uses the existing foundation references in its reviewed handoff. [Google Cloud profiles](../../repository-sources/gitops-templates/resources-catalog/README.md#google--compute)

GitHub, the optional UI and the optional Codex plugin prepare the published resource and operation requests within the scope configured for each interface. Cloud Operations can add capabilities through the [extension model](architecture-details.md#extension-model).
