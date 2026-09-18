# Upgrading To 1.1.1

This patch carries the applicable bootstrap fixes from OKE GitOps into OKE
DevOps Starter. It does not change application delivery ownership.

## IAM Placement

When creating IAM, select **IAM Policy Compartment** as a common ancestor of
the DevOps project, OKE, and network compartments. The default is the tenancy
root. Policies still grant access only to the selected resource compartments;
this is not tenancy-wide authorization. The applying identity must be allowed
to manage policies at the selected location.

Review the plan before applying: an existing DevOps policy changes attachment
location. Vault access remains a separate policy in the secret compartment.
When IAM creation is disabled, continue managing these policies externally.

## Project Location

Application delivery and cluster administration use Shell stages backed by
Container Instances. Both new and reused DevOps projects must be in a child
compartment for those modes. Pure build-only mode without cluster administration
does not require this restriction.

## Explicit Helm Reruns

New application baseline and component dev/release pipelines default
`ENFORCE_HELM_DEPLOYMENT` to `true`. This OCI-reserved uppercase name is
intentional. Explicit runs execute Helm even if artifacts and parameters are
unchanged; no continuous reconciliation is introduced.

Existing pipeline customizations remain protected by `ignore_changes = all`.
For existing pipelines, manually add this parameter with default `true`, or
pass it on a deployment run. No repository reseeding or pipeline replacement
is needed. Operations pipelines already invoke Helm directly and are unchanged.

See [Oracle's Helm deployment documentation](https://docs.oracle.com/en-us/iaas/Content/devops/using/deploy-helmchart.htm).
