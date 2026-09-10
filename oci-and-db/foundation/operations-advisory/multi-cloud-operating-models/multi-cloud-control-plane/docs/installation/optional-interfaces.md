# Install optional Project Team interfaces

The GitHub interface requires no additional MCCP component. Complete this page
only after the first project repository has passed the core acceptance check,
and only if the customer selected the optional Multi-Cloud Control Plane UI or Codex
plugin. Both prepare pull requests against the same handed-off project
repositories.

Cloud Operations installs the shared UI service or marketplace files once.
Each Project Team user then authorizes the UI or installs the Codex plugin in
their own shell. The GitHub interface remains available without either
optional component.

| Customer choice | Additional Cloud Operations action | Project Team result |
| --- | --- | --- |
| GitHub only | None after core acceptance. | Submit and review requests in the handed-off repository. |
| Multi-Cloud Control Plane UI | Install and configure the shared UI service. | Authorize the UI and prepare pull requests. |
| Codex plugin | Publish the approved local marketplace. | Install the plugin in a local shell and prepare pull requests. |

## Optional Multi-Cloud Control Plane UI

Stage the UI from the `multi-cloud-control-plane` directory of a clean clone:

```bash
export INTERFACE_STAGE="$(mktemp -d)"
export UI_STAGE="$INTERFACE_STAGE/optional-ui"
cp -R repository-sources/optional-ui "$UI_STAGE"
test ! -e "$UI_STAGE/.env"
```

Configure OAuth, session secrets, GitHub App permissions, TLS, and the runtime
using the [Multi-Cloud Control Plane technical guide](../../repository-sources/optional-ui/README.md).
Keep `.env` and all credentials outside Git. Before inviting Project Team
users, confirm that a test user can see only its handed-off project
repositories.

## Optional Codex plugin

Stage a local MCCP marketplace containing the plugin. Set
`CODEX_MARKETPLACE_ROOT` to a persistent directory readable by the approved
Project Team users:

```bash
export CODEX_MARKETPLACE_ROOT=/path/to/persistent/mccp-marketplace
export CODEX_PLUGIN_STAGE="$CODEX_MARKETPLACE_ROOT/plugins/project-gitops"
test ! -e "$CODEX_PLUGIN_STAGE"
mkdir -p "$CODEX_MARKETPLACE_ROOT/.agents/plugins" \
  "$CODEX_MARKETPLACE_ROOT/plugins"
cp -R codex-plugins/project-gitops "$CODEX_PLUGIN_STAGE"
test -f "$CODEX_PLUGIN_STAGE/LICENSE"

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
