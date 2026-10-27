# Safety And Troubleshooting

## Before Mutation

- Confirm region, project, pipeline, cluster, namespace, application, component,
  tool, commit, image tag, and chart version.
- Read pipeline parameters and stage logs before retrying.
- Inspect current Git, OCIR, Helm, and Kubernetes state without revealing
  secret values.
- Obtain explicit authorization immediately before production approval,
  release, decommissioning, destructive cleanup, or infrastructure mutation.

## Diagnose In Order

1. Resource Manager job and Terraform check failures.
2. Repository seed state, branch protection, trigger filters, and source commit.
3. Build-stage logs and exported variables.
4. OCIR image or chart existence and immutable digest.
5. Deployment-stage parameters, artifacts, environment, subnet, and NSG.
6. Helm release history and status.
7. Kubernetes workloads, events, services, service accounts, and image-pull
   errors.

Keep cross-variable constraints in Resource Manager root checks when modifying
the stack; older Terraform runtimes reject cross-variable references in
variable validation blocks. OCI deployment command images support only their
documented Helm command surface, so inspect the actual stage error before adding
optional flags.

## Recovery

- Retry only after identifying whether the failed step is idempotent.
- Roll back a component with its Helm release history and the previously used
  immutable image and retained values.
- Revert repository configuration through Git for cluster-admin changes.
- Do not edit generated resources directly as a substitute for fixing the
  owning repository or pipeline.
- Report deployment, image promotion, Git tagging, and informational-stage
  outcomes separately.
