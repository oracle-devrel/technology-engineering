# Security and GitHub controls

Project Teams propose and review changes in GitHub. A person independent of the author reviews the current request before an authorized merge. Trusted runners use their own cloud identities to plan or check the request before merge and execute it afterward. Cloud Operations controls those identities, the state and the repository settings.

## Secret delivery

The Project Team creates and rotates workload secrets in the approved Vault scope. For OCI and Azure Autonomous Database (ADB), each database has its own native OCI Vault secret. The request contains its identifier in `admin_password_secret_id`. Google Cloud ADB uses the provider-native secret reference in its catalog. Password values stay out of Git and chat. Azure and Google VM manifests contain the approved SSH public key. Private keys stay with their owner.

The shared workload Vault belongs to environment security. The version 5 handoff identifies the Vault, the project's AES-256 HSM key and its Database compartment. During onboarding, Cloud Operations supplies the key reference and configures runner read access. The key material stays in the HSM. During retirement, Cloud Operations retains the shared Vault after the project's secrets and key have been removed through the approved process.

Platform CI reads `environments/<environment>/environment_information.md` from the pull request's base commit for plan and the merged commit for apply. It checks every OCI and Azure ADB secret's compartment, Vault, key, OCI region and ACTIVE state before reading any value, initializing Terraform or accessing its backend. A missing or mismatched reference or a failed OCI query stops the run.

OCI passes the native reference to the module. Azure reads the secret's `CURRENT` version through the runner's OCI Instance Principal into private temporary variables after all metadata checks pass. The trusted handoff supplies the OCI region, independently of the Azure deployment location. The manifest uses the secret OCID directly, without a runtime token, per-secret binding or GitHub Secrets fallback. See the [configuration steps](../installation/installation-runbook.md#prepare-workload-secret-delivery).

Project Team can prepare secrets manually or, in Codex, separately confirm native Vault generation using its authorized OCI profile. The Codex skill handles secret metadata and asks for a separate confirmation before publishing a pull request. The optional UI accepts an existing identifier and uses GitHub authorization for project changes. [Codex request guide](../usage/codex-plugin.md)

## GitHub plan controls

| Private repository control | GitHub Free | GitHub Team | GitHub Enterprise Cloud |
| --- | --- | --- | --- |
| Pull request and independent review for `main` | Review is procedural for private repositories. Restrict write and admin access and record independent approval. | Configure an active ruleset requiring a pull request and at least one approval, with no direct-push bypass. | Use the same `main` ruleset. |
| Deployment environment | Follow the organization's reviewed merge process. | Environment secrets and variables are available. Required deployment reviewers are available only for public repositories. | Required deployment reviewers and prevention of self-review can be configured for a separate deployment approval. |

A `CODEOWNERS` file identifies reviewers. Enforcing their approval requires a branch protection rule or ruleset. Deployment environment approvals, where configured, apply to the workflow job and are distinct from pull request approval. Check the current plan and repository visibility before configuring these controls. [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) · [GitHub deployment environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments#required-reviewers)

The optional UI prepares the pull request and sends the user to GitHub for merge. In Codex, a user can explicitly authorize the plugin to merge one exact PR after independent review. The skill checks current-head human approval, matching validation and repository restrictions, including on GitHub Free. It uses a merge commit with an expected-head guard and rechecks the base and approval before merging. GitHub can still change base, review or check settings between those reads and the merge. See the [Codex merge steps](../usage/codex-plugin.md#merge-and-verify).

## Required controls

- Keep shared and project repositories private. Restrict Platform CI writes to Cloud Operations and review every change to its `main` branch.
- Use the reviewed orchestrator commits and GitHub Action release tags. Review upstream Action changes as part of Platform CI upgrades because major tags can move.
- Separate state by organization, project, cloud, environment and region. Keep production and non-production runners separate. Give each runner the labels and permissions for its approved work.
- A shared runner uses the same cloud identity for its approved projects. GitHub routing and secret checks protect the request path. Use separate identities and runner groups when project-level IAM isolation is required. [Runner group access](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access)
- Keep cloud credentials, raw plans and provider diagnostics private. Use the safe resource-action report or operation check as review evidence. The workflow rejects forks, unsupported paths, invalid JSON, mixed deployment scopes and unresolved placeholders.
- Verify the first intended request before its deployment. [First-project check](verify-secret-isolation.md)
