# Security Guidance

The stack creates delivery capabilities with access to source repositories, OCIR, Vault, and OKE. Treat pipeline identity and repository review as production security boundaries.

## Credentials And Secrets

- Store the OCIR pull password or auth token in OCI Vault and pass only its secret OCID to `<application>-bootstrap`.
- Never commit secret material to application charts, component repositories, cluster values, or supplemental resource YAML.
- Do not use plain Kubernetes `Secret` manifests in the cluster-admin repository; use External Secrets or an equivalent external-secret reference.
- Rotate repository seeding credentials and OCIR tokens according to organizational policy.
- Review the published Terraform configuration before distribution and exclude local state, plans, credentials, logs, private ad hoc test/deployment scripts, `.git`, `.terraform`, `.agents`, and `AGENT.md`. Bundled stack templates and their intentional runtime scripts remain part of the product.

## IAM

- Prefer a dedicated dynamic group and narrowly scoped policies for OCI DevOps execution resources.
- Restrict Vault secret access to the configured Vault compartment and only the identities that run namespace initialization.
- Separate stack maintainers, application release approvers, and cluster production approvers where organizational controls require it.
- Review manually customized pipelines before expanding their IAM permissions.

## Network Access

- DevOps shell stages use OKE private endpoints and run in the selected worker subnet with the optional worker NSG.
- Keep worker-subnet egress limited to required OCI services, chart sources, and application dependencies.
- Configure pre-prod and prod subnet and NSG inputs independently, even when a temporary test setup points both environments to the same cluster.

## Supply Chain

- Pin every cluster tool repository, chart, and version in the Resource Manager tool definition; the generated `catalog/tools.yaml` must not contain floating versions.
- Keep image, chart, and values versions immutable.
- Use multi-stage Dockerfiles to keep compilers, package managers, credentials, and test tools out of runtime images.
- Replace the placeholder PR pipeline with real tests and add language-appropriate dependency and image scanning where required.
- Review the successful staging deployment before production approval.

## Kubernetes Boundaries

- Give each application and cluster tool its own namespace.
- Component ServiceAccounts reference the configured OCIR pull secret instead of modifying the namespace default ServiceAccount.
- Supplemental tool resources are restricted to the tool namespace.
- Cluster-scoped baseline changes require particular review because they can affect every namespace and may depend on CRDs installed by tool charts.
