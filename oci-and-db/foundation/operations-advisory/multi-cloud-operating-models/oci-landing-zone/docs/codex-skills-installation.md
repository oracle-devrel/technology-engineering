# Install and use the Codex GitOps skills

Use this runbook when adopting this reference implementation in a new customer
GitHub organization and you want to use the optional Codex assistants. It
covers the local Cloud Operator and Project GitOps skills after the foundation
and Multi-Cloud Control Plane (MCCP) repositories have been prepared.

The assistants prepare validated Git changes and pull requests. They do not
replace the foundation or project workflows, merge pull requests, run
Terraform or Ansible, or operate OCI directly.

## 1. Prerequisites

Prepare the customer installation before installing either skill:

- A private customer GitHub organization and an OCI foundation that follows
  this Landing Zone runbook.
- The private `platform-ci`, `nonprod-project-template`,
  `prod-project-template`, and `gitops-templates` repositories created by the
  [MCCP deployment runbook](../../multi-cloud-control-plane/docs/deployment.md).
- A completed OP03 and OP02 for the environment that will host the first
  project. OP03 creates the project runner identity; OP02 creates the fixed
  environment-level runner policies.
- Codex App with local-shell access, Git, `gh`, `jq`, `rg`, Perl, and Python
  3.11 or later.
- An authenticated GitHub CLI identity with read access to the foundation,
  template, and catalog repositories. Cloud Operators also need permission to
  create the selected project repository and pull requests.

Check the local identity before starting:

```bash
gh auth status
git --version
jq --version
rg --version
perl --version
python3 --version
```

Do not put credentials, Terraform state, workflow artifacts, or workload
secret values in the staged packages or this source repository.

## 2. Render the customer-specific packages

Build the shared MCCP repositories first. In particular, record immutable
commits for `nonprod-project-template`, `prod-project-template`, and
`gitops-templates` after they have been created in the customer organization.

Then follow these existing recipes exactly:

1. Render and validate the Cloud Operator package, including
   `cloud-operator-installation.json`, in [Create the Cloud Operator
   installation file](deployment.md#6-create-the-cloud-operator-installation-file).
2. Render and validate the Project GitOps package, including
   `mccp-installation.json`, in [Prepare the shared
   repositories](../../multi-cloud-control-plane/docs/deployment.md#1-prepare-the-shared-repositories).

Both JSON files are non-secret installation configuration. They must contain
the selected customer organization and immutable repository references. Verify
both packages before installing them:

```bash
jq -e . "$STAGE/cloud-operator-gitops/cloud-operator-installation.json" >/dev/null
jq -e . "$STAGE/project-gitops/mccp-installation.json" >/dev/null

if rg -n '__[A-Z0-9_]+__' \
  "$STAGE/cloud-operator-gitops/cloud-operator-installation.json" \
  "$STAGE/project-gitops/mccp-installation.json"
then
  echo 'Unresolved installation placeholders remain' >&2
  exit 1
fi
```

Install the staged directories, never the unrendered `plugins/` directories
from this publication.

## 3. Install the local skills

Use the Codex plugin process approved by the customer organization when one is
available. For a user-scoped local Codex installation, place each complete,
rendered package in the Codex skills directory. This is the layout used by the
Codex installation; keep the installation JSON beside the skill package.

```bash
export CODEX_SKILLS_DIR="${CODEX_HOME:-$HOME/.codex}/skills"

test -d "$STAGE/cloud-operator-gitops"
test -d "$STAGE/project-gitops"
test ! -e "$CODEX_SKILLS_DIR/cloud-operator-gitops"
test ! -e "$CODEX_SKILLS_DIR/project-gitops"

mkdir -p "$CODEX_SKILLS_DIR"
cp -R "$STAGE/cloud-operator-gitops" "$CODEX_SKILLS_DIR/cloud-operator-gitops"
cp -R "$STAGE/project-gitops" "$CODEX_SKILLS_DIR/project-gitops"
```

Restart Codex if the skills do not appear in its skills list. Codex should show
both `cloud-operator-gitops` and `project-gitops`. Confirm that the installed
configuration still identifies the intended organization and immutable catalog
or template revisions before using either skill.

```bash
jq '{schema_version, customer_org, foundation, project_templates}' \
  "$CODEX_SKILLS_DIR/cloud-operator-gitops/cloud-operator-installation.json"
jq '{schema_version, customer_org, catalog_revision}' \
  "$CODEX_SKILLS_DIR/project-gitops/mccp-installation.json"
```

Do not copy a package between customer organizations. Render a new package for
each organization and install it separately.

## 4. Run the end-to-end flow

Clone only the customer foundation repository locally, then open Codex App in
that checkout. The skills resolve the configured template, catalog, and
project repositories through GitHub; you do not need local clones of those
repositories.

```bash
git clone "git@github.com:<customer-org>/oci-landing-zone.git"
cd oci-landing-zone
```

### Cloud Operator: OP04 to project handoff

Start with a read-only request to demonstrate the configured boundary:

```text
$cloud-operator-gitops

Show the read-only onboarding status for the configured dev project.
Do not create or modify anything.
```

For a new project, ask the skill to prepare OP04. It validates the selected
environment, prepares the Git change, shows paths and hashes, and waits for an
explicit confirmation before a branch push or pull request. A human reviews
and merges that pull request. The approved workflow creates the schema-3
foundation handoff.

After the successful human-merged OP04 workflow, Cloud Operator GitOps
validates the handoff, creates `nonprod-<project>` from the configured
immutable template when needed, and opens the handoff pull request. It reuses
the shared non-production repository for additional non-production
environments.

### Bootstrap the project repository

Before a Project Team uses Project GitOps, complete the required repository
bootstrap: active CODEOWNERS, project handoff, and runner routing. Private
`platform-ci` Actions access is configured once for the organization and is
inherited by new project repositories. Configure an environment secret bundle
only when the workload manifest contains matching secret placeholders. Follow
[Required GitHub Free bootstrap before Project
GitOps](../../multi-cloud-control-plane/docs/deployment.md#required-github-free-bootstrap-before-project-gitops)
and the applicable paid-plan controls if the organization uses them.

### Project Team: prepare a governed request

Project GitOps can be invoked after the handoff and bootstrap. A read-only
status request is a safe first check:

```text
$project-gitops

Show the read-only status of pull request #42 in the handed-off project
repository. Do not create or modify anything.
```

To demonstrate a governed change without writing to GitHub, ask the skill to
stop after its semantic preview:

```text
$project-gitops

Prepare an OCI Autonomous Database stop request for dev. Stop after the
semantic preview; do not confirm a GitHub write.
```

The preview records the validated catalog provenance and changed paths. A
branch push or pull request occurs only after the user explicitly confirms it;
the subsequent human review and merged workflow remain the deployment gate.

## 5. Update or remove a local installation

When the installation contract or an immutable template/catalog revision
changes, render and validate a new package. Remove the old local package only
after Codex is closed and the new package has been verified. Never edit an
installed customer JSON in place or change its values through a prompt.

The direct GitHub pull-request path remains available if Codex is unavailable
or the optional assistants are not installed.
