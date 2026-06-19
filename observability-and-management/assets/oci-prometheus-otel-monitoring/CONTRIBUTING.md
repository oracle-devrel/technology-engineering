# Contributing

Thanks for your interest in improving this project. It's a cross-platform
automation suite (PowerShell + Bash + a Docker OTEL sink), so contributions are
mostly scripts, docs, and config.

## Ground rules

1. **No secrets, ever.** Don't commit OCIDs, IPs, tenancy namespaces, install
   keys, wallet passwords, `*.rsp`, `*.pem`, `*.key`, or `gcp-*.json`. See
   [SECURITY.md](SECURITY.md). Use `<PLACEHOLDER>` tokens in examples.
2. **Keep it idempotent and fail-fast.** Installers may run unattended (cloud-init)
   and re-run on the same host. Check exit codes; don't leave half-built state.
3. **Document new errors in the KB.** If you fix a bug, add an entry to
   [`docs/KNOWLEDGE_BASE.md`](docs/KNOWLEDGE_BASE.md) (Symptom → Root cause →
   Resolution → File).

## Local checks (run before opening a PR)

```bash
# Bash: lint every script
shellcheck *.sh otel-destination/*.sh

# PowerShell: parse + analyze
pwsh -NoProfile -Command "Invoke-ScriptAnalyzer -Path ./Install-OCI-Prometheus.ps1 -Severity Warning,Error"

# Docker compose: validate the test sink
docker compose -f otel-destination/docker-compose.yml config >/dev/null
```

CI runs these on every PR (see `.github/workflows/lint.yml`).

## Commit messages

Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`, `ci:`,
`test:`, `perf:`. One logical change per commit.

## Pull requests

- Describe the change and how you tested it (which OS, which OCI region/profile —
  redacted).
- For behavior changes to the installers, note backward compatibility with
  Windows PowerShell 5.1 and older Windows targets.
- Link any KB entry you added.

## Scope

In scope: exporters install/config, the Prometheus proxy, OCI Management Agent
integration, the OTEL export path, OCI instance discovery, the test sink, docs.

Out of scope: vendoring large binaries (beyond the bundled `nssm.exe`), and
anything that hardcodes environment-specific values.
