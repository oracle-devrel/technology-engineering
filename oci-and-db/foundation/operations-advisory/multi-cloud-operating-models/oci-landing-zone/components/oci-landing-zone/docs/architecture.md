# Architecture and state

The Landing Zone separates tenancy, environment, platform, and project changes
so reviewers can understand the scope of each plan.

```mermaid
flowchart LR
  B[Bootstrap readiness] --> O0[OP00 global IAM]
  O0 --> O1[OP01 shared foundation]
  O1 --> O2[OP02 environment]
  O2 -. optional .-> O3[OP03 platform]
  O2 --> O4[OP04 project]
  O4 --> H[Project handoff]
```

## Ownership

Cloud Operators own every phase through OP04. Project Teams receive no tenancy
administrative access and begin work only after OP04. The project handoff is the
only contract with the Multi-Cloud Control Plane; it carries identifiers and
network references, never credentials.

## State isolation

All phases may share one protected OCI Object Storage bucket, but each uses a
separate key:

The OP03 runner uses a different private, versioned bucket for project
workload state. Its IAM policy must not authorize the foundation-state bucket.

| Phase | State key |
|---|---|
| OP00 | `op00_manage_global_landing_zone/terraform.tfstate` |
| OP01 | `op01_manage_landing_zone_environment/terraform.tfstate` |
| OP02 | `op02_manage_environment/{environment}/terraform.tfstate` |
| OP03 | `op03_manage_platform_gitops/terraform.tfstate` |
| OP04 | `op04_manage_project/{environment}/{project}/terraform.tfstate` |

The workflows obtain the bucket, namespace, and region from GitHub repository
variables. OCI providers and state access use the private foundation runner's
Instance Principal identity. Bootstrap readiness is a read-only workflow and
has no Terraform state.

## Official blueprint boundary

OE `v3.1.0` owns the hierarchy, naming, and standard IAM definitions. The local
Jsonnet adapter projects its output into the OP00–OP04 state boundaries and
adds only the MCPP runner policies that OE does not provide. It also removes
OE `v3.1.0`'s obsolete `allow service osms` statement: the legacy
[OS Management service reached end of life on April 23, 2025](https://docs.oracle.com/iaas/os-management/osms/alx-overview.htm),
and current OCI IAM rejects the retired `osms` service principal. OS Management
Hub access must use its current, separately scoped policies.

OE `v3.1.0` also emits a child-specific Security Zone for the shared network
compartment in addition to the parent CIS zone. OCI prohibits a platform
resource in the parent zone from using a subnet in that child zone. Until the
upstream generator places dependent resources under one common zone, the
protected adapter omits only the shared-network child target. Shared network
and platform resources therefore inherit the same CIS Level 1 zone from
`CMP-LANDINGZONE-KEY`; the environment-level zone remains unchanged.

OE `v3.1.0` derives an example Bastion SSH source by adding host offset `123`
to the Hub management subnet. OCI Bastion assigns its private endpoint
dynamically, so that example is not an executable access contract. The
protected adapter removes the example when
`platform_bastion_private_endpoint_cidr` is `null` and otherwise replaces it
with the exact OCI-assigned `/32`. No broader management-subnet SSH source is
accepted.

The adapter derives every DRG route-distribution statement key from its owning
distribution. This preserves the Hub E routes while satisfying the official
networking module's globally unique flattened-statement key contract.

The current OE model creates one project compartment under the environment's
`PROJECTS` compartment. Application, database, and infrastructure values in the
handoff are logical compatibility fields and contain the same project
compartment OCID. The application, database, and infrastructure *subnets*
remain distinct because they are part of the official project-network model.
The MCPP runner extension grants project NSG management in that exact project
compartment. It does not grant NSG management across the shared environment
network compartment; the project manifest combines the handed-off project
compartment OCID with the handed-off shared VCN OCID.

OCI resolves a named compartment in a policy statement as a direct child of
the compartment where that policy is attached. The adapter therefore attaches
the project GitOps policy to the environment's `PROJECTS` compartment and the
network/security GitOps policies to the environment compartment. Their
statements still target only the exact project, network, or security child
compartment; attaching them at the parent makes those scopes effective without
broadening them.

Creating or deleting a project NSG also changes its shared VCN. The network
GitOps policy therefore adds OCI's narrowly conditioned `manage vcns` grant
only for `CreateNetworkSecurityGroup` and `DeleteNetworkSecurityGroup` in the
environment network compartment. The existing `use virtual-network-family`
grant remains the read/use boundary for other VCN operations.

## Change path

Pull requests validate and plan; an approved merge to `main` applies. Workflows
clone the approved OCI orchestrator at its pinned commit and pass the JSON files
from the selected phase as Terraform variable files.

Because phases depend on earlier outputs, deploy them in order for a new
tenancy. Later maintenance remains isolated to the phase that owns the changed
resource. A downstream phase reads the exact Orchestrator-generated dependency
JSON content recorded in protected upstream Terraform state
(`compartments_output.json`, `network_output.json`, and similar) and passes the
resulting file paths through a temporary `.tfvars.json` file. The temporary
file only binds official Orchestrator dependency variables to JSON files; it
does not define resources or replace the Orchestrator.
