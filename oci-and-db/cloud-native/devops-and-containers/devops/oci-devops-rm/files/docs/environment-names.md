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

Select **Customize environment names** in **Environment Names** to reveal all
five inputs in Resource Manager. Unchecking hides all five inputs; saving the
Console form with customization off restores their defaults. Leave customization
enabled when saving a configuration with custom names.
The same inputs remain directly configurable through Terraform or the API. Names
must be lowercase DNS labels, with no slashes, spaces, or leading/trailing
hyphens. Application names must be distinct from each other; the two target
names must also be distinct. Application and cluster names may overlap because
they describe separate layers. Generated Helm release names are checked against
Helm's 53-character limit and for collisions within a cluster and namespace.

For stacks created or updated through the Resource Manager API, submit
`cluster_administration` as a JSON array of tool objects, or `[]` for
baseline-only administration. The graphical list control cannot render a
legacy wrapper such as `{"tools": []}`. Wrapped configurations remain accepted
by Terraform, but must be converted to the equivalent array before graphical
editing. Applications and Components use separate flat graphical lists to avoid
Resource Manager's nested-list serialization defect. Components reference their
application by name. See the [Quickstart](quickstart.md#applications) for inputs.

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

## Template Ownership

Choose names before the first apply. Changing names does not rename existing
Helm releases, update immutable Kubernetes selectors, or overwrite customer-owned
repository files and pipeline internals. Default names preserve the established
release identities and workflow keys.
