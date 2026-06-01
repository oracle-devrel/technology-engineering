"use client";

import { useReducer } from "react";
import {
  Box,
  TextField,
  Select,
  MenuItem as MuiMenuItem,
  FormControl,
  InputLabel,
  Button,
  Chip,
  Switch,
  IconButton,
  InputAdornment,
  CircularProgress,
  Typography,
  Tooltip,
  FormControlLabel,
} from "@mui/material";
import { Plug, Eye, EyeOff, X, Check, Wand2, Wrench, ShieldAlert } from "lucide-react";
import mcpService from "../../services/mcpService";

function makeInitial(initial) {
  return {
    name: initial?.name || "",
    endpoint: initial?.endpoint || "",
    authType: initial?.authType || "none",
    authKey: initial?.authKey || "",
    oauthTokenUrl: initial?.oauth?.tokenUrl || "",
    oauthClientId: initial?.oauth?.clientId || "",
    oauthClientSecret: initial?.oauth?.clientSecret || "",
    oauthScope: initial?.oauth?.scope || "",
    testStatus: null, // 'connected' | 'error' | null
    testLoading: false,
    testTools: null,
    testError: null,
    showSecret: false,
    detecting: false,
    detectMsg: null,
    // Server-level human approval. OCI only supports per-server granularity for
    // `require_approval`, so we use a single boolean. Legacy configs may have
    // `requireApprovalTools` (array) — treat any non-empty array as "on".
    requireApproval: initial?.requireApproval === true
      || (Array.isArray(initial?.requireApprovalTools) && initial.requireApprovalTools.length > 0),
  };
}

function reducer(state, action) {
  switch (action.type) {
    case "set":
      return { ...state, [action.field]: action.value };
    case "patch":
      return { ...state, ...action.patch };
    case "resetTest":
      return { ...state, testStatus: null, testError: null, testTools: null };
    default:
      return state;
  }
}

function formatTestError(err) {
  const raw = err?.message || String(err) || "Unknown error";
  if (/MCP request failed:\s*401/i.test(raw)) return "Authentication failed (401). Check the auth type and credentials.";
  if (/MCP request failed:\s*403/i.test(raw)) return "Forbidden (403). Credentials valid but lack permission.";
  if (/MCP request failed:\s*404/i.test(raw)) return "Endpoint not found (404). Check the URL.";
  if (/MCP request failed:\s*5\d\d/i.test(raw)) return `Server error: ${raw.replace(/MCP request failed:\s*/i, "")}`;
  if (/Failed to fetch|NetworkError|ERR_NETWORK/i.test(raw)) return "Network error — endpoint unreachable, CORS blocked, or DNS issue.";
  if (/needs_auth/i.test(raw)) return "OAuth flow required. Use authType OAuth 2.1 (interactive) for this endpoint.";
  return raw.length > 240 ? raw.slice(0, 240) + "…" : raw;
}

/**
 * Unified form for adding or editing a custom MCP tool.
 *
 * Props:
 *   - mode: 'add' | 'edit'
 *   - initialValues: existing server (for edit)
 *   - onSave: (serverData, testTools) => void   — receives the data to persist
 *   - onCancel: () => void
 */
