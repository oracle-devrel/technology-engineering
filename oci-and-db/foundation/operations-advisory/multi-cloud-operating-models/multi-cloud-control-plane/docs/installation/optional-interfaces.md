# Install optional Project Team interfaces

After [first-project acceptance](../reference/verify-secret-isolation.md), add the interfaces selected for your organization. GitHub is ready with the core installation.

| Interface | Cloud Operations | Project Team |
| --- | --- | --- |
| GitHub | Hand off the accepted project repository. | Use the repository directly. |
| Multi-Cloud Control Plane UI | Configure the shared UI and its GitHub App. | Sign in with GitHub. |
| Codex plugin | Prepare the approved marketplace for the organization. | Install the plugin and authenticate GitHub CLI. |

## Optional Multi-Cloud Control Plane UI

Stage the UI from the `multi-cloud-control-plane` directory of a clean clone.

```bash
export INTERFACE_STAGE="$(mktemp -d)"
export UI_STAGE="$INTERFACE_STAGE/optional-ui"
cp -R repository-sources/optional-ui "$UI_STAGE"
test ! -e "$UI_STAGE/.env"
```

Follow the [UI setup guide](../../repository-sources/optional-ui/README.md#installation) for GitHub authorization, session settings, TLS and startup. Keep `.env` and credentials outside Git.

**Ready when:** a test user sees only the handed-off project repositories they can access, and a catalog form is available in the intended scope.

## Optional Codex plugin

Stage a local MCCP marketplace containing the plugin. Reuse `CUSTOMER_ORG` from the core installation; the commands bind the installed skill to that organization. Users cannot change this boundary in a request. Set `CODEX_MARKETPLACE_ROOT` to a persistent directory readable by the approved Project Team users:

```bash
: "${CUSTOMER_ORG:?set CUSTOMER_ORG to the installation organization}"
if ! [[ "$CUSTOMER_ORG" =~ ^[A-Za-z0-9]+(-[A-Za-z0-9]+)*$ ]] || \
  [ "${#CUSTOMER_ORG}" -gt 39 ]; then
  echo 'Set CUSTOMER_ORG to a valid GitHub organization name.' >&2
  exit 1
fi
export CODEX_MARKETPLACE_ROOT=/path/to/persistent/mccp-marketplace
export CODEX_PLUGIN_STAGE="$CODEX_MARKETPLACE_ROOT/plugins/project-gitops"
test ! -e "$CODEX_PLUGIN_STAGE"
mkdir -p "$CODEX_MARKETPLACE_ROOT/.agents/plugins" \
  "$CODEX_MARKETPLACE_ROOT/plugins"
cp -R codex-plugins/project-gitops "$CODEX_PLUGIN_STAGE"
test -f "$CODEX_PLUGIN_STAGE/LICENSE"
find "$CODEX_PLUGIN_STAGE/skills" -type f -name '*.md' -exec perl -pi -e \
  's/multicloud-control-plane/$ENV{CUSTOMER_ORG}/g' {} +
if [ "$CUSTOMER_ORG" != multicloud-control-plane ] && \
  rg 'multicloud-control-plane' "$CODEX_PLUGIN_STAGE/skills"; then
  echo 'The plugin still references the example organization.' >&2
  exit 1
fi

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

Each Project Team user installs the approved marketplace and plugin from a local shell.

```bash
codex --version
codex plugin marketplace add "$CODEX_MARKETPLACE_ROOT"
codex plugin add project-gitops@mccp
codex plugin list
```

**Ready when:** `codex plugin list` shows `project-gitops` from `mccp` and the user has authenticated GitHub CLI access to the handed-off project repository. Start a new Codex thread to load the plugin. Keep `CODEX_MARKETPLACE_ROOT` available while the marketplace is configured. Remove only unused staging artifacts after verifying the selected interfaces.
