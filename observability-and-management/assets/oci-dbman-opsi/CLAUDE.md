# dbman-opsi

End-to-end OCI **Database Management** and **Operations Insights** enablement for
DBCS / Base Database, Autonomous Database, Exadata Database Service, and external
databases (via OCI Management Agents). Public-repo-ready workshop toolkit.

Runs from OCI Cloud Shell, a local workstation, or OCI Resource Manager. Every
tenant-specific value comes from variables, gitignored local config, OCI Vault, or
env vars — never hardcoded.

## Commands

| Task | Command |
|------|---------|
| Install (editable) | `pip install -e .` |
| Install dev extras | `pip install -e '.[dev]'` |
| Test (enforces ≥80% coverage) | `pytest` |
| Run CLI | `dbman-opsi` |

`pytest` config lives in `pyproject.toml` (`--cov=dbman_opsi --cov-fail-under=80`,
`pythonpath=["src"]`). No lint/format tool is configured in this repo.

## Layout

- `src/dbman_opsi/` — Python package. Logical enablement workflow:
  - `orchestrator.py` — drives the end-to-end flow
  - `discovery.py` · `preflight.py` · `prerequisites.py` · `checks.py` · `db_check.py` — is-it-installed / is-it-ready gates
  - `enablement.py` · `iam.py` · `handoff.py` — turn on DB Management / Ops Insights, IAM, registration
  - `oci_cli.py` · `terraform.py` · `tf_outputs.py` · `runner.py` — OCI CLI + Terraform execution
  - `wizard.py` · `cli.py` · `config.py` · `validation.py` · `status.py` · `doctor.py` · `reporting.py` — UX, config, status, reporting
  - `redact.py` — strips OCIDs/IPs/secrets from output
- `tests/` — pytest suite, mirrors module names
- `terraform/examples/zero-start-poc/` — provisions a DBCS in an existing VCN/subnet for testing
- `docs/workshop/` — workshop guide

## OCI tenancy rules (MANDATORY)

See `~/.claude/CLAUDE.md` for the full tenancy matrix. Short form:

- `cap` — **staging, full control**. Use for testing/experiments.
- `emdemo` — **production, read-only** outside the `LogAnalytics` compartment.
- `DEFAULT` — personal scratch tenancy.

Real tenancy names, OCIDs, namespaces, and IPs live only in
`~/.claude/private/` and the user's global `~/.claude/CLAUDE.md` — never in this repo.

## Public-repo hygiene (MANDATORY)

**This is a public repo. Never commit any real OCI identifier — not in code, docs,
config, tests, or the secret-scanner config itself.** The most common slip is
embedding real values "as examples" or as detection literals; that is itself the
exposure.

Never commit, in any tracked file (including `.gitleaks.toml`, `docs/`, tests):

- **OCIR tenancy namespaces** (e.g. the `*.ocir.io/<namespace>` segment) — use
  `${OCIR_TENANCY}` or `<OCIR_NAMESPACE>`.
- **OCIDs** (`ocid1.<type>.oc1..<body>`) — use `<…_OCID>` placeholders.
- **Tenancy names** (the real names live in `~/.claude/private/`; never inline
  them) — use `<TENANCY_NAME>` or the generic profile label (`cap`/`emdemo`/`DEFAULT`).
- **Public/private IPs of infra, API-key fingerprints, install keys, datakeys.**

`.gitleaks.toml` must detect by **context/format** (e.g. `…ocir.io/<ns>`,
`ocid1.<type>.oc1.<body>`), **never by hardcoding this tenancy's real values** —
the scanner config is the worst place to inline a secret.

**Pre-push audit (run before every push):**

```bash
# OCIDs (with a body) and OCIR namespaces in path context — detected by FORMAT,
# so this command embeds no real values. Tenancy names have no format and must be
# caught by review against the private list in ~/.claude/private/.
git grep -nE 'ocid1\.[a-z0-9]+\.oc[0-9]\.[a-z0-9._-]{15,}|[a-z0-9-]+\.ocir\.io/[a-z0-9]+' \
  -- . ':!*.md' && echo 'ABORT: real identifier in tracked files'
gitleaks detect --source . --config .gitleaks.toml --no-banner   # must be 0 over full history
```

If a real value is found in **already-pushed history**, a new "fix" commit does
NOT remove it — scrub with `git filter-repo --replace-text` and force-push (see
the global `~/.claude/CLAUDE.md` remediation protocol), and rotate anything that
was a live credential.

## Gotcha

- OCI **PDB** DB Management requires the parent **CDB** management-type set to
  `ADVANCED`. Enable CDB ADVANCED before registering a PDB.

## Troubleshooting

On error only, consult `KB.md` (this repo). Add a new KB entry after fixing any
new error.
