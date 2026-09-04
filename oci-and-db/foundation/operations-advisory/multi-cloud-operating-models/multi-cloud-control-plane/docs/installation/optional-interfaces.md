# Install optional Project Team interfaces

The GitHub interface requires no additional MCCP component. Complete this page
only after the first project repository has passed the core acceptance check,
and only if the customer selected the optional Multi-Cloud Plane UI or Codex
plugin. Both prepare pull requests against the same handed-off project
repositories.

Cloud Operations installs the shared UI service or marketplace files once.
Each Project Team user then authorizes the UI or installs the Codex plugin in
their own shell. The GitHub interface remains available without either
optional component.

## Prepare the installation configuration

Use the customer organization and immutable `gitops-templates` commit recorded
as organization installation evidence. Run these commands from the
`multi-cloud-control-plane` directory of a clean clone:

```bash
export CUSTOMER_ORG=example-enterprise
export CATALOGS_REF=0123456789abcdef0123456789abcdef01234567
export INTERFACE_STAGE="$(mktemp -d)"

jq -n \
  --arg customer_org "$CUSTOMER_ORG" \
  --arg catalog_revision "$CATALOGS_REF" \
  '{
    schema_version: 1,
    customer_org: $customer_org,
    catalog_revision: $catalog_revision
  }' > "$INTERFACE_STAGE/mccp-installation.json"

jq -e '
  .schema_version == 1 and
  (.customer_org | type == "string" and length > 0) and
  (.catalog_revision | test("^[0-9a-f]{40}$"))
' "$INTERFACE_STAGE/mccp-installation.json" >/dev/null

test "$(git ls-remote "https://github.com/$CUSTOMER_ORG/gitops-templates.git" \
  refs/heads/main | cut -f1)" = "$CATALOGS_REF"
```

The final `test` must return exit code zero. The rendered file is non-secret;
it prevents either interface from selecting another organization or a mutable
catalog revision.

## Optional Multi-Cloud Plane UI

Stage the UI and place the rendered configuration beside its runtime:

```bash
export UI_STAGE="$INTERFACE_STAGE/optional-ui"
cp -R repository-sources/optional-ui "$UI_STAGE"
cp "$INTERFACE_STAGE/mccp-installation.json" "$UI_STAGE/mccp-installation.json"
test ! -e "$UI_STAGE/.env"
```

Configure OAuth, session secrets, GitHub App permissions, TLS, and the runtime
using the [Multi-Cloud Plane technical guide](../../repository-sources/optional-ui/README.md).
Keep `.env` and all credentials outside Git. Before inviting Project Team
users, confirm that the UI reads the recorded catalog revision and that a test
user can see only its handed-off project repositories.

## Optional Codex plugin

Stage a local MCCP marketplace containing the plugin and the same rendered
configuration. Set `CODEX_MARKETPLACE_ROOT` to a persistent directory readable
by the approved Project Team users:

```bash
export CODEX_MARKETPLACE_ROOT=/path/to/persistent/mccp-marketplace
export CODEX_PLUGIN_STAGE="$CODEX_MARKETPLACE_ROOT/plugins/project-gitops"
test ! -e "$CODEX_PLUGIN_STAGE"
mkdir -p "$CODEX_MARKETPLACE_ROOT/.agents/plugins" \
  "$CODEX_MARKETPLACE_ROOT/plugins"
cp -R codex-plugins/project-gitops "$CODEX_PLUGIN_STAGE"
cp "$INTERFACE_STAGE/mccp-installation.json" \
  "$CODEX_PLUGIN_STAGE/mccp-installation.json"
jq -e . "$CODEX_PLUGIN_STAGE/mccp-installation.json" >/dev/null

jq -n '
  {
    name: "mccp",
    interface: {displayName: "Multi-Cloud Control Plane"},
    plugins: [
      {
        name: "project-gitops",
        source: {source: "local", path: "./plugins/project-gitops"},
        policy: {installation: "AVAILABLE", authentication: "ON_INSTALL"},
        category: "Productivity"
      }
    ]
  }
' > "$CODEX_MARKETPLACE_ROOT/.agents/plugins/marketplace.json"

jq -e . "$CODEX_MARKETPLACE_ROOT/.agents/plugins/marketplace.json" >/dev/null
```

Each Project Team user installs the approved marketplace and plugin from a
local shell:

```bash
codex --version
codex plugin marketplace add "$CODEX_MARKETPLACE_ROOT"
codex plugin add project-gitops@mccp
codex plugin list
```

`codex plugin list` must show `project-gitops` from the `mccp` marketplace.
Each user also needs authenticated GitHub CLI access and permission to the
handed-off project repository. Start a new Codex thread after installation so
the plugin is loaded. Keep `CODEX_MARKETPLACE_ROOT` available while the
marketplace is configured. Remove only unused temporary staging artifacts after
both optional interfaces have been verified.
