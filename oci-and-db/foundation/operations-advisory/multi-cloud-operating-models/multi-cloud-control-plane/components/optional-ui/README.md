# Multi-Cloud Plane

Multi-Cloud Plane is the optional web request interface for the Multi-Cloud
Control Plane MVP reference blueprint. It lets Project Teams select an approved
catalog entry and open a governed GitHub pull request in an already handed-off
project repository.

It is not a deployment engine. It does not create project repositories, run
OP04, call cloud APIs, read cloud credentials, approve or merge pull requests,
or run Terraform or Ansible. The standard GitHub pull-request flow remains
fully available without this UI.

## Supported request surface

- Day 1 OCI, Azure, and GCP VM and Autonomous Database requests from the
  MCCP V2 catalog, plus OCI project NSGs.
- `nonprod-<project>` repositories: `dev`, `test`, and `uat`.
- `prod-<project>` repositories: `prod`.
- OCI Day 2 `adb-lifecycle` and `deploy-agent` requests in every supported OCI
  environment, including `prod`.
- Resource create, update, and delete requests for the supported Day 1
  resources. The same generic manifest editor is used for OCI, Azure, and
  GCP, so the UI does not carry cloud-specific deployment code.

Azure and GCP Day 2 remain outside this MVP. Teams may always use the direct
GitHub PR flow or the Project GitOps skill instead; both produce the same
governed V2 artifacts.

## Installation

The platform team copies this component to its UI runtime location and places
the rendered MCCP `mccp-installation.json` beside it. This small non-secret
file identifies the customer organization and approved immutable catalog
revision. Repository layouts and environments are fixed by this V2 reference
blueprint.

Create a local `.env` from `.env.example` and set the GitHub App and session
values outside Git. `GITHUB_ORG` must match the rendered installation
configuration. Use TLS in
any shared deployment.

For a local demo that coexists with another UI, create and install a separate
**GitHub App** for this installation. Enable user-to-server authorization and
register the exact callback URL `http://localhost:8011/callback`. Install the
App on the configured organization and select the `gitops-templates` catalog
repository, which the UI reads but never writes, plus only the handed-off
project repositories it must serve. Then each user authorizes the App and must
already have the repository access needed for the requested action. Installation
gives the App its organization and repository access; user authorization lets
the UI act on behalf of that user. Do not reuse another organization's client
ID or secret.

Use these GitHub App repository permissions:

- **Actions: read** and **Checks: read** to display plan/check and execution
  status.
- **Contents: read and write**, **Issues: read and write**, and **Pull
  requests: read and write** for the UI's issue, branch, commit, and PR flow.
- **Metadata: read** is always present and must remain read-only.

The UI does not need a GitHub App private key, an installation-token flow, or
write permission to Actions, Checks, Administration, or Workflows.

For a shared deployment, register the exact externally visible
`https://<host>/callback` URL and configure the reverse proxy to preserve the
original host and HTTPS protocol. This MVP runs as one UI process/replica; use
a shared token and session store before scaling it horizontally.

Copy the sample configuration before starting. The sample environment file
uses port `8011`; a customer may choose another address only when the exact
matching callback URL is registered with GitHub.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8011
```

The application reads `.env` itself. `APP_URL` must be the exact browser
origin used to access the UI, including its protocol and port.

The signed-in user remains the authorizing identity for project writes. An
optional server token may read the catalog but never bypasses user-scoped
project write authorization.

## V2 paths

Every request uses exactly one cloud/environment/region tuple:

- Azure VM: `azure/<environment>/<region>/compute/compute.json`
- Azure ADB: `azure/<environment>/<region>/database/database.json`
- GCP VM: `gcp/<environment>/<region>/compute/compute.json`
- GCP ADB: `gcp/<environment>/<region>/workloads/adb.json`
- OCI paths follow the same environment-aware layout.

Handoff suggestions come only from
`environments/<environment>/environment_information.md`. Runtime secrets are
represented by environment-qualified placeholders; their values remain in the
project repository secret bundle. The update editor rejects literal password
and key values for the same reason.

## Security boundary

The UI creates only an issue, branch, commit, and pull request. GitHub review,
the shared workflow, and the trusted runner retain control of plan, approval,
and apply. See the parent MCCP [security guidance](../../docs/security.md).
