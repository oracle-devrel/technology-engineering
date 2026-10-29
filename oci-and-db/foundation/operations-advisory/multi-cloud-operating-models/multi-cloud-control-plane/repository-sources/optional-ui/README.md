# AI Operations UI

AI Operations is the project workspace for consulting declared resources, requesting infrastructure changes, preparing published operations and investigating workflow failures. MCCP provides its catalogs, project boundaries, human review and trusted execution. The same `project-gitops` skill serves Codex and the web assistant. Catalog forms remain available as a structured request route. The canonical MCCP documentation defines the [Reference capabilities](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/support.md) and [Project Team workflow](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/README.md).

## Installation

Cloud Operations copies this component to its UI runtime location. The UI uses its configured GitHub organization and the current `gitops-templates` catalog on `main`. Repository layouts and environments are fixed by the installed release.

Create a local `.env` from `.env.example` and set the GitHub App and session values outside Git. `GITHUB_ORG` must match the rendered installation configuration. Use TLS in any shared deployment.

Create and install a dedicated **GitHub App** for the customer organization. Enable user-to-server authorization and register the exact callback URL. Select the `gitops-templates` repository, which the UI reads but never writes, plus only the handed-off project repositories it must serve. Each user authorizes the App and must already have the project repository access required for the requested action.

Use these GitHub App repository permissions:

- **Actions: read** and **Checks: read** to display plan/check and execution status.
- **Contents: read and write**, **Issues: read and write**, and **Pull requests: read and write** for the UI's issue, branch, commit, and PR flow.
- **Metadata: read** is always present and must remain read-only.

The UI does not need a GitHub App private key, an installation-token flow, or write permission to Actions, Checks, Administration, or Workflows.

## Catalog boundary

The catalog is the UI's complete Day 1 contract. The UI renders only documented placeholders; it does not expose catalog literals as editable inputs or provide an arbitrary JSON editor. OCI Compute and Autonomous Database capacity profiles therefore remain fixed. The single OCI project-NSG catalog template supports a new NSG with zero or more TCP ingress and egress rules, or additive rules on an existing NSG. The UI renders destination ports as integers and rejects a rule key that already exists.

Copy the sample configuration before starting. For a local installation, the sample uses `http://localhost:8011/callback`. For a shared deployment, register the exact externally visible `https://<host>/callback` URL and configure the reverse proxy to preserve the original host and HTTPS protocol.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m app.main
```

The application reads `.env` itself, including its configured host and port. `APP_URL` must match the exact browser origin, including its protocol and port. The signed-in user remains the authorizing identity for project writes; an optional server token may read the catalog but cannot bypass user-scoped project authorization.

## Security boundary

The UI creates GitHub issues, branches, commits, and pull requests. It does not hold cloud credentials, approve or merge requests, or execute Terraform or Ansible. See the canonical MCCP [security guidance](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/security.md).

## Local chat demo

The optional chat runs the existing `project-gitops` skill through a local Codex app-server process. It is a single-presenter MVP for the governed projects available to that presenter, disabled by default. Existing catalog forms remain available. This prototype relies on the skill for semantic previews and the standalone `confirm` gate; it is not a shared production agent service.

Install Codex CLI, GitHub CLI (`gh`), and Git on the UI host, and authenticate Codex there. The integration was checked with Codex CLI 0.165.0. In the UI's local `.env`, set `CHAT_ENABLED=true`, `CHAT_DEMO_LOGIN=<presenter-github-login>` and optionally `CHAT_DEMO_PROJECT=<preferred-project-repository>` for a home-page shortcut. The installation must use `GITHUB_ORG=multicloud-control-plane`, matching the skill's configured organization. Set `CHAT_SKILL_PATH` to the absolute path of the bundled `project-gitops/SKILL.md` when running an installed copy of the UI; the source checkout resolves it automatically. An optional `CHAT_MODEL` selects the Codex model. `APP_URL` must match the exact browser origin. Start the UI with `.venv/bin/python -m app.main` from this directory.

Sign in as the configured presenter, select any project you can write to, and open **AI Operations**. Ask for an inventory or a supported catalog resource in the selected OCI scope. Non-production repositories use dev; production repositories use prod. Supply the CRQ and any missing values, review the skill's proposal, then send `confirm` as its own message to publish the PR. Human approval and merge remain necessary before the existing protected workflow deploys the resource. A supported demonstration can use a Small Compute request followed by a PR status query.

The request panel reads selected resources or operation targets from the skill's local candidate JSON. It shows the scope, CRQ, capacity or operation action, manifest and runtime secret key names. Values are never displayed in the panel. The full semantic preview in chat remains the confirmation reference. The integration uses Codex's experimental dynamic-tool interface to update this panel; keep the checked CLI version for the demo.

For a published or existing PR, the panel reads GitHub independently. **Refresh status** checks the latest PR head, matching workflows, merge commit and execution jobs. A successful Terraform apply is shown only when its push workflow and execution step succeeded for that merge commit. Missing, skipped or unavailable evidence stays unverified. An Ansible wrapper can succeed without running an operation, so its job status alone does not verify execution. Confirmation of an existing PR is not inferred from its merge. PR links open a separate tab.

The Codex child process receives the web session's GitHub token for `gh` and Git HTTPS authentication. It uses a temporary workspace outside this repository and the host's existing Codex login. Treat the host and presenter as trusted: the skill has shell and network access, and this MVP does not enforce the preview/confirmation policy independently of the agent. Do not use a host containing cloud deployment credentials for the demo. Codex's own configuration and retention settings still apply.

The configured presenter enters AI Operations when selecting any authorized project. Dashboard and catalog routes remain available. **Catalog** combines Resources and Operations tabs; **Activity** shows requests and recorded evidence. Each web conversation stays inside its selected repository, OCI environment and configured region. Codex uses the same skill rules in the scope supplied by its user and project handoff.

Conversations and request panels stay in the authenticated server session, separated by project. Reloading the browser reopens the last chat project and restores its messages while that session remains active. Browser tab storage holds only the project and conversation identifier; transcript HTML and credentials stay out of browser storage. A server restart, logout, or 30 minutes of inactivity ends the session. **New chat** closes only the selected project conversation and clears its history and workspace; logout closes all project conversations. If a chat expires while another section is open, messages already loaded in that browser page remain visible when returning, with an expiry notice. A new chat is required before sending again. A full page reload cannot recover history from an expired server session.

The empty chat offers **Consult**, **Request change**, **Operate**, and **Investigate**. These buttons fill an editable message; **Send** submits it. **Stop**, navigation during a response, or a page reload during a response can interrupt generation. The partial transcript is preserved, and **New chat** is required before sending again. Cancellation cannot undo a GitHub write that already completed, so check for an existing PR before repeating a confirmed request. Local validation of this integration does not certify a new deployment.
