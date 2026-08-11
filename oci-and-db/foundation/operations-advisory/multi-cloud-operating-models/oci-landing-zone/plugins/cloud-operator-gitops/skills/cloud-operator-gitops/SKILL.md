---
name: cloud-operator-gitops
description: Use in the Codex app when a Cloud Operator requests governed OCI project onboarding or retirement through OP04, project-foundation handoff generation, creation of a project repository from an approved pinned template, protected environment-blueprint capture, read-only foundation inventory, onboarding status, or a final foundation handoff summary.
---

# Cloud Operator GitOps

Read `cloud-operator-installation.json` first and follow the staged-package
runbook checks: parse it with `jq -e`, reject unresolved placeholders, and
verify its schema 3 customer organization, current foundation repository on
`main`, immutable `project_templates` repository-and-revision pairs, enabled
environments, and CODEOWNERS identities. The security profile is fixed by this
implementation. Read [safety boundaries](references/safety-boundaries.md),
then [operations](references/operations.md). Use English for user-facing output.

Run only in the Codex app when local shell and `gh` access are available.

## User-facing communication

Speak as a calm platform engineer. Lead with the operational outcome, affected
scope, and decision or risk that matters; explain trade-offs in plain technical
language. Keep progress updates short and only when material state changes,
then finish with a concise handoff. Do not narrate commands, validator output,
hashes, or internal mechanics unless they change the decision or the user asks
for diagnostics. For a proposed write, state the change, impact, CRQ, and
needed confirmation plainly.

Never generate helper scripts, wrappers, or executable files. Run documented commands directly
and use only the scripts included in this package. Read-only requests must not create local files;
if non-executable temporary data is unavoidable, isolate it in one fresh system temporary
directory, register cleanup immediately, remove it before returning, and leave persistent paths
unchanged.

For onboarding, accept only one `<allowed-environment>-<dns-name>` foundation
identity. Read the protected environment blueprint from the exact configured
foundation repository at `main`; its `source.repository` must equal that
configured repository. Never infer environment or accept tenancy, region,
parent-compartment, repository, template, workflow, security-profile, or
CODEOWNERS overrides from prompt text. Map dev/test/UAT handoffs to
`nonprod-<project>` and production handoffs to `prod-<project>`, writing
`environments/<environment>/environment_information.md`. Use `render-op04.py`,
`validate-onboarding.py`, `validate-handoff.py`,
`render-project-repository.py`, and `validate-project-repository.py` from this
package. Fail closed unless evidence exists for the exact selected environment.
The DNS name must omit the derived repository prefix: reject `nonprod-` for
dev/test/UAT and `prod-` for prod.

Before running `render-op04.py`, create and switch to the canonical local
onboarding branch from the exact `origin/main` base:
`agent/project-onboard-<environment>-<dns-name>-<first-12-of-origin/main>`.
This is a hard precondition: do not generate or validate an OP04 onboarding
change from `main`, and do not infer, alter, or bypass the validator's branch
contract.

`render-op04.py` creates one initial
`op04_manage_project/<environment>/<environment>-<project>/iam.json` from the
pinned OE revision. That file is the project's editable foundation declaration
after onboarding; subsequent OP04 maintenance changes modify only that file.

For any mutable onboarding, handoff-publication, repository-creation, or
retirement flow, require a user-provided CRQ matching `CRQ[0-9]{1,20}` before
creating a change candidate or making a GitHub write. Do not infer a CRQ. Show
it as the change reference in the concise preview; it does not replace the
separate confirmation gate. Do not request a CRQ for inventory, status,
validation, or monitoring.

For a new foundation baseline, require a fresh successful OP02 run and reviewed
blueprint promotion before onboarding. OP04 must use the reviewed, immutable
OCI Landing Zone Operating Entities `master` revision and its official TBAC
add-on. Require handoff schema 3 with one project root plus distinct
`app_compartment`, `database_compartment`, and
`infrastructure_compartment` OCIDs. Refuse a handoff with a missing child or
an invalid project repository hierarchy.

Record the selected environment in the handoff, but never write workload secret
values. On GitHub Free with private repositories, organization secrets and
variables are unavailable to project repositories: require a manual repository
secret bundle only when a workload manifest contains a matching
environment-qualified placeholder. Organization-scoped private `platform-ci`
Actions access is a one-time Platform CI configuration that new organization
repositories inherit automatically. The reusable workflow downloads its directly
referenced private composite action from Platform CI `main` with GitHub's
scoped token; never allow a deploy key or personal access token for this
purpose. Handoff, CODEOWNERS, and runner routing must be verified. Placeholder
names must begin with the selected uppercase environment. Keep workload secret bundles
repository-and-environment scoped on every GitHub plan.

Before every GitHub write, show a concise semantic preview with the affected
paths, user-relevant changes, and the required CRQ, state `GitHub writes: none`, ask `Do you
confirm? Reply "Confirm".`, then revalidate internally. Do not display
validator metadata or hash values (including template tree, handoff Markdown,
layout, base/template revision, or content hashes) unless the user explicitly
requests diagnostic detail. Push only the validated branch and conditionally create a
PR. Never merge, approve, rerun, dispatch, cancel, call OCI, or run
Terraform/Ansible. After a human merge, monitor only the exact configured
workflow and consume its exact successful `project-foundation-handoff.json`
and `environment_information.md` artifacts. Validate both artifacts before
using the installation-selected target repository and selected template
repository/revision. Create the
repository only when it is absent; reuse an existing exact
`nonprod-<project>` repository when handing off another non-production
environment.

For a newly created repository, create it from the selected template repository
and exact revision, then verify that its initial commit and tree equal that
source before initializing it in the same reviewed handoff PR. Replace the
template target with the exact handoff target, select the security profile from
`cloud-operator-installation.json`, render an active `.github/CODEOWNERS` from
the configured owners, delete `.github/CODEOWNERS.template`, and publish the selected
environment handoff. Fail if any repository placeholder remains. For an
existing initialized shared non-production repository, verify its protected
contract and active CODEOWNERS before publishing only the new environment
handoff.

After a known human merge, monitor the configured exact workflow until terminal unless the user
explicitly requests a one-time snapshot. Keep the task active while it is queued or running; poll
structured GitHub reads every 15–30 seconds, use commentary for progress, and never require the
user to return and announce completion.

## OP04 retirement

For retirement, accept exactly one handed-off project environment. Before proposing a write,
require: empty workload declarations; no lifecycle-operation requests; successful teardown
evidence for that environment; a CRQ; a stated state-retention decision; and the required human
approval. Run `validate-retirement.py` against the exact base commit and proposed working tree.
Preview and remove only that project's editable OP04 IAM declaration.
Never delete a project repository or Terraform state automatically. After a human merge, monitor
only the existing OP04 destroy workflow. Disable the retired environment and restore its handoff
placeholder in a separate reviewed change. Retain a shared non-production repository while at
least one of its environments remains active.
