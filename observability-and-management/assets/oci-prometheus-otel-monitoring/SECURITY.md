# Security Policy

## Reporting a vulnerability

Please report security issues **privately**. Do **not** open a public issue for a
vulnerability.

- Use GitHub's **Report a vulnerability** (Security → Advisories) on this repository, or
- email the maintainer listed in the repository profile.

Include: affected script/file, reproduction steps, and impact. You'll get an
acknowledgement and a remediation timeline.

## Never put secrets in issues, PRs, or logs

This project automates cloud infrastructure. When sharing logs or config to get
help, **redact** the following before posting:

- OCIDs (`ocid1.tenancy…`, `ocid1.compartment…`, `ocid1.instance…`, etc.)
- Public and private IP addresses
- Tenancy namespaces, APM/LA identifiers
- Management Agent install keys, datakeys, wallet passwords
- `input.rsp` contents, `*.pem`, `*.key`, GCP service-account JSON
- API key fingerprints

Replace real values with `<PLACEHOLDER>` tokens.

## What this project does and does not handle

- The scripts **do not embed** any credentials. Secrets are provided at runtime
  via `config.json`, response files, or environment variables, all of which are
  git-ignored.
- `config.json`, `downloads/`, `*.rsp`, `*.pem`, `*.key`, `.env*`,
  `discovered-targets.json`, and `gcp-*.json` are excluded by `.gitignore`.
  Verify your fork keeps them out of version control.
- The `otel-destination/` stack is a **test sink**: anonymous Grafana, no TLS.
  Override `GF_SECURITY_ADMIN_PASSWORD` and add TLS/auth before any real use; do
  not expose it publicly.

## Supported versions

This is an automation suite released as rolling `main`. Fixes land on `main`;
pin a commit/tag for reproducible deployments.
