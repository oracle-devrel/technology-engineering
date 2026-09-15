// Split an OpenAI-style function name `mcp__<serverLabel>__<toolName>` back into
// its parts. OCI exposes MCP tools to the model under this naming scheme, and the
// server label itself may contain underscores (it comes from sanitizing the
// user's server name: "PPT & Mail" → "PPT___Mail"), so a naive regex split at the
// first "__" can cut the label short. When the caller knows the configured labels
// (from the request's tools array), match against those first — longest first so
// "my_server_v2" wins over "my_server".
//
// Returns { serverLabel, toolName } or null when the name isn't an MCP mirror.
export function splitMcpFunctionName(fname, knownLabels = []) {
  if (typeof fname !== 'string' || !fname.startsWith('mcp__')) return null;
  const rest = fname.slice('mcp__'.length);

  const labels = [...new Set(knownLabels.filter(Boolean))].sort((a, b) => b.length - a.length);
  for (const label of labels) {
    if (rest.startsWith(`${label}__`)) {
      const toolName = rest.slice(label.length + 2);
      if (toolName) return { serverLabel: label, toolName };
    }
  }

  // Fallback for labels we don't know about: split at the first "__" boundary
  // (no consecutive underscores inside the label).
  const m = rest.match(/^([^_]+(?:_[^_]+)*?)__(.+)$/);
  return m ? { serverLabel: m[1], toolName: m[2] } : null;
}
