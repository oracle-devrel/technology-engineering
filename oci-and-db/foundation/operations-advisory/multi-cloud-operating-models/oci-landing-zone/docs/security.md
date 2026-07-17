# Security

Foundation changes can affect the whole tenancy. Restrict the Landing Zone to
the Cloud Operators who are responsible for OCI governance.

Before production rollout:

- Keep the repository private and protect `main`.
- Require independent approval and a successful Terraform plan.
- Pin the OCI orchestrator and third-party GitHub Actions to approved versions.
- Use a dedicated runner identity with least-privilege OCI permissions.
- Treat the temporary first-bootstrap identity as privileged, remove its access
  after the permanent runner is verified, and retain the required audit record.
- Isolate, protect, and back up Terraform state for every phase.
- Keep API keys, private keys, runner tokens, passwords, and credentials out of
  Git and project handoffs.
- Test failure recovery, partial applies, runner replacement, audit evidence,
  and state restoration in non-production.

The project handoff contains identifiers and network references only. Its
workflow cannot access or write a project repository. Project repository
creation is a separate Control Plane responsibility.

Review these controls against your organization's security, compliance, data
residency, and change-management requirements before enabling production use.
