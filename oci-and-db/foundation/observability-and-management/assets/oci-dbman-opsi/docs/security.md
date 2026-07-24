# Security And Public Repository Guidance

This project is designed for public repository use. Keep tenant-specific data in ignored local files and use variables for every deploy-time value.

## Public-Safe Defaults

- Do not commit generated configs, generated SQL payloads, Terraform state, local logs, screenshots, or local MCP files.
- Do not commit `.env.local`. Keep local operator variables in `.env.local` from
  `.env.local.example`, set file mode to `0600`, and avoid copying real values
  into app code, generated docs, screenshots, or Terraform variable files.
- Do not commit OCIDs, public IPs, private IPs, API key fingerprints, namespaces, endpoint URLs, wallet material, or passwords.
- Use OCI Vault for database monitoring credentials.
- Use environment variables for secret input, for example `DBMAN_OPSI_DB_PASSWORD`, then run `prepare-prereqs --password-env DBMAN_OPSI_DB_PASSWORD`.
- Use placeholders in documentation and workshops, such as `<COMPARTMENT_OCID>` and `<PRIVATE_SUBNET_OCID>`.

## Screenshot Rules

Screenshots for workshops must not show tenant names, user names, tenancy OCIDs, compartment OCIDs, database OCIDs, public IP addresses, private IP addresses, or credential values. Crop or mask the browser chrome and account selector before publishing.

## Validation Before Publishing

Install the repository audit without changing `core.hooksPath`. This repository
may already use ECC-managed hooks through `core.hooksPath`; running
`git config core.hooksPath scripts` would replace that hook directory and
disable the ECC pre-push checks.

Use one of these non-conflicting approaches:

- Chain `scripts/pre-push` from the existing `pre-push` file in the current
  hooks directory reported by `git config --get core.hooksPath`.
- Register `scripts/pre-push` through the pre-commit framework.
- If the clone does not use `core.hooksPath`, symlink or copy `scripts/pre-push`
  to `.git/hooks/pre-push` locally.

The audit in `scripts/pre-push` blocks pushes when non-Markdown changes contain
format-shaped OCI resource identifiers or OCIR registry paths. It checks the
Git push range when Git supplies one and falls back to the current working tree
when run manually. If `gitleaks` is installed, the hook also runs:

```bash
gitleaks detect --source . --config .gitleaks.toml --no-banner
```

If `gitleaks` is missing, the hook prints a warning and continues so the
format-based audit still runs everywhere.

Run:

```bash
python3 -m pytest
terraform -chdir=terraform/examples/zero-start-poc fmt -check
rg -n 'ocid1\.|<personal-name>|<tenant-name>|130\.61|161\.153' README.md docs terraform src tests
```

The final `rg` command should return no public sensitive values.

Bypass the hook only for intentional, reviewed exceptions:

```bash
git push --no-verify
```

Bypassing skips both the OCI identifier audit and the optional `gitleaks` scan.
