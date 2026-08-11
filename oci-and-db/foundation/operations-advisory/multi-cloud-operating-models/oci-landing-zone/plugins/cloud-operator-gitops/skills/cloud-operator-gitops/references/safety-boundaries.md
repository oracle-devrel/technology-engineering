# Safety boundaries

- Treat `cloud-operator-installation.json` as immutable installation configuration.
- Accept only schema 3 with one exact customer-owned foundation repository on
  `main` and two explicit customer-owned template repository/revision pairs.
  Never infer either repository from a prompt,
  redirect, SHA search, or historical artifact.
- Require blueprint and handoff source provenance to name that configured
  repository. After any foundation identity change, require a fresh OP02 promotion.
- Accept only one `<allowed-environment>-<dns-name>` OP04 target. The DNS name
  must omit the derived repository prefix: reject `nonprod-` for dev/test/UAT
  and `prod-` for prod.
- Keep this enforcement layer small. Put communication, confirmation, and
  operator choices in the skill; add executable validation only to protect an
  identity, artifact, provenance, path, or pending write.
- Require a user-provided CRQ matching `CRQ[0-9]{1,20}` before any mutable
  onboarding, handoff-publication, repository-creation, or retirement flow.
  A CRQ is not required for inventory, status, validation, or monitoring, and
  it never replaces explicit confirmation.
- Derive foundation values only from the protected environment blueprint.
- Permit only the canonical additive OP04 files in the landing-zone repository.
- Require the official OCI TBAC hierarchy: one project root with Application,
  Database, and Infrastructure child compartments. Any other hierarchy is unsupported.
- Never accept secrets, raw state, or prompt-provided cloud identifiers.
- On GitHub Free private repositories, never claim that an organization secret
  or variable is available to a project repository. Require a manual
  repository secret bundle only for a workload manifest with a matching
  environment-qualified placeholder. Configure organization-scoped private
  `platform-ci` Actions access once on Platform CI; new organization
  repositories inherit it automatically. Use the Platform CI `main` composite
  action and reject a deploy key or personal access token. Workload secret bundles
  remain repository-and-environment scoped on every GitHub plan.
- Create a project repository only when the validated handoff target is absent,
  by pushing the exact contract-selected template commit to a private target and
  proving its commit and tree equality before the handoff branch. For an
  existing shared non-production repository, verify its identity and protected
  default-branch workflow before adding another environment handoff.
- In a newly created project repository, the first handoff branch may change
  only `.github/CODEOWNERS.template`, `.github/CODEOWNERS`, and the validated
  `environments/<environment>/environment_information.md`. Derive the exact
  target, fixed security profile, and owners from
  `cloud-operator-installation.json` and the
  protected template; never accept them from a prompt. Require the rendered
  CODEOWNERS identities to exist and have repository write access before the
  branch is pushed.
- In an already initialized project repository, write only the validated
  `environments/<environment>/environment_information.md` path on a new
  branch. Never change workflows, contracts, manifests, secrets, teams, or
  permissions.
- Never merge, approve, control workflows, call cloud APIs, or run Terraform.
- For retirement, require the packaged validator to prove the exact deletion of one project's
  IAM declaration. Preserve Terraform state and the project repository automatically.
- Keep inventory read-only and limited to declared foundation state.
- Never generate helper scripts or executable files. Use only packaged scripts. Keep temporary
  data inside one fresh system temporary directory, clean it before returning, and leave no local
  files after read-only work.
- Treat valid empty manifests and empty resource collections as zero declarations, not incomplete
  inventory. Never infer live running or stopped state from Git declarations.
- After a known human merge, monitor the exact workflow until terminal by default. Never use a
  non-terminal state as the final answer unless the user requested a one-time snapshot.
