# How the foundation works

Your OCI foundation is established in ordered phases. Each phase has its own
Terraform state and pull-request workflow, which limits the scope of a change
and makes approvals easier to understand.

```mermaid
flowchart LR
  B[Bootstrap readiness] --> O0[OP00 tenancy IAM]
  O0 --> O1[OP01 shared landing zone]
  O1 --> O2[OP02 environment]
  O2 -. optional .-> O3[OP03 platform]
  O2 --> O4[OP04 project foundation]
  O4 --> H[Project handoff]
```

- **Bootstrap readiness** verifies the administrator-created private foundation
  runner, its Instance Principal identity, and the private state bucket. It
  creates no OCI resource and has no Terraform state.
- **OP00** configures tenancy-wide groups and policies.
- **OP01** creates the shared landing-zone structure and network.
- **OP02** creates an environment such as production or development.
- **OP03** creates the control-plane platform foundation.
- **OP04** creates the official OE project compartment, group, and policies.

The project hierarchy follows OE `v3.1.0`: each environment has a `PROJECTS`
container and each project has one compartment below it. Older OE `v2.x`
examples used application, database, and infrastructure child compartments;
this asset does not recreate that retired hierarchy. The three existing
Control Plane handoff fields are compatibility aliases for the same project
compartment OCID.

After OP04, the workflow produces `project-foundation-handoff.json` for the
Control Plane and `environment_information.md` for your teams. The Landing Zone
does not create the project repository or deploy project workloads.

OP04 foundation identities are environment-specific: `dev-<project>`,
`test-<project>`, `uat-<project>`, and `prod-<project>`. Dev, test, and UAT
handoffs target the shared `nonprod-<project>` repository; production targets
`prod-<project>`. Each handoff is written to
`environments/<environment>/environment_information.md`.

Cloud Operators control the foundation. Project Teams work only in their
handed-off project repositories, where the normal pull-request approval process
continues to apply.
