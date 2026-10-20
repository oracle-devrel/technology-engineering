# Environment Names

Environment names are configurable when creating a new starter installation.
The workflow still has three application roles and two cluster targets; names
do not add stages, change cluster selection, or change approval requirements.

| Input | Default | Example |
| --- | --- | --- |
| `dev_environment_name` | `dev` | `development` |
| `staging_environment_name` | `staging` | `uat` |
| `prod_environment_name` | `prod` | `live` |
| `noprod_cluster_name` | `noprod` | `sandbox` |
| `prod_cluster_name` | `prod` | `production` |

Configure the application names in **Application Environment Names**, and the
cluster target names alongside their OKE selectors in Resource Manager. Names
must be lowercase DNS labels, with no slashes, spaces, or leading/trailing
hyphens. Application names must be distinct from each other; the two target
names must also be distinct. Application and cluster names may overlap because
they describe separate layers. Generated Helm release names are checked against
Helm's 53-character limit and for collisions within a cluster and namespace.

## Generated Naming

With the example settings above, component `invoice` has releases
`invoice-development`, `invoice-uat`, and `invoice` in production. Production
continues to omit the environment suffix, use the promoted final image, require
approval, and tag the released source commit. Kubernetes labels use the
configured environment name, while Helm's `environmentRole` carries the stable
workflow role. Older charts/values using `environment: prod` without a role
retain the default production behavior.

The application baseline releases are `<application>-sandbox` and
`<application>`; bootstrap stages use the configured target names. Cluster
administration uses `cluster-admin-sandbox`, `cluster-admin-production`, their
explicit decommission pipelines, and `clusters/sandbox` / `clusters/production`
directories. The `clusters` map in stack-managed `catalog/tools.yaml` records
the role-to-name mapping. Production approval is always selected by role,
regardless of the chosen name. The two targets may use the same physical OKE
cluster, as before.

Custom target names are also used for new OCI DevOps OKE environment display
names. Leaving the target defaults unchanged preserves the previous convention
of using the selected OKE cluster's name. The actual OKE clusters and Kubernetes
namespaces are not renamed; namespace overrides remain per application.

Terraform resource keys and existing pipeline-ID output keys remain role-based
(`dev`, `staging`, `noprod`, `prod`). The `environment_names` output provides
the configured names for those roles. Build-only mode does not create application
deployment resources; cluster administration remains independently selectable.

## Existing Installations

Keeping the defaults preserves existing release identities and workflow keys.
Changing the inputs is **not** an automatic rename or migration of an installed
solution. Customer-owned pipelines, stages, artifacts and repository paths retain
their ownership protections; a newer stack does not overwrite their internals.
The generated cluster catalog remains stack-managed, so do not change target
names on a live stack until its pipelines and repository directories are ready.

For an existing installation:

1. Inventory the current releases, namespaces, pipeline overrides and Git paths.
2. Prepare reviewed repository changes, including the chart's `environmentRole`,
   custom directory names, runtime scripts, command specs and pipeline defaults.
3. Plan the coordinated OCI resource/catalog changes explicitly. Stable Terraform
   keys alone do not update resources protected by lifecycle ignores.
4. Treat changed Helm release names as new releases. Kubernetes selector labels
   are immutable, and production names can stay the same while selectors change;
   plan controlled replacement or a separate namespace rather than expecting
   an in-place Helm rename. Check Service selectors and traffic before retiring
   old workloads.
5. Retain production approvals and run the full delivery and cluster-admin
   workflow before removing old resources. Nothing is automatically pruned.

Choose names before the first apply whenever possible. There is no automatic
destructive migration in this feature.
