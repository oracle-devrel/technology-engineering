# OCI IAM policy reference

This page is the stack-author reference for DevOps resource-principal and
runtime-reader policies. Cluster administrators should follow the navigable
bootstrap guide generated into `cluster-config`:

- [Argo CD IAM guide](repos/argocd/cluster-config/docs/iam.md)
- [Flux CD IAM guide](repos/fluxcd/cluster-config/docs/iam.md)

## Execution principals

With `create_iam = true`, the stack creates three identity-domain dynamic groups.
The existing `devops_dynamic_group_name` group is retained in Terraform state but
its membership is narrowed to the exact mirror and bootstrap build pipeline IDs:

```text
ANY {ALL {resource.type = 'devopsbuildpipeline', resource.id = '<mirror-id>'}, ALL {resource.type = 'devopsbuildpipeline', resource.id = '<bootstrap-id>'}}
```

The shared build group grants mirroring permissions, not installation triggering.
The additional `<devops_dynamic_group_name>-bootstrap` group contains only the
bootstrap build pipeline and grants DevOps-family management:

```text
ALL {resource.type = 'devopsbuildpipeline', resource.id = '<bootstrap-id>'}
```

Bootstrap belongs to both build groups; mirror-only execution does not belong
to the bootstrap group. The `<devops_dynamic_group_name>-deployment` group contains only the
created installer:

```text
ALL {resource.type = 'devopsdeploypipeline', resource.id = '<installer-id>'}
```

No repositories, environments, connections, container instances, or other
pipelines in the same compartment become execution principals. Policies refer
to dynamic-group OCIDs, not ambiguous domain display names.

## Execution permissions

The stack attaches the policy to `iam_policy_compartment_id`, defaulting to the
tenancy root. This supports sibling DevOps, OKE, and network compartments.
An alternative policy location must be a common ancestor of every referenced
compartment. The statements still grant access only in the specified resource
compartments; placing the policy at the root does not grant tenancy-wide access.

`modules/iam/policies.tf` is the policy definition. The `execution_iam` output
exposes rendered statements, group OCIDs, membership rules, and execution IDs.

| Principal | Allowed access | Boundary |
| --- | --- | --- |
| Shared build group | Read project and pipeline-source repository | Exact project and `gitops-pipelines` repository IDs; bootstrap has additional DevOps-family access below |
| Shared build group | Inspect OCIR metadata/configuration | Actual DevOps project compartment |
| Shared build group | Read, create, push/update OCIR content | `${ocir_repo_path_prefix}/*`, with a slash boundary; no repository delete/manage permission |
| Bootstrap group and installer | Manage DevOps resources, including repositories, pipelines, deployments, environments and artifact references | Actual DevOps project compartment, including other projects/resources there; not exact-installer scoped |
| Installer | Read OCIR | Same prefix; no push/create/update |
| Installer | Read cluster, create kubeconfig, administer Kubernetes | Exact configured OKE cluster ID; no cluster create/delete/update permission |
| Installer | Create/read/delete ephemeral Shell containers and retrieve logs | Actual DevOps project compartment; no move, update, start/stop/restart permission |
| Installer | Use subnets/VNICs, read DHCP configuration | Selected network compartment |
| Installer | Use NSGs | Selected network compartment, only when an NSG is configured |
| Installer | Read credential secret bundles | Explicit secret IDs in the actual DevOps project compartment |

The user-approved DevOps-family grant follows the companion OCI DevOps asset's
execution-policy pattern. It deliberately trades fine-grained DevOps resource
boundaries for compatibility; bootstrap and installer can modify or delete
DevOps source repositories and other DevOps resources in the compartment.
Mirror-only execution does not receive that grant. OCIR, credential secrets,
cluster, Container Instance and network permissions retain their existing scopes;
no `read all-artifacts`, topic publishing, or IAM administration is added.

### OCIR pattern syntax

OCI IAM patterns are slash-delimited. Escape every slash inside the registry
prefix and the slash separating that prefix from the wildcard. The Terraform
expression used by execution and runtime-reader policies is:

```hcl
"/${replace(var.ocir_repo_path_prefix, "/", "\\/")}\\/*/"
```

For a prefix of `company-name/org`, the actual policy text is:

