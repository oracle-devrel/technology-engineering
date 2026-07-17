# Multi-Cloud Control Plane UI

This optional web interface helps Project Teams prepare governed infrastructure
requests in repositories that have already completed project handoff. It reads
the approved catalog, presents a form, and opens a GitHub issue, branch, commit,
and pull request.

The UI does not create project repositories, run OP04, call cloud APIs, merge
pull requests, or replace the normal GitHub pull-request path.

## Before deployment

You need:

- Python 3.11 or later.
- A GitHub OAuth App for the URL where users will open the UI.
- Access to the private `gitops-templates` repository.
- Handed-off project repositories whose names match `PROJECT_REPO_PREFIX`.
- TLS, secret storage, logging, and monitoring appropriate for your
  organization.

The OAuth callback must be `<APP_URL>/callback`. Give the OAuth App only the
repository access needed by its users.

## Configure and run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Set at least:

| Variable | Purpose |
|---|---|
| `GITHUB_ORG` | Organization containing the shared and project repositories |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App secret |
| `SESSION_SECRET` | Strong random session-signing secret |
| `APP_URL` | Public HTTPS origin used by the OAuth callback |
| `PROJECT_REPO_PREFIX` | Prefix used to discover handed-off project repositories |

`GITHUB_TOKEN` is optional and may support catalog reads. It must never bypass
the signed-in user's project permissions. Keep OAuth secrets, tokens, and the
session secret outside Git.

Use the [smoke test](docs/howto/smoke-test.md) for pre-production validation.

## What users can do

- View accessible project repositories, inventory, pull requests, and workflow
  results.
- Prepare supported Day 1 requests from the resource catalog.
- Prepare supported OCI Day 2 requests from the operations catalog.
- Review the generated manifest and open a pull request.

The UI refuses writes when it cannot validate repository state, paths, existing
JSON, the target project, or the user's write permission. It writes only to
handed-off project repositories and never to shared, template, or foundation
repositories.

## Production checks

- Use HTTPS and a production `SESSION_SECRET`.
- Restrict OAuth and optional token permissions to the required repositories.
- Protect project branches and require the same independent plan/check approval
  used by the no-UI flow.
- Confirm cache, session, error logging, backup, and incident procedures.
- Run the smoke test in non-production before enabling users.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
