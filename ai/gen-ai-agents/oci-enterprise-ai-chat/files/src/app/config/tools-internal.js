// Internal-only tools content. Empty on the public/main branch.
// The private `internal` branch populates these. See CLAUDE.md "Branching strategy".

// Extra tabs registered into Settings → Tools tab bar (e.g. "Internal Marketplace").
// Each entry: { id: string, label: string, icon: ReactNode }.
// The corresponding JSX content for the tab lives in ToolsTab.js, gated by
// `INTERNAL_TOOL_TABS.length > 0 && activeTabId === <id>`.
export const INTERNAL_TOOL_TABS = [];

// Pre-configured addon servers prepended into ADDON_TOOLS in ToolsTab.js.
// Each entry follows the ADDON_TOOLS schema: { id, name, description, endpoint, authType, authKey?, color, icon|LogoComponent }.
// NEVER put internal endpoints, API keys, or Oracle-internal IPs on the public branch.
export const INTERNAL_ADDONS = [];
