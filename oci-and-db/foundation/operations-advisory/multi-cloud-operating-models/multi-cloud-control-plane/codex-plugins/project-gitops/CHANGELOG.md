# Changelog

## 3.2.0

- Use a stable CRQ-and-destination branch name and stop on an existing branch
  or PR instead of inventing a suffix.
- Keep previews repeatable without exposing or requiring hashes or SHAs.
- Support published OCI Compute `deploy-agent` requests as a marker-only,
  state-backed Day 2 operation.

## 3.1.0

- Align the skill with protected project workflows, including their
  `pull_request_target` trigger and post-merge `push` run.
- Cover catalog-driven OCI lifecycle requests and clears as well as
  infrastructure requests.
- Make clone, catalog-read, preview, confirmation, and PR discovery steps
  deterministic without restoring local resource validation.

## 3.0.0

- Move resource schemas and change policy to the catalog contract.
- Use one contract-driven validator entry point.
- Split operational guidance into focused references.

Plugin releases track engine and prose changes only. Contract changes ship to
the catalog `main` branch and do not require a plugin reinstall.
