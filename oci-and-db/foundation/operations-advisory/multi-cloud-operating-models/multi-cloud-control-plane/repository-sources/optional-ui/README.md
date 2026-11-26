# AI Operations UI

Use the optional UI to prepare MCCP requests through catalog forms. The optional AI Operations chat lets a demo presenter consult declared resources, prepare supported requests and investigate workflows. Both routes use the [MCCP request process](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/usage/request-lifecycle.md).

## Installation

**Before you start**, have the accepted project repositories, the installed catalog and an approved UI runtime location. The UI reads the configured organization's `gitops-templates` repository on `main`.

1. Create and install a dedicated GitHub App. Enable user-to-server authorization and register the exact callback URL. Give the App access only to the catalog and the project repositories it serves.
2. Configure the repository permissions below and the local `.env`. Use `GITHUB_ORG` for the installed organization and a strong session secret. Keep the configuration and all credentials out of Git.
3. Start the UI from its runtime directory and sign in. Check that the user sees only their authorized projects and can open a catalog form.

| GitHub App permission | Level | Purpose |
| --- | --- | --- |
| Actions and Checks | Read | Show validation and execution evidence |
| Contents, Issues and Pull requests | Read and write | Prepare issues, branches, commits and pull requests |
| Metadata | Read | Identify accessible repositories |

Use the signed-in user's GitHub authorization for project writes. The App uses user authorization with the permissions above. An optional server token can read the catalog. The runtime needs no GitHub App private key, installation-token flow or write access to Actions, Checks, Administration or Workflows.

```bash
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with the approved settings, then start the UI.

```bash
.venv/bin/python -m app.main
```

The application reads its host and port from `.env`. The local example uses `http://localhost:8011/callback`. Use TLS for a shared installation, register its exact external `https://<host>/callback` URL and preserve the original host and protocol at the proxy. Set `APP_URL` to the browser origin, including protocol and any port.

## Catalog boundary

Forms expose approved placeholders and fixed catalog profiles. An OCI network security group request can create a group or add approved TCP rules to an existing group. The form uses integer port ranges and rejects duplicate rule keys. For Azure Autonomous Database, the public mTLS options allow connections from any IP with wallet and database authentication. [Reference capabilities](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/support.md)

## Security boundary

GitHub handles independent review and merge. Trusted runners hold cloud deployment permissions and execute approved changes. The UI operates with GitHub authorization. See the [component security policy](SECURITY.md) and [MCCP security controls](https://github.com/oracle-devrel/technology-engineering/blob/main/oci-and-db/foundation/operations-advisory/multi-cloud-operating-models/multi-cloud-control-plane/docs/reference/security.md).

## Workload secret references

Use an existing OCI Vault secret OCID in `admin_password_secret_id` for each OCI or Azure Autonomous Database. The form and chat use a separate reference per database. OCI uses the deployment region. For Azure, the trusted handoff supplies the OCI region used for validation and lookup. Project Team owns secret preparation and rotation, and Cloud Operations prepares runner access.

The form checks the merged ADB manifest before publication. The chat panel checks the selected proposal for native references, including missing, legacy or reused references. For Azure and Google VMs, provide the approved SSH public key. Keep passwords and private keys in their approved stores.

## Local chat demo

The chat is disabled by default. It runs the `project-gitops` skill through a local Codex app-server process for one configured presenter. Catalog forms remain available. The demo uses an experimental Codex tool interface and depends on the skill for semantic previews and explicit confirmation. It is a single-presenter MVP.

| Setting | What to use |
| --- | --- |
| Host tools | Git, authenticated Codex CLI and GitHub CLI. The integration was checked locally with Codex CLI 0.165.0. |
| Enablement | `CHAT_ENABLED=true` and `CHAT_DEMO_LOGIN=<presenter-github-login>` |
| Organization | `GITHUB_ORG=multicloud-control-plane` for the bundled demo skill |
| Skill | For a standalone UI installation, make the approved Project GitOps skill available on the UI host and set `CHAT_SKILL_PATH` to its `SKILL.md` file. The source checkout resolves the repository copy automatically. |
| Optional settings | `CHAT_DEMO_PROJECT` for a project shortcut and `CHAT_MODEL` for model selection |

Use a trusted host and presenter. The Codex process uses the host's Codex login, a temporary workspace and the signed-in user's GitHub token for Git and `gh`. The skill has shell and network access on the host. Keep cloud credentials off the demo host. Codex configuration and retention still apply.

1. Start the UI with `.venv/bin/python -m app.main` and sign in as the configured presenter. Select a project you can write to and open **AI Operations**.
2. Use an OCI or Azure scope shown in the chat header. Non-production uses `dev` and production uses `prod`. OCI reads `DEFAULT_REGION`. Azure reads `DEFAULT_CLOUD_REGIONS` and `CLOUD_REGION_OPTIONS`. After changing regions, restart the app and start a new chat.
3. Ask for an inventory or an approved change. For a change, supply the CRQ and missing inputs. Review the full proposal in chat and send `confirm` as the entire message to publish.
4. Open the PR in GitHub for independent review and merge. **Refresh status** reads the matching GitHub evidence. Use the GitHub workflow as the source for execution, particularly when the panel reports an unverified result.

The request panel shows the scope, CRQ, proposed manifest and relevant catalog settings or operation targets. Use the full preview in chat for confirmation. The app preserves in-session conversations separately per project. **New chat** resets the selected conversation. Logout, server restart or 30 minutes of inactivity ends the session. Polling status does not extend that time. If a response is interrupted, check GitHub for an existing PR before repeating a confirmed request, then select **New chat** to continue.
