# Multi-Cloud Plane

Multi-Cloud Plane is the optional MCCP guided interface. It lets Project
Teams select an approved catalog entry and open a pull request in an already
handed-off project repository. The canonical MCCP documentation defines the
[supported request surface](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/support.md)
and [Project Team workflow](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md).

## Installation

Cloud Operations copies this component to its UI runtime location and places
the rendered MCCP `mccp-installation.json` beside it. This small non-secret
file identifies the customer organization and approved immutable catalog
revision. Repository layouts and environments are fixed by the installed
release.

Create a local `.env` from `.env.example` and set the GitHub App and session
values outside Git. `GITHUB_ORG` must match the rendered installation
configuration. Use TLS in any shared deployment.

Create and install a dedicated **GitHub App** for the customer organization.
Enable user-to-server authorization and register the exact callback URL. Select
the `gitops-templates` repository, which the UI reads but never writes, plus
only the handed-off project repositories it must serve. Each user authorizes
the App and must already have the project repository access required for the
requested action.

Use these GitHub App repository permissions:

- **Actions: read** and **Checks: read** to display plan/check and execution
  status.
- **Contents: read and write**, **Issues: read and write**, and **Pull
  requests: read and write** for the UI's issue, branch, commit, and PR flow.
- **Metadata: read** is always present and must remain read-only.

The UI does not need a GitHub App private key, an installation-token flow, or
write permission to Actions, Checks, Administration, or Workflows.

Copy the sample configuration before starting. For a local installation, the
sample uses `http://localhost:8011/callback`. For a shared deployment, register
the exact externally visible `https://<host>/callback` URL and configure the
reverse proxy to preserve the original host and HTTPS protocol.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m app.main
```

The application reads `.env` itself, including its configured host and port.
`APP_URL` must match the exact browser origin, including its protocol and port.
The signed-in user remains the authorizing identity for project writes; an
optional server token may read the catalog but cannot bypass user-scoped
project authorization.

## Security boundary

The UI creates GitHub issues, branches, commits, and pull requests. It does not
hold cloud credentials, approve or merge requests, or execute Terraform or
Ansible. See the canonical MCCP
[security guidance](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/security.md).
