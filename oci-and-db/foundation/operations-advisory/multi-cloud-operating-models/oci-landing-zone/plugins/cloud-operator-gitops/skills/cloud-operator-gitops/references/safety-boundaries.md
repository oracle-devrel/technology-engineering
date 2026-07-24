# Safety boundaries

- Treat `deployment-contract.json` as immutable policy.
- Accept only one `<allowed-environment>-<dns-name>` OP04 target.
- Derive foundation values only from the protected environment blueprint.
- Permit only the canonical additive OP04 files in the landing-zone repository.
- Preserve the OE `v3.1.0` single project-compartment hierarchy; never add the
  retired OE `v2.x` application/database/infrastructure children.
- Never accept secrets, raw state, or prompt-provided cloud identifiers.
- Create a project repository only when the validated handoff target is absent,
  using the exact contract-pinned template and private visibility. For an
  existing shared non-production repository, verify its identity and protected
  contract before adding another environment handoff.
- In a newly created project repository, the first handoff branch may change
  only `control-plane.json`, `.github/CODEOWNERS.template`,
  `.github/CODEOWNERS`, and the validated
  `environments/<environment>/environment_information.md`. Derive the exact
  target, security profile, and owners from `deployment-contract.json`; never
  accept them from a prompt. Require the rendered CODEOWNERS identities to
  exist and have repository write access before the branch is pushed.
- In an already initialized project repository, write only the validated
  `environments/<environment>/environment_information.md` path on a new
  branch.
  Write `environments/<environment>/exacs-databases.json` only when the Cloud
  Operator has an explicit request and verified regular-ExaCS resource facts;
  it is platform-owned and must never be populated with secrets. Never change
  workflows, contracts, manifests, secrets, teams, or permissions.
- Never merge, approve, control workflows, call cloud APIs, or run Terraform.
- Keep inventory read-only and limited to declared foundation state.
- Never generate helper scripts or executable files. Use only packaged scripts. Keep temporary
  data inside one fresh system temporary directory, clean it before returning, and leave no local
  files after read-only work.
- Treat valid empty manifests and empty resource collections as zero declarations, not incomplete
  inventory. Never infer live running or stopped state from Git declarations.
- After a known human merge, monitor the exact workflow until terminal by default. Never use a
  non-terminal state as the final answer unless the user requested a one-time snapshot.
