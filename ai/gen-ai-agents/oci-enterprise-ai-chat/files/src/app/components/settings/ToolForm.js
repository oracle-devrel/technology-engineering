"use client";

import { forwardRef, useEffect, useImperativeHandle, useReducer } from "react";
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
import { Icon } from "@iconify/react";
import mcpService from "../../services/mcpService";

function makeInitial(initial) {
  return {
    name: initial?.name || "",
    endpoint: initial?.endpoint || "",
    authType: initial?.authType || "none",
    authKey: initial?.authKey || "",
    oauthTokenUrl: initial?.oauth?.tokenUrl || "",
    oauthAuthorizeUrl: initial?.oauth?.authorizeUrl || "",
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

// Presets: one-click filler for popular OAuth providers that don't support dynamic
// client registration. User still has to paste their own clientId/clientSecret from
// the provider's developer console, but URLs and scopes are auto-populated.
const OAUTH_USER_PRESETS = [
  {
    id: 'google-gmail',
    label: 'Google Gmail',
    icon: 'logos:google-icon',
    authorizeUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl:     'https://oauth2.googleapis.com/token',
    scope:        'https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.compose',
  },
  {
    id: 'github',
    label: 'GitHub',
    icon: 'logos:github-icon',
    authorizeUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl:     'https://github.com/login/oauth/access_token',
    scope:        'repo read:user',
  },
  {
    id: 'slack',
    label: 'Slack',
    icon: 'logos:slack-icon',
    authorizeUrl: 'https://slack.com/oauth/v2/authorize',
    tokenUrl:     'https://slack.com/api/oauth.v2.access',
    scope:        'channels:read chat:write',
  },
];

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
  if (/Failed to fetch|NetworkError|ERR_NETWORK/i.test(raw)) return "Network error: endpoint unreachable, CORS blocked, or DNS issue.";
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
function ToolFormInner({ mode = "add", initialValues = null, onSave, onCancel, onStateChange }, ref) {
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
    } else if (s.authType === "oauth2-user") {
      // OAuth 2.0 authorization_code + PKCE with a pre-registered client.
      // Used for providers (Google, GitHub, Slack…) that do not implement
      // RFC 7591 dynamic client registration.
      server.oauth = {
        authorizeUrl: s.oauthAuthorizeUrl.trim(),
        tokenUrl:     s.oauthTokenUrl.trim(),
        clientId:     s.oauthClientId.trim(),
        clientSecret: s.oauthClientSecret.trim(),
        scope:        s.oauthScope.trim() || undefined,
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
    if (s.authType === "oauth2-user") {
      if (!s.oauthAuthorizeUrl.trim() || !s.oauthTokenUrl.trim() || !s.oauthClientId.trim()) return false;
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

  // Expose imperative handles so a parent (e.g. a Dialog rendering its own
  // DialogActions footer) can trigger save/test without owning the buttons.
  useImperativeHandle(ref, () => ({
    save: handleSave,
    test: handleTest,
  }), [handleSave, handleTest]);

  // Notify the parent about state changes that should drive button
  // enabled/loading states. Only emits primitive snapshots, no handlers,
  // so the dependency list stays simple and there is no risk of loops.
  useEffect(() => {
    onStateChange?.({
      isValid,
      isLoading: s.testLoading,
      authType: s.authType,
      testStatus: s.testStatus,
      testToolsCount: s.testTools?.length || 0,
    });
  }, [isValid, s.testLoading, s.authType, s.testStatus, s.testTools, onStateChange]);

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
            detectMsg: "OAuth 2.1 metadata detected, switched auth type to OAuth 2.1 (interactive). Click Add to register, then Authorize from the chat.",
            detecting: false,
          },
        });
        return;
      }
      d({ type: "patch", patch: { detecting: false, detectMsg: "No OAuth metadata at this URL. Keep current auth type." } });
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
        <FormControl size="small" sx={{ minWidth: 320 }}>
          <InputLabel>Authentication</InputLabel>
          <Select value={s.authType} label="Authentication" onChange={setAuthType}>
            <MuiMenuItem value="none">None: public MCP server</MuiMenuItem>
            <MuiMenuItem value="api-key">API Key: static header</MuiMenuItem>
            <MuiMenuItem value="bearer">Bearer Token: static token</MuiMenuItem>
            <MuiMenuItem value="oauth2">OAuth 2.0: Service (Client Credentials)</MuiMenuItem>
            <MuiMenuItem value="oauth2.1">OAuth 2.1: User Sign-in (Auto-discovery)</MuiMenuItem>
            <MuiMenuItem value="oauth2-user">OAuth 2.0: User Sign-in (Manual setup)</MuiMenuItem>
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

      {/* Inline guidance: which authType for what scenario */}
      <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.55))", mt: -1, ml: 0.5, lineHeight: 1.55 }}>
        {s.authType === "none" && "No credentials required. The MCP server is publicly reachable."}
        {s.authType === "api-key" && "The MCP server validates a fixed API key sent on every request as X-API-KEY."}
        {s.authType === "bearer" && "The MCP server validates a fixed bearer token sent as Authorization: Bearer <token>."}
        {s.authType === "oauth2" && "Server-to-server. No user login. You provide a client_id + client_secret, we fetch a short-lived token from the token URL on every request. Use for back-office connectors (e.g. IDCS, OIC) where the principal is the application itself."}
        {s.authType === "oauth2.1" && "User sign-in, fully automatic. The MCP server publishes /.well-known/oauth-authorization-server and supports RFC 7591 dynamic client registration. You only paste the endpoint, we register and run the PKCE flow."}
        {s.authType === "oauth2-user" && "User sign-in, manual setup. For providers that do NOT support dynamic registration (Google, GitHub, Slack, Microsoft). You pre-create an OAuth client in the provider's developer console, paste client_id + client_secret + the authorize/token URLs here, and we run the PKCE flow against them."}
      </Typography>

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
          After saving, click <strong>Authorize</strong> from the chat to sign in. PKCE and client registration are handled automatically.
        </Box>
      )}

      {s.authType === "oauth2-user" && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 2,
            borderLeft: "3px solid var(--dm-border, rgba(0,0,0,0.08))",
            paddingLeft: 2,
          }}
        >
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", alignItems: "center" }}>
            <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.55))", mr: 0.5 }}>
              Preset:
            </Typography>
            {OAUTH_USER_PRESETS.map(p => (
              <Chip
                key={p.id}
                icon={<Icon icon={p.icon} width={14} height={14} />}
                label={p.label}
                size="small"
                onClick={() => d({
                  type: "patch",
                  patch: {
                    oauthAuthorizeUrl: p.authorizeUrl,
                    oauthTokenUrl: p.tokenUrl,
                    oauthScope: p.scope,
                  },
                })}
                sx={{ fontSize: "0.72rem", cursor: "pointer", "& .MuiChip-icon": { ml: "8px", mr: "-4px" } }}
              />
            ))}
          </Box>
          <TextField
            label="Authorize URL"
            value={s.oauthAuthorizeUrl}
            onChange={set("oauthAuthorizeUrl")}
            placeholder="https://accounts.google.com/o/oauth2/v2/auth"
            size="small"
            fullWidth
          />
          <TextField
            label="Token URL"
            value={s.oauthTokenUrl}
            onChange={set("oauthTokenUrl")}
            placeholder="https://oauth2.googleapis.com/token"
            size="small"
            fullWidth
          />
          <Box sx={{ display: "flex", gap: 2 }}>
            <TextField
              label="Client ID"
              value={s.oauthClientId}
              onChange={set("oauthClientId")}
              placeholder="From provider's developer console"
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
            label="Scopes (space-separated)"
            value={s.oauthScope}
            onChange={set("oauthScope")}
            placeholder="e.g. https://www.googleapis.com/auth/gmail.readonly"
            size="small"
            fullWidth
          />
          <Box sx={{
            p: 1.5,
            borderRadius: 1,
            backgroundColor: "rgba(14, 165, 233, 0.06)",
            border: "1px solid rgba(14, 165, 233, 0.2)",
            fontSize: "0.78rem",
            color: "rgba(0,0,0,0.7)",
            lineHeight: 1.5,
          }}>
            Set your OAuth redirect URI in the provider's console to:{" "}
            <Box
              component="span"
              sx={{
                fontWeight: 600,
                fontFamily: "inherit",
                px: 0.5,
                py: 0.25,
                borderRadius: 0.5,
                backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.06))",
              }}
            >
              {typeof window !== "undefined" ? `${window.location.origin}/api/mcp/oauth/callback` : "<your-origin>/api/mcp/oauth/callback"}
            </Box>
            <br />After saving, click <strong>Authorize</strong> from the chat banner to sign in the first time.
          </Box>
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
            Ask the user to confirm before any tool from this server runs. Applies to all tools. OCI does not support per-tool granularity.
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
                        title={tool.description}
                        sx={{
                          fontSize: "0.75rem",
                          color: "var(--dm-muted, rgba(0,0,0,0.5))",
                          lineHeight: 1.5,
                          mt: 0.25,
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
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

const ToolForm = forwardRef(ToolFormInner);
export default ToolForm;