```text
target.repo.name = /company-name\/org\/*/
```

The trailing escaped slash preserves the intended prefix boundary; do not drop
it or broaden the pattern as a parsing workaround. OCI policy creation rejected
the unescaped form with `400 InvalidParameter` and accepted the escaped form for
both execution and runtime-reader policies during live validation. Subsequent
live mirror-build probes confirmed prefix matching for repository reads and
successful chart repository creation/push. Full chart/image mirroring and an
independently launched installer were subsequently verified; see the validation
status below. Full automatic bootstrap with the approved DevOps-family grants
subsequently passed.
Mocked regression tests check the rendered escapes for build writes, installer
reads, and runtime-reader access; they do not exercise OCI authorization.

### Live validation status

The functional-test operator reported these completed checks:

- Mirror-build isolation passed. The same `GetContainerRepository` API succeeded
  inside the prefix and was denied outside it. The probe harness recognized
  OCIR's `DENIED` response code as an authorization denial.
- The mirror-build principal was denied access to an unrelated Git repository, all
  tested credential secrets (including the installer secrets), and the selected
  OKE cluster.
- Creation of the in-prefix Argo CD chart repository and chart push succeeded.
- The mirror stage completed all chart and image mirroring successfully.
- The runtime Git reader received HTTP 200 for cluster-config and HTTP 401 for
  both an unrelated repository and the pipeline-source repository.
- The runtime OCIR reader received HTTP 200 for the chart and HTTP 403 outside
  the prefix.
- Under the earlier granular DevOps policy, the installer passed eight probes:
  allowed reads of the
  two credential secrets, selected cluster, and in-prefix OCIR repository;
  denied reads of the pipeline-source repository, unrelated Git repository,
  unrelated secret, and outside-prefix OCIR repository.
  Its Git-repository denials are historical results, not boundaries of the
  approved DevOps-family grant.
- Private-network Shell execution prepared the namespace and runtime secrets;
  Helm installation and healthy Argo CD workloads were verified.

The earlier installer was started by the applying user. A subsequent fresh
bootstrap build automatically triggered the installer and both completed
successfully with the approved DevOps-family policy. Namespace and credential
preparation and Helm installation passed. All seven Argo CD Applications remained
Synced and Healthy, and the public echoserver returned HTTP 200.

A temporary getter-permission-only probe succeeded and pipeline listing was
denied. Earlier granular-getter failures were not proven to be propagation.
At the user's request, bootstrap and installer now follow the companion DevOps
asset's compartment-scoped `manage devops-family` pattern. The policy was applied
and a fresh bootstrap build passed its pipeline-read preflight, mirroring, and
automatic deployment trigger. The triggered installer's namespace and credential
preparation and final Helm stage passed. The temporary
getter grant was revoked and the normal installer command restored. No further
narrow-getter tests are planned.

### Credential modes

Automatic mode grants the installer access to only the two generated secrets.
It ignores `execution_secret_ids`; build principals receive no secret access.

Manual mode accepts an advanced Terraform input `execution_secret_ids` containing
the Git and pull credential secret OCIDs. Both must be in the DevOps project
compartment. Set the same IDs in the bootstrap pipeline's
`git_read_credentials_secret_ocid` and `registry_pull_secret_ocid` parameters.
An empty allowlist produces **no secret policy**, not compartment-wide access.
Changing a runtime parameter cannot expand the IAM allowlist. With
`create_iam = false`, administrators must supply equivalent external execution
policies. Runtime reader policies remain independent.

### Residual boundaries and live verification

- Bootstrap and installer have DevOps-family management across the actual project
  compartment, not only this stack's project or installer. Use a dedicated DevOps
  compartment when unrelated projects must be isolated. Exact dynamic-group
  membership limits which principals receive this access, not which DevOps
  resources those principals may manage.
