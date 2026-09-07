# Invariants And OCI Constraints

## Developer Delivery

- Application and component names are configurable; components are globally unique.
- Image paths use `<project>/<application>/<component>`.
- Umbrella charts use `<project>/charts/<application>` and component charts add `/<component>`.
- Main builds produce only a 7-character Git SHA image tag and deploy development.
- Pull-request build specs are component-owned placeholders intended for language-specific tests.
- Application baselines and component charts have independent package and deployment lifecycles.
- Release builds promote an explicit semantic release-candidate tag without rebuilding the image.
- Production follows staging and approval, retags the RC image to the final version, deploys it, records status, and tags the released commit.
- Values artifacts are application/environment or cluster specific; image coordinates are pipeline parameters where required.

## Cluster Administration

- The feature is absent unless `enable_cluster_admin` is true.
- Public HTTP(S) and OCI Helm chart sources are supported and mirrored to the project chart prefix.
- Tool configuration forms a DAG through `depends_on`; orchestration, not arbitrary Terraform predecessor edges, enforces topological waves.
- Independent tools run in parallel. Tool Helm deployments happen before the final cluster-wide baseline because baseline objects may use tool-provided CRDs.
- Pre-prod begins without approval. Production requires approval before mutation.
- Values artifact versions equal the full configuration commit SHA.
- Supplemental namespaced resources may target only the configured tool namespace.
- Removing Git files does not prune live objects. Explicit decommission pipelines uninstall tools.

## OCI DevOps Constraints

- Deployment pipeline parameters may omit defaults. Build pipeline parameters cannot use empty defaults reliably, so derive build context from sources, stage metadata, and limited OCI lookups.
- Step-level environment assignments do not persist unless exported through the build specification contract; top-level build-spec environment values are available to all steps.
- OCI Helm `set_values` become chart values. Do not treat undocumented values such as `DRY_RUN=true` as stage control unless verified against the live service.
- Shell runners use OKE private endpoints and must use the target cluster worker subnet plus optional NSG.
- The OCI provider may reject empty strings on update even where the UI displays a blank default. Prefer omitted/null defaults when supported.
- Use `--stage-id` with `oci devops deploy-stage get`.
- Avoid changing predecessor graphs and resource keys in one apply when OCI resources still reference old stages. Use a staged migration when necessary.

## Security And Distribution

- Vault secret OCIDs are inputs, never embedded defaults for credentials.
- Secret values never enter Git, Terraform outputs, generated values, command specifications, or logs.
- Package only product Terraform, intentional templates/scripts, starter repository content, tests, and customer documentation.
- Exclude `.agents`, `AGENT.md`, `.git`, `.terraform`, state, tfvars, logs, credentials, local plans, generated archives, and private ad hoc deployment scripts.
- Inspect `docs/security.md` when changing IAM, Vault, networking, repository authentication, image/chart sources, or Kubernetes privileges.
