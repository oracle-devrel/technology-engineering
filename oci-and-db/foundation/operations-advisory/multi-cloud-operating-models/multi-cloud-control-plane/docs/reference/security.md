# Security and GitHub controls

Project Teams submit reviewed Git changes, manage the values and rotation of their workload secrets, and do not receive deployment credentials. Cloud Operations manages repository controls, the secret-delivery boundary, state, and runner identities. Before merge, trusted runners read cloud resources, state and required secrets for plan or check. Workload apply and lifecycle execution require independent human review and a human-authorized merge. In Codex only, Project Team can explicitly instruct the skill to merge one exact PR after its decision summary; the skill verifies current-head independent approval, matching validation and repository restrictions before executing that merge. The optional UI cannot merge.

## Secret delivery

Workload secrets stay in the approved Vault scope for the project and environment. The Project Team owns their preparation and rotation. In Codex, its skill can create a dedicated ADB secret after a separate semantic preview and confirmation, using the team's authorized OCI profile and native Vault generation. It handles metadata only, then requests a separate confirmation for GitHub publication. The optional UI cannot use host credentials or create secrets. Cloud Operations prepares foundation access and the runner's read access. Git, chat and the handoff contain references, not passwords.

OCI ADB uses one native Vault secret OCID per database through `admin_password_secret_id`. Google Cloud ADB uses its provider-native secret reference. Azure ADB also accepts `admin_password_secret_id`. The runner validates all ADB secret metadata against the trusted handoff, uses its OCI region and then reads `CURRENT` through Instance Principal under its existing OCI IAM permissions. There is no per-project scope file or per-secret Azure ADB binding. Azure and Google VM manifests contain approved SSH public keys directly. All catalog placeholders must be rendered before publication; runtime tokens are unsupported. There is no GitHub Secrets fallback. The [installation runbook](../installation/installation-runbook.md#prepare-workload-secret-delivery) shows the configuration.

The workflows reject forks, unsupported file changes, invalid JSON, mixed deployment scopes and unresolved placeholders. A shared dev runner has one shared identity: these checks select the approved request, but do not create a separate IAM boundary for every project. Choose separate runner identities when the customer needs stronger separation.

## GitHub plan controls

GitHub Free private repositories do not provide enforceable [private branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches) or deployment-environment approval. CODEOWNERS cannot enforce review without branch protection. On this profile, approval is procedural: restrict direct pushes and administrators, record independent review, verify the current plan or check, and then merge. Do not describe this as GitHub-enforced approval.

The explicit Codex merge path checks for an effective GitHub approval from a human other than the PR author on the current head, with no outstanding changes request, even when branch protection does not enforce review. It uses a merge commit with an expected-head guard and repeats base, checks and review reads before mutation. These reads do not atomically lock the base or review/check settings; the skill does not claim stronger isolation than GitHub provides. It does not use administrative bypass, auto-merge, merge queues or automatic branch deletion. Missing evidence, restricted metadata or unsupported merge settings block the action.

GitHub Team and GitHub Enterprise Cloud add controls for private repositories that Cloud Operations should configure during installation. Use an active `main` ruleset that requires a pull request and at least one approving review, with no direct-push bypass. The installation runbook includes the plan-specific configuration and verification. These controls strengthen the same governed request path; they do not change the project workflow.

## Required controls

- Keep shared and project repositories private.
- Restrict Platform CI writes to Cloud Operations and review every change to its `main` branch.
- Use the reviewed orchestrator commits from the installation runbook and reviewed GitHub Action release tags.
- Isolate state by organization, project, cloud, environment, and region.
- Give each runner only the cloud permissions and labels required for its scope.
- Keep non-production and production on separate runners.
- Project Teams create and rotate workload-secret values only in their approved Vault scope.
- Keep Azure `ARM_*` values and Google credentials on the trusted runner, outside project manifests.
- Keep passwords in Vault. Publish safe resource-action reports and fixed diagnostic categories; raw plans and provider messages can contain secret material.
- Complete the [first-project check](verify-secret-isolation.md) before the first workload deployment.

## Additional GitHub plan capabilities

GitHub Team and GitHub Enterprise Cloud can protect private `main` branches and use environment secrets or variables. They do not provide required deployment reviewers for private repositories.

GitHub Enterprise Cloud can additionally use required deployment reviewers, prevent self-review, and keep environment secrets behind an approval gate in private repositories. It can support paired GitHub Environments such as `dev` and `dev-apply` when that approach is selected for the customer.

Availability depends on the GitHub plan and repository visibility. Verify the current GitHub documentation for [protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments), and [runner groups](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access) before configuring customer controls.

Official GitHub Actions referenced by major tag can receive breaking changes. Cloud Operations reviews those release changes during Platform CI upgrades. The workflows retain their reviewed major tags unless an upgrade requires a separately reviewed change.

The shared workload Vault belongs to environment security. Each project owns its AES-256 HSM key and secrets in Database; the key OCID is a reference and key material remains in HSM. Project Team prepares each database's independent secret through confirmed Codex preparation or its approved manual process, using the handoff references. Manifests keep the same `admin_password_secret_id` field. Secret preparation does not authorize ADB deployment, changes to the shared Vault or project key, or automatic secret removal if the request is abandoned.

Platform CI checks all ADB secret metadata before reading any value, initializing Terraform or accessing its backend. The authorization handoff is `environments/<environment>/environment_information.md` from the immutable PR base for plan and merged commit for apply. The request branch cannot replace that authorization. Compartment, Vault, key, OCI region and ACTIVE state must all match; query failures stop the run. OCI retains the native secret OCID; Azure resolves `CURRENT` into private temporary variables only after all references pass. Azure location does not select the OCI Vault region. There are no additional project scope files or bindings.

These checks protect the governed workflow. They do not create IAM isolation between executions using the shared runner identity. Keep secret values, raw Terraform diagnostics and private temporary variables out of Git and PR comments. CloudOps retains the Vault during project retirement and manually completes project-secret and key removal first.
