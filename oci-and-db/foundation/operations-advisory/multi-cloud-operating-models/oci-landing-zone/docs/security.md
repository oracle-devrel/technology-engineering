# Security

Foundation changes can affect the whole tenancy. Restrict the Landing Zone to
the Cloud Operators who are responsible for OCI governance.

Before production rollout:

- Keep the repository private and protect `main`.
- Require independent approval and a successful Terraform plan.
- Pin the OCI orchestrator to an immutable revision. Use repository-approved,
  readable version tags for third-party GitHub Actions and review those tags
  during each release update.
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

## Why `pull_request_target` is acceptable here

The foundation workflows use `pull_request_target` so a pull request can run a
Terraform plan on the private, privileged foundation runner. A repository user
with write access can therefore trigger tenancy-administrator reads and a plan
before the pull request is approved; treat repository write access as a
privileged role.

The workflow rejects fork-based pull requests, checks out the exact base commit
as `trusted`, and checks out the requested commit separately as `request`. It
accepts only phase-specific allowlisted paths with regular-file mode `100644`.
Generated phases are rebuilt with the protected adapter and compared with the
request before Terraform consumes them. `FOUNDATION_AUTOMATION_READY` disables
execution until bootstrap review is complete, and Terraform apply runs only
from a push to protected `main` after merge. Keep all of these controls
together; weakening one requires a new security review of the trigger model.

The project handoff contains identifiers and network references only. Under the
official TBAC hierarchy, it identifies a project root and distinct Application,
Database, and Infrastructure compartments. Its workflow cannot access or write
a project repository. Project repository creation is a separate Control Plane
responsibility.
The OP02 MCCP runner extension creates three fixed, environment-scoped policies
for the `PROJECTS` subtree, shared `NETWORK`, and shared `SECURITY`. They are
limited to the MVP Compute, ADB, and project-NSG contracts; they do not grant a
human TBAC role or general VCN administration.
The shared-VCN policy grants `manage vcns` only when the request operation is
`CreateNetworkSecurityGroup` or `DeleteNetworkSecurityGroup`; general VCN
administration remains outside the project runner boundary.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.

Related operational-security guidance:
[Git Security](https://github.com/oracle-devrel/technology-engineering/tree/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/operational-security/git-security),
[CI/CD Security](https://github.com/oracle-devrel/technology-engineering/tree/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/operational-security/cicd-security),
and [Programmatic Access to OCI for CI/CD Pipelines](https://github.com/oracle-devrel/technology-engineering/tree/OperationsAdvisory-updates2/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/operational-security/programatic-access-cicd).
