# Security

Foundation changes can affect the whole tenancy. Restrict the Landing Zone to
the Cloud Operators who are responsible for OCI governance.

Before production rollout:

- Keep the repository private and protect `main`.
- Require independent approval and a successful Terraform plan.
- Pin the OCI orchestrator and third-party GitHub Actions to approved versions.
- Use a dedicated private foundation runner, bind its dynamic group to the exact
  instance OCID, and do not share it with project workloads.
- Treat the administrator-created foundation identity as privileged. Protect,
  monitor, patch, and replace it through a reviewed procedure.
- Keep the separate foundation and project Terraform state buckets private
  with Object Storage versioning enabled. Bootstrap readiness validates the
  foundation bucket; the OP03 identity preflight validates the project bucket
  contract.
- Keep API keys, private keys, runner tokens, passwords, and credentials out of
  Git and project handoffs.
- Test failure recovery, partial applies, runner replacement, audit evidence,
  and state restoration in non-production.

The project handoff contains identifiers and network references only. Under the
OE `v3.1.0` hierarchy, its application, database, and infrastructure
compartment fields all identify the same project compartment. Its
workflow cannot access or write a project repository. Project repository
creation is a separate Control Plane responsibility.
The OP04 MCPP runner extension limits project NSG management to that exact
project compartment. It does not authorize NSG management across the shared
environment network compartment. Its policies are attached to the immediate
parent of each named target compartment because OCI resolves a named policy
location relative to the policy attachment compartment.
The shared-VCN policy grants `manage vcns` only when the request operation is
`CreateNetworkSecurityGroup` or `DeleteNetworkSecurityGroup`; general VCN
administration remains outside the project runner boundary.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.
