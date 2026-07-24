---
name: cloud-operator-gitops
description: Use in the Codex app when a Cloud Operator requests governed OCI project onboarding through OP04, project-foundation handoff generation, creation of a project repository from an approved pinned template, protected environment-blueprint capture, read-only foundation inventory, onboarding status, or a final foundation handoff summary.
---

# Cloud Operator GitOps

Read `deployment-contract.json` first. Fail closed unless it names the exact customer organization, canonical repositories, approved immutable refs, allowed environments, project-name pattern, and workflow names. Read [safety boundaries](references/safety-boundaries.md), then [operations](references/operations.md). Use English for user-facing output.

Run only in the Codex app when local shell and `gh` access are available.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the scripts included in this package. Read-only requests must not create local files;
if non-executable temporary data is unavoidable, isolate it in one fresh system temporary
directory, register cleanup immediately, remove it before returning, and leave persistent paths
unchanged.

For onboarding, accept only one `<allowed-environment>-<dns-name>` foundation
identity. Read the protected environment blueprint from exact landing-zone
`main`; never infer environment or accept tenancy, region,
parent-compartment, repository, template, workflow, security-profile, or
CODEOWNERS overrides from prompt text. Map dev/test/UAT handoffs to
`nonprod-<project>` and production handoffs to `prod-<project>`, writing
`environments/<environment>/environment_information.md`. Use `render-op04.py`,
`validate-onboarding.py`, `validate-handoff.py`,
`render-project-repository.py`, and `validate-project-repository.py` from this
package. Fail closed unless evidence exists for the exact selected environment.

OP04 must be generated from the contract-pinned OE `v3.1.0` source. Preserve
its single project-compartment hierarchy. In the validated handoff,
`app_compartment`, `database_compartment`, and
`infrastructure_compartment` must be aliases for that same project
compartment OCID; never recreate the retired OE `v2.x` child hierarchy.

Record the selected environment in the handoff, but never write workload secret
values. Project-repository setup uses one explicitly selected repository secret
bundle and readiness variable per environment; placeholder names must begin with
the selected uppercase environment.

When the Cloud Operator has verified a regular ExaCS database that was not
provisioned by Terraform, register it only as a platform-owned handoff artifact
at `environments/<environment>/exacs-databases.json`. Require its Database,
compartment, and VM cluster OCIDs plus each approved target Database Home OCID
and exact version. Do not infer these values, call OCI to discover them, or
accept secret values. Do not create or modify this registry unless the operator
explicitly requests the registration and confirms the verified resource facts.

Before every GitHub write, show a semantic preview with paths and hashes,
state `GitHub writes: none`, ask `Do you confirm? Reply "Confirm".`, then
revalidate hashes. Push only the validated branch and conditionally create a
PR. Never merge, approve, rerun, dispatch, cancel, call OCI, or run
Terraform/Ansible. After a human merge, monitor only the exact configured
workflow and consume its exact successful `project-foundation-handoff.json`
and `environment_information.md` artifacts. Validate both artifacts before
using the contract-selected target repository and pinned template. Create the
repository only when it is absent; reuse an existing exact
`nonprod-<project>` repository when handing off another non-production
environment.

For a newly created repository, verify that its initial tree equals the pinned
template tree, then initialize it in the same reviewed handoff PR. Replace the
template target with the exact handoff target, select the security profile from
`deployment-contract.json`, render an active `.github/CODEOWNERS` from the
contract owners, delete `.github/CODEOWNERS.template`, and publish the selected
environment handoff. Fail if any repository placeholder remains. For an
existing initialized shared non-production repository, verify its protected
contract and active CODEOWNERS before publishing only the new environment
handoff. An explicitly requested verified ExaCS registry update remains a
separate allowed handoff artifact. The optional Multi-Cloud Control Plane UI
operates handed-off repositories; it is not a bootstrap tool.

After a known human merge, monitor the configured exact workflow until terminal unless the user
explicitly requests a one-time snapshot. Keep the task active while it is queued or running; poll
structured GitHub reads every 15–30 seconds, use commentary for progress, and never require the
user to return and announce completion.
