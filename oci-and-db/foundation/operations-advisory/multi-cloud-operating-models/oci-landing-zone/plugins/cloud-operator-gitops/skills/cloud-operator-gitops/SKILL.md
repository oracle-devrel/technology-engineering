---
name: cloud-operator-gitops
description: Use in the Codex app when a Cloud Operator requests governed OCI project onboarding through OP04, artifact-only project-foundation handoff generation, protected environment-blueprint capture, read-only foundation inventory, onboarding status, or a final foundation handoff summary.
---

# Cloud Operator GitOps

Read `deployment-contract.json` first. Fail closed unless it names the exact customer organization, canonical repositories, approved immutable refs, allowed environments, project-name pattern, and workflow names. Read [safety boundaries](references/safety-boundaries.md), then [operations](references/operations.md). Use English for user-facing output.

Run only in the Codex app when local shell and `gh` access are available.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the scripts included in this package. Read-only requests must not create local files;
if non-executable temporary data is unavoidable, isolate it in one fresh system temporary
directory, register cleanup immediately, remove it before returning, and leave persistent paths
unchanged.

For onboarding, accept only one `<allowed-environment>-<dns-name>` foundation identity. Read the protected environment blueprint from exact landing-zone `main`; never infer environment or accept tenancy, region, parent-compartment, repository, template, or workflow overrides from prompt text. Map dev/test/UAT handoffs to `nonprod-<project>` and production handoffs to `prod-<project>`, writing `environments/<environment>/environment_information.md`. Use `render-op04.py` and `validate-onboarding.py` from this package. Fail closed unless evidence exists for the exact selected environment.

Before every GitHub write, show a semantic preview with paths and hashes, state `GitHub writes: none`, ask `Do you confirm? Reply "Confirm".`, then revalidate hashes. Push only the validated branch and conditionally create a PR. Never merge, approve, rerun, dispatch, cancel, call OCI, or run Terraform/Ansible. After a human merge, monitor only the exact configured workflow and consume its exact successful `project-foundation-handoff.json` and `enviroment_information.md` artifacts. Stop there: project repository creation belongs to the Multi-Cloud Control Plane.

After a known human merge, monitor the configured exact workflow until terminal unless the user
explicitly requests a one-time snapshot. Keep the task active while it is queued or running; poll
structured GitHub reads every 15–30 seconds, use commentary for progress, and never require the
user to return and announce completion.
