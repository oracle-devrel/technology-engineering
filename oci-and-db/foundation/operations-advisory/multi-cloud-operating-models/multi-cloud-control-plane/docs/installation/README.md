# Install the Multi-Cloud Control Plane

This guide is for Cloud Operations. Use it to prepare the shared MCCP
repositories, configure trusted runners, hand over a project boundary, and
verify that the installation is ready for Project Teams.

## Installation path

1. [Prepare shared repositories](installation-runbook.md#1-prepare-the-shared-repositories).
2. [Configure trusted runners](installation-runbook.md#2-configure-trusted-runners).
3. [Onboard an OCI project](installation-runbook.md#3-onboard-an-oci-project).
4. [Verify the installation](installation-runbook.md#4-confirm-the-installation).
5. Use the [security boundaries](../reference/security-boundaries.md) and
   [future hardening guidance](../reference/future-hardening.md) to select and
   operate the appropriate governance model.

The `repository-sources/` directories are the sources of the repositories created by
the installation runbook. Their README files describe each repository's own
technical contract; this section describes how those repositories work
together as one control plane.
