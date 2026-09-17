# Stack scope and bootstrap

Flux Operator is a normal platform application:
`platform/applications/kustomization.yml` includes `flux-operator` in both
scopes. Only Kustomization/platform is declared in gitops/fluxcd/platform.yml.
The pipeline installs the operator before handoff, so its CRDs already exist.
Do not recreate a separate Kustomization/flux-operator. For older repositories,
use the staged handoff in docs/operations.md: disable old pruning and set
deletionPolicy to Orphan, reconcile it, adopt its exact objects under platform,
verify readiness and inventory, then remove the old Kustomization. Bootstrap
pruning may be disabled, so explicit deletion of the orphaning old object may
be needed with user authorization.

- `cluster_admin` creates cluster-config and gitops-pipelines, plus optional
  fleet-config. It does not create apps-config or its source. The full
  `applications_and_cluster` scope adds the developer catalog and placements.
  Switching to cluster_admin can destroy the Terraform-managed apps-config
  repository; inspect the plan. Existing customer Git is not rewritten by an
  ordinary Resource Manager apply.
- New and reused DevOps projects must be in a child compartment. The Shell
  runner uses that compartment and reaches the private OKE endpoint through
  the configured subnet and optional NSG.
- `iam_policy_compartment_id` is the policy attachment location, defaulting to
  the tenancy root. An alternative must contain all referenced DevOps, OKE,
  and network compartments in its subtree. Statements remain scoped to those
  compartments. OCI-added dynamic-group schema extensions are ignored;
  matching rules remain managed.
- Create two credential Secrets in the DevOps project compartment. The Git
  JSON is `{"username":"example-tenancy/Default/git-reader","password":"REPLACE_WITH_GIT_AUTH_TOKEN"}`.
  The OCIR JSON is `{"username":"example-namespace/Default/ocir-reader","password":"REPLACE_WITH_OCIR_AUTH_TOKEN"}`.
  Replace every example value. OCIR uses the Object Storage namespace; Git
  uses the tenancy name. Use separate read-only identities and auth tokens.
  In the Console, enter plaintext JSON, not manually base64-encoded content.
- Supply only Secret OCIDs through `git_read_credentials_secret_ocid` and
  `registry_pull_secret_ocid`. The shared-token fallback has been removed.
  Resource Manager's `auth_token` still seeds Git and is not a runtime credential.
- `bootstrap-gitops-agent` mirrors and installs; it passes the OCI-defined
  `ENFORCE_HELM_DEPLOYMENT=true` to the installer. Do not add a nonce Helm
  override. `mirror-gitops-agent` takes chart_version and never installs.
- Parameter descriptions must avoid angle-bracket placeholders: OCI rejects
  them as HTML. Use concrete example JSON with clearly replaceable values.
- Bootstrap installs the controller, then an administrator applies the
  generated bootstrap root once. Routine changes subsequently go through Git.

See the repository's `docs/iam.md` and `docs/runtime-secrets.md` for the full
credential workflow. Never print token values while validating it.