- Workload load balancers using NSG security-rule management require separate
  OKE cluster-principal permissions to manage NSGs and VCNs in their network
  compartment. DevOps execution dynamic groups do not authorize the cloud
  controller. Configure these permissions with the cluster infrastructure;
  see [Oracle's load-balancer requirements](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm).
- OCIR metadata inspection is compartment-wide because
  `GetContainerConfiguration` and `ListContainerRepositories` have no repository
  name target. It does not permit downloading unrelated images or repository
  writes outside the prefix. The current mirroring scripts require these calls.
- Network use is compartment-scoped, not subnet-ID scoped. The core policy
  reference does not document subnet/DHCP/NSG target-ID variables. Use a dedicated
  network compartment for stronger isolation. The configured stage still selects
  its subnet and optional NSG, but IAM does not enforce those exact selections.
- Ephemeral container create/delete/read permissions cover the project
  compartment, not only containers from this deployment. Their IDs are unknown
  before execution. Use a dedicated project compartment to isolate other jobs.
- `CLUSTER_MANAGE` is needed for `AdministerK8s` and also authorizes other
  operations mapped to that permission (for example cluster join/endpoint
  configuration). It is not namespace-only Kubernetes RBAC. Bootstrap installs
  cluster-scoped GitOps CRDs and roles; treat pipeline source editors and people
  allowed to start parameterized bootstrap runs as trusted cluster administrators.
- `REPOSITORY_UPDATE`, needed for pushing, also permits deleting/restoring image
  versions within the prefix. It does not include repository deletion or
  repository configuration management.
- OCI policies are additive. Pre-existing policies or other dynamic-group
  memberships can widen access. Audit both before relying on negative probes.
- Identity-domain group changes can take time to propagate. Static/mocked tests
  prove rendered boundaries, not OCI authorization. The completed and pending
  live checks are listed above. Verify bootstrap preflight and triggering before
  claiming end-to-end functional success with the approved DevOps-family pattern.

For live negative probes, first verify each outsider resource exists as the
applying user. Run read-only resource-principal getters for an unrelated DevOps
repository in the same project, an OCIR repository/image outside the prefix,
an unrelated cluster, and a dummy secret in the same secret compartment. Expect
authorization denial, not an empty list or a missing-resource error alone. Pair
each denial with an allowed getter using the same principal and API. Suppress
secret contents; check only exit status. Both builds must remain denied access
to installer credential secrets. Only mirror-only execution retains unrelated
DevOps repository denial; bootstrap and installer have the approved broader
DevOps access. Installer OCIR and unrelated-secret denials remain applicable.
No mutation is necessary for these negative probes. Test trigger authorization
through the actual bootstrap flow; a mirror-only run must not invoke a deployment.

Primary references:

- [DevOps policies, target variables, and stage requirements](https://docs.oracle.com/en-us/iaas/Content/devops/using/devops_iampolicies.htm)
- [OCIR resource variables and permission mapping](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/registrypolicyreference.htm)
- [OCIR push-only permission examples](https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm)
- [OKE target cluster and permission mapping](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/contengpolicyreference.htm)
- [Core networking policy reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/corepolicyreference.htm)
- [Container Instances policy reference](https://docs.oracle.com/en-us/iaas/Content/container-instances/permissions/policy-reference.htm)
- [Vault secret target variables](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/keypolicyreference.htm)

## Runtime reader policies

With `create_automatic_credentials = true`, the stack creates the reader users,
groups, tokens and JSON secrets, and their scoped access policy in the actual
DevOps project compartment. This policy is independent of `create_iam` and is
always created with the credentials. Git access covers only the generated
runtime repositories; registry access covers only `ocir_repo_path_prefix`.
See [Automatic runtime credentials](automatic-credentials.md).

The runtime identities are deliberately outside the DevOps dynamic group.
Place each non-human identity in a separate group and grant only its read
operation:

```text
Allow group <domain-name>/<gitops-reader-group> to read devops-project in compartment id compartmentOCID where target.project.id = '<project-id>'
Allow group <domain-name>/<gitops-reader-group> to read devops-repository in compartment id compartmentOCID where target.repository.id = '<runtime-repository-id>'
Allow group <domain-name>/<ocir-reader-group> to read repos in compartment id compartmentOCID where target.repo.name = /<ocir-prefix>/*/
```

Repeat the repository statement for each selected runtime repository, excluding
the pipeline-source repository. The GitOps reader must not receive
`manage devops-repository`; the OCIR
reader must not receive `manage repos`. The Resource Manager user's token is
used only for initial repository seeding and is not stored in the cluster.
