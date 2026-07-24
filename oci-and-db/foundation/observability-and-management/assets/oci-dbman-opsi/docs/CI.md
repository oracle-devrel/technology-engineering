# Continuous Integration

This document describes the three CI jobs that run on every push and pull request,
how to reproduce each check locally, and how to interpret and triage findings.

## Jobs

### 1. `test` — Pytest + coverage gate

Runs on a matrix of **Python 3.11, 3.12, and 3.13**.

Steps:
1. Install the package in editable mode with dev extras (`pip install -e '.[dev]'`).
2. Run `pytest` — the 80 % coverage gate is enforced by `pyproject.toml`
   (`--cov-fail-under=80`).  A coverage drop below 80 % fails the job.

The matrix uses `fail-fast: false` so all three Python versions are always tested
even when one leg fails.

**Run locally:**
```bash
pip install -e '.[dev]'
pytest                          # with coverage report
pytest --no-cov                 # skip coverage (faster feedback loop)
pytest -m eval --no-cov         # run only the eval marker suite
```

---

### 2. `security` — Bandit static analysis

Runs `bandit -r src/ -ll --skip B608` against the entire `src/` tree.

| Flag | Meaning |
|------|---------|
| `-ll` | Report **Medium severity or higher** only (Low issues omitted). |
| `--skip B608` | One rule ID suppressed project-wide as structurally inapplicable (see below). |

#### Suppression policy — rationale

| Rule | Handling | Location | Why |
|------|----------|----------|-----|
| **B608** `hardcoded_sql_expressions` (Medium/Low) | **Skipped project-wide** (`--skip B608`) | `db_scripts.py:25,45,84,185,231` | All five hits are Oracle SQL\*Plus script generators — multi-line f-strings that produce `.sql` files for a human DBA to run in `sqlplus`.  These are **not** Python DB-API calls; the interpolated values are DDL identifiers (usernames, container names) that cannot be bind-parameterised.  Oracle-side injection is guarded by `dbms_assert.simple_sql_name()`.  B608 is structurally inapplicable to a SQL-emitting tool, so a blanket skip is correct. |
| **B108** `hardcoded_tmp_directory` (Medium/Medium) | **Active**; one site `# nosec`'d inline | `bastion_exec.py` `remote_dir="/tmp"` | The string `"/tmp"` is the default of the `remote_dir` constructor parameter of `BastionSqlRunner` — a **remote** SSH target directory, not a local Python `tempfile` creation (CWE-377 does not apply).  The rule stays enabled so a real insecure local-tempfile use elsewhere still fails CI; only this one line carries `# nosec B108` with a justification. |

To close B608 inline later (and drop the `--skip`): add `# nosec B608` at the end of each SQL-template assignment statement in `db_scripts.py`, then remove `--skip B608` from `.github/workflows/ci.yml`.

**Run locally:**
```bash
pip install bandit
bandit -r src/ -ll --skip B608   # mirrors CI exactly
bandit -r src/ -ll               # see all findings including the skipped B608
bandit -r src/ -lll              # high-severity only (strict mode)
```

---

### 3. `secret-scan` — Gitleaks

Runs `gitleaks/gitleaks-action@v2` with a custom `.gitleaks.toml` config.

**Why gitleaks and not a grep gate?**  Gitleaks understands git history — it
can detect secrets that were introduced in an older commit even if they were
later "deleted".  The official GitHub Action also produces SARIF output, which
GitHub Security integrates into the repository's Code Scanning dashboard.  A
bare `grep` gate on the working tree would miss committed-then-removed secrets.

#### Custom OCI rules in `.gitleaks.toml`

The config extends the default gitleaks ruleset and adds:

| Rule ID | Detects |
|---------|---------|
| `oci-ocid` | Any `ocid1.<resource-type>.oc1.*` identifier — covers all resource types tracked in `redact.py` |
| `oci-isk-key` | `isk_<40 hex chars>` — OCI internal service keys |
| `oci-api-fingerprint` | 16 colon-delimited hex pairs — OCI API key fingerprint format |
| `oci-registry-namespace` | Tenancy namespace in OCIR path context (`…ocir.io/<namespace>`) — detected by format, not by hardcoding real values |
| `oci-public-ip` | Public-IP blocks from the tenancy matrix (`130.61.*`, `161.153.*`, etc.) |

The default ruleset detects generic secrets (AWS keys, GCP tokens, GitHub PATs,
PEM private keys, high-entropy strings, etc.) that are equally relevant here.

**Run locally:**
```bash
# Install gitleaks (macOS)
brew install gitleaks

# Detect — scans working tree against the last commit
gitleaks detect --config .gitleaks.toml --verbose

# Detect across full git history (mirrors CI fetch-depth: 0)
gitleaks detect --config .gitleaks.toml --verbose --log-opts="--all"

# Protect — scan staged changes before a commit
gitleaks protect --config .gitleaks.toml --staged --verbose
```

#### Triaging a gitleaks finding

When gitleaks flags a hit, the output includes the rule ID, file, line, and the
matched value.  Follow this decision tree:

```
Is the matched value a real secret or OCID?
  YES → See "Real leak" below.
  NO  → Is it a <PLACEHOLDER> token, ${ENV_VAR}, or example value?
          YES → It should already be allowed.  If not, update .gitleaks.toml.
          NO  → Is it in docs/ or tests/ as a synthetic fixture?
                  YES → Add the file path to the appropriate [rules.allowlist] paths.
                  NO  → Treat as a real leak and follow the procedure below.
```

**Real leak — response procedure:**

1. **Stop.** Do not push a "fix" commit — the secret remains in git history.
2. Identify the commit SHA that introduced it (`git log -S '<matched-value>'`).
3. Rotate the secret immediately (regenerate the OCI API key, auth token, etc.).
4. Rewrite history with `git filter-repo --replace-text <redactions-file>` to
   purge all occurrences from every branch and tag.
5. Force-push the rewritten history and notify collaborators.
6. See `docs/security.md` for the full incident playbook.

**Placeholder / false-positive — updating the allowlist:**

If a legitimate placeholder or test fixture is flagged:

1. Open `.gitleaks.toml`.
2. Add the file path to the relevant `[rules.allowlist].paths` list
   (preferred — narrowest scope) or to the global `[allowlist].paths`.
3. Re-run `gitleaks detect --config .gitleaks.toml --verbose` to confirm the
   finding is suppressed.
4. Commit `.gitleaks.toml` with a note explaining why the allowlist was extended.

**Do not** add broad `regexes` to the global allowlist unless the pattern is
genuinely impossible to mistake for a real secret.

---

## Quick-reference — run all CI checks locally

```bash
# 1. Tests + coverage
pip install -e '.[dev]'
pytest

# 2. Security scan
pip install bandit
bandit -r src/ -ll --skip B608

# 3. Secret scan
brew install gitleaks          # or: https://github.com/gitleaks/gitleaks/releases
gitleaks detect --config .gitleaks.toml --verbose
```