export default function ToolForm({ mode = "add", initialValues = null, onSave, onCancel }) {
  const isEdit = mode === "edit";
  const [s, d] = useReducer(reducer, initialValues, makeInitial);

  const set = (field) => (e) => {
    d({ type: "set", field, value: e.target.value });
    // Any field change invalidates the previous test result
    if (s.testStatus) d({ type: "resetTest" });
  };

  const setAuthType = (e) => {
    d({ type: "patch", patch: { authType: e.target.value } });
    d({ type: "resetTest" });
  };

  // Build the server config from the current form values.
  const buildServer = (id) => {
    const server = {
      id: id || (isEdit ? initialValues.id : "test-new"),
      name: s.name.trim(),
      endpoint: s.endpoint.trim(),
      authType: s.authType !== "none" ? s.authType : undefined,
    };
    if (s.authType === "api-key" || s.authType === "bearer") {
      if (s.authKey.trim()) server.authKey = s.authKey.trim();
    } else if (s.authType === "oauth2") {
      server.oauth = {
        tokenUrl: s.oauthTokenUrl.trim(),
        clientId: s.oauthClientId.trim(),
        clientSecret: s.oauthClientSecret.trim(),
        scope: s.oauthScope.trim() || undefined,
      };
    }
    // oauth2.1 is handled by the OAuth flow (no creds in form)
    server.requireApproval = !!s.requireApproval;
    return server;
  };

  // Required-field validation for the save button
  const isValid = (() => {
    if (!s.endpoint.trim()) return false;
    if (mode === "add" && !s.name.trim()) return false;
    if (s.authType === "api-key" || s.authType === "bearer") {
      if (!s.authKey.trim() && !(isEdit && initialValues?.authKey)) return false;
    }
    if (s.authType === "oauth2") {
      if (!s.oauthTokenUrl.trim() || !s.oauthClientId.trim()) return false;
      if (!s.oauthClientSecret.trim() && !(isEdit && initialValues?.oauth?.clientSecret)) return false;
    }
    return true;
  })();

  const handleTest = async () => {
    d({ type: "patch", patch: { testLoading: true, testStatus: null, testError: null, testTools: null } });
    try {
      const tools = await mcpService.listToolsFromServer(buildServer("test-" + (isEdit ? initialValues.id : "new")));
      d({ type: "patch", patch: { testLoading: false, testStatus: "connected", testTools: tools || [] } });
      return tools || [];
    } catch (err) {
      d({ type: "patch", patch: { testLoading: false, testStatus: "error", testError: formatTestError(err) } });
      return null;
    }
  };

  const handleSave = async () => {
    if (!isValid) return;
    // OAuth 2.1 is interactive — the test would just trigger needs_auth.
    // Save first; the user authorizes from the chat banner or explicitly.
    let tools = s.testTools;
    if (s.authType !== "oauth2.1" && s.testStatus !== "connected") {
      tools = await handleTest();
      if (!tools) return;
    }
    onSave(buildServer(), tools || []);
  };

  // Auto-discovery: try /.well-known/oauth-authorization-server on the endpoint origin
  const handleDetect = async () => {
    if (!s.endpoint.trim()) return;
    d({ type: "patch", patch: { detecting: true, detectMsg: null } });
    try {
      const u = new URL(s.endpoint.trim());
      // Common locations OAuth 2.1 servers expose metadata
      const candidates = [
        `${u.origin}/.well-known/oauth-authorization-server`,
        `${u.origin}/.well-known/openid-configuration`,
        // Some MCPs publish under their base path
        `${u.origin}${u.pathname.replace(/\/?$/, "")}/.well-known/oauth-authorization-server`,
      ];
      let meta = null;
      for (const url of candidates) {
        try {
          const res = await fetch(url);
          if (res.ok) {
            meta = await res.json();
            break;
          }
        } catch { /* try next */ }
      }
      if (meta) {
        // Authorization server found → suggest OAuth 2.1 interactive flow
        d({
          type: "patch",
          patch: {
            authType: "oauth2.1",
            oauthTokenUrl: meta.token_endpoint || s.oauthTokenUrl,
            detectMsg: "OAuth 2.1 metadata detected — switched auth type to OAuth 2.1 (interactive). Click Add to register, then Authorize from the chat.",
            detecting: false,
          },
        });
        return;
      }
      d({ type: "patch", patch: { detecting: false, detectMsg: "No OAuth metadata at this URL — keep current auth type." } });
    } catch (e) {
      d({ type: "patch", patch: { detecting: false, detectMsg: `Detect failed: ${e.message || e}` } });
    }
  };

  const showSecretAdornment = (
    <InputAdornment position="end">
      <IconButton size="small" onClick={() => d({ type: "set", field: "showSecret", value: !s.showSecret })} edge="end">
        {s.showSecret ? <EyeOff size={16} /> : <Eye size={16} />}
      </IconButton>
    </InputAdornment>
  );


  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {mode === "add" && (
        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
          Add MCP Tool
        </Typography>
      )}

      {mode === "add" && (
        <TextField
          label="Tool Name"
          value={s.name}
          onChange={set("name")}
          placeholder="e.g., Suppliers MCP"
          size="small"
          fullWidth
          autoFocus
        />
      )}
      {isEdit && (
        <TextField
          label="Tool Name"
          value={s.name}
          onChange={set("name")}
          size="small"
          fullWidth
          autoFocus
        />
      )}

      <TextField
        label="Endpoint URL"
        value={s.endpoint}
        onChange={set("endpoint")}
        placeholder="https://mcp.example.com/mcp"
        size="small"
        fullWidth
        slotProps={{
          input: {
            endAdornment: (
              <InputAdornment position="end">
                <Tooltip title="Detect OAuth metadata at the endpoint origin">
                  <span>
                    <IconButton
                      size="small"
                      onClick={handleDetect}
                      disabled={!s.endpoint.trim() || s.detecting}
                      edge="end"
                    >
                      {s.detecting ? <CircularProgress size={14} /> : <Wand2 size={14} />}
                    </IconButton>
                  </span>
                </Tooltip>
              </InputAdornment>
            ),
          },
        }}
      />
      {s.detectMsg && (
        <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.55))", mt: -1, ml: 0.5 }}>
          {s.detectMsg}
        </Typography>
      )}

      <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
        <FormControl size="small" sx={{ minWidth: 220 }}>
          <InputLabel>Authentication</InputLabel>
          <Select value={s.authType} label="Authentication" onChange={setAuthType}>
            <MuiMenuItem value="none">None</MuiMenuItem>
            <MuiMenuItem value="api-key">API Key (X-API-KEY)</MuiMenuItem>
            <MuiMenuItem value="bearer">Bearer Token</MuiMenuItem>
            <MuiMenuItem value="oauth2">OAuth 2.0 (Client Credentials)</MuiMenuItem>
            <MuiMenuItem value="oauth2.1">OAuth 2.1 (Interactive / PKCE)</MuiMenuItem>
          </Select>
        </FormControl>

        {(s.authType === "api-key" || s.authType === "bearer") && (
          <TextField
            label={s.authType === "bearer" ? "Bearer Token" : "API Key"}
            value={s.authKey}
            onChange={set("authKey")}
            placeholder={s.authType === "bearer" ? "Enter bearer token" : "Enter API key"}
            size="small"
            fullWidth
            type={s.showSecret ? "text" : "password"}
            slotProps={{ input: { endAdornment: showSecretAdornment } }}
          />
        )}
      </Box>

      {s.authType === "oauth2" && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            borderLeft: "3px solid var(--dm-border, rgba(0,0,0,0.08))",
            paddingLeft: 2,
          }}
        >
          <TextField
            label="Token URL"
            value={s.oauthTokenUrl}
            onChange={set("oauthTokenUrl")}
            placeholder="https://idcs-xxxx.identity.oraclecloud.com/oauth2/v1/token"
            size="small"
            fullWidth
          />
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Client ID"
              value={s.oauthClientId}
              onChange={set("oauthClientId")}
              size="small"
              fullWidth
            />
            <TextField
              label="Client Secret"
              value={s.oauthClientSecret}
              onChange={set("oauthClientSecret")}
              size="small"
              fullWidth
              type={s.showSecret ? "text" : "password"}
              slotProps={{ input: { endAdornment: showSecretAdornment } }}
            />
          </Box>
          <TextField
            label="Scope (optional)"
            value={s.oauthScope}
            onChange={set("oauthScope")}
            placeholder="e.g. urn:opc:resource:consumer::all"
            size="small"
            fullWidth
          />
        </Box>
      )}

      {s.authType === "oauth2.1" && (
        <Box
          sx={{
            p: 1.5,
            borderRadius: 1,
            backgroundColor: "rgba(14, 165, 233, 0.06)",
            border: "1px solid rgba(14, 165, 233, 0.2)",
            fontSize: "0.78rem",
            color: "rgba(0,0,0,0.7)",
            lineHeight: 1.5,
          }}
        >
          OAuth 2.1 is interactive. After saving, click <strong>Authorize</strong> from the chat banner the first time
          a tool from this server is invoked. PKCE + dynamic client registration is performed automatically using the
          server&apos;s discovery metadata.
        </Box>
      )}

      {s.testStatus === "error" && s.testError && (
        <Box
          sx={{
            p: 1.25,
            borderRadius: 1,
            backgroundColor: "rgba(211, 47, 47, 0.06)",
            border: "1px solid rgba(211, 47, 47, 0.2)",
            fontSize: "0.78rem",
            color: "#c62828",
            lineHeight: 1.45,
          }}
        >
          {s.testError}
        </Box>
      )}

      <Box sx={{ display: "flex", gap: 1, justifyContent: "flex-end", alignItems: "center" }}>
        {s.testStatus === "connected" && (
          <Chip
            icon={<Plug size={14} />}
            label={s.testTools ? `Connected · ${s.testTools.length} tools` : "Connected"}
            size="small"
            color="success"
            variant="outlined"
            sx={{ mr: 1 }}
          />
        )}
        <Button variant="outlined" size="small" onClick={onCancel} startIcon={<X size={14} />}>
          Cancel
        </Button>
        {s.authType !== "oauth2.1" && (
          <Button
            variant="outlined"
            size="small"
            onClick={handleTest}
            disabled={!isValid || s.testLoading}
            startIcon={s.testLoading ? <CircularProgress size={14} /> : <Plug size={14} />}
          >
            Test Connection
          </Button>
        )}
        <Button
          variant="contained"
          size="small"
          onClick={handleSave}
          disabled={!isValid || s.testLoading}
          startIcon={s.testLoading ? <CircularProgress size={14} /> : <Check size={14} />}
        >
          {isEdit ? "Save" : "Add Tool"}
        </Button>
      </Box>

      {/* Server-level human approval. OCI Responses API only supports per-server
          granularity for require_approval, so this is a single switch. */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          p: 1.5,
          borderRadius: 1.5,
          border: `1px solid ${s.requireApproval ? "rgba(240, 162, 59, 0.45)" : "var(--dm-border, rgba(0,0,0,0.08))"}`,
          backgroundColor: s.requireApproval ? "rgba(240, 162, 59, 0.06)" : "transparent",
        }}
      >
        <ShieldAlert size={18} style={{ color: s.requireApproval ? "#b26a00" : "var(--dm-muted, rgba(0,0,0,0.35))", flexShrink: 0 }} />
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography sx={{ fontSize: "0.85rem", fontWeight: 600, color: "var(--dm-text, #1a1a1a)" }}>
            Require user approval
          </Typography>
          <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.55))", lineHeight: 1.4 }}>
            Ask the user to confirm before any tool from this server runs. Applies to all tools — OCI does not support per-tool granularity.
          </Typography>
        </Box>
        <Switch
          size="small"
          checked={!!s.requireApproval}
          onChange={(e) => d({ type: "set", field: "requireApproval", value: e.target.checked })}
          sx={{
            "& .MuiSwitch-switchBase.Mui-checked": { color: "#b26a00" },
            "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": { backgroundColor: "#b26a00" },
          }}
        />
      </Box>

      {/* Test results — list discovered tools so the user can verify the connection. */}
      {(() => {
        const toolsList = (s.testStatus === "connected" && s.testTools)
          ? s.testTools
          : (Array.isArray(initialValues?.tools) ? initialValues.tools : null);
        if (!toolsList || toolsList.length === 0) return null;
        return (
          <Box
            sx={{
              mt: 1,
              p: 2,
              backgroundColor: "rgba(46, 125, 50, 0.04)",
              borderRadius: 1.5,
              border: "1px solid rgba(46, 125, 50, 0.15)",
            }}
          >
            <Typography sx={{ fontSize: "0.8rem", fontWeight: 600, color: "#2e7d32", mb: 1.5 }}>
              {toolsList.length} function{toolsList.length !== 1 ? "s" : ""}
            </Typography>
            <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
              {toolsList.map((tool) => (
                <Box
                  key={tool.name}
                  sx={{
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 1.5,
                    p: 1.5,
                    backgroundColor: "var(--dm-surface)",
                    borderRadius: 1,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
                  }}
                >
                  <Wrench size={15} style={{ color: "var(--dm-muted, rgba(0,0,0,0.35))", marginTop: 2, flexShrink: 0 }} />
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography sx={{ fontWeight: 500, fontSize: "0.85rem" }}>{tool.name}</Typography>
                    {tool.description && (
                      <Typography
                        sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", lineHeight: 1.5, mt: 0.25 }}
                      >
                        {tool.description}
                      </Typography>
                    )}
                  </Box>
                </Box>
              ))}
            </Box>
          </Box>
        );
      })()}
    </Box>
  );
}
