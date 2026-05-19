"use client";

import { Box, IconButton, TextField, Typography, Chip, createTheme, ThemeProvider, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import Image from "next/image";
import { useState, useEffect, useMemo } from "react";
import IOSSwitch from "../ui/IOSSwitch";
import { Building2, Moon, Sun, Settings as SettingsIcon, Users } from "lucide-react";
import Header from "../ui/Header";
import ChatSidebar from "../chat/ChatSidebar";
import { DARK_BG } from "../../config/darkMode";



const STORAGE_KEYS = {
  UI_SETTINGS: 'uiSettings',
};

const DEFAULT_UI_SETTINGS = {
  appTitle: "OCI Enterprise AI Agents",
  appLogo: "",
  welcomeMessage: "Welcome back!",
  inputPlaceholder: "Type anything...",
  accentColor: "#C74634",
  showLabChip: true,
  showLabIcon: true,
  darkMode: false,
};

export default function GeneralTab() {
  const [uiSettings, setUiSettings] = useState(DEFAULT_UI_SETTINGS);
  const [logoError, setLogoError] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  const pAccent = uiSettings.accentColor || "#C74634";
  const isDarkBg = uiSettings.darkMode === true;

  const baseTheme = useTheme();
  const previewTheme = useMemo(() => {
    if (!isDarkBg) return baseTheme;
    return createTheme({
      ...baseTheme,
      palette: {
        ...baseTheme.palette,
        mode: "dark",
        background: { default: DARK_BG, paper: "#242424" },
        text: { primary: "#e5e5e5", secondary: "rgba(255,255,255,0.5)" },
        divider: "rgba(255,255,255,0.08)",
      },
    });
  }, [isDarkBg, baseTheme]);

  // Load from localStorage after mount (client-only)
  useEffect(() => {
    const storedUiSettings = localStorage.getItem(STORAGE_KEYS.UI_SETTINGS);
    if (storedUiSettings) {
      try {
        setUiSettings(JSON.parse(storedUiSettings));
      } catch (e) {
        console.error('Error parsing stored UI settings:', e);
      }
    }
    setIsHydrated(true);
  }, []);

  // Save UI settings to localStorage whenever they change (after hydration)
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem(STORAGE_KEYS.UI_SETTINGS, JSON.stringify(uiSettings));
      window.dispatchEvent(new CustomEvent('uiSettingsChanged', { detail: uiSettings }));
    }
  }, [uiSettings, isHydrated]);

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Typography
        variant="h6"
        sx={{
          fontSize: "1.1rem",
          fontWeight: 400,
          color: "var(--dm-text, #1a1a1a)",
          mb: 3
        }}
      >
        Appearance
      </Typography>
      
      {/* Live Preview — real components, scaled down & non-interactive */}
      <Box sx={{
        border: "1px solid var(--dm-border, rgba(0,0,0,0.1))",
        borderRadius: 2,
        overflow: "hidden",
        mb: 3,
        backgroundColor: "var(--dm-subtle, #fafafa)",
      }}>
        <Typography sx={{ fontSize: "0.65rem", color: "var(--dm-muted, rgba(0,0,0,0.35))", px: 1.5, pt: 1, fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.5px" }}>
          Preview
        </Typography>
        <Box sx={{ p: 1.5, pt: 0.5, display: "flex", justifyContent: "center" }}>
          {/* Viewport window — clips the scaled content */}
          <Box sx={{
            borderRadius: "12px",
            height: 280,
            maxWidth: 520,
            width: "100%",
            overflow: "hidden",
            position: "relative",
            backgroundColor: isDarkBg ? DARK_BG : "#fff",
            boxShadow: `inset 0 0 0 1px ${isDarkBg ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)"}`,
          }}>
            {/* Scaled container — renders at full size, scaled down to fit */}
            <ThemeProvider theme={previewTheme}>
              <Box sx={{
                width: 1440,
                height: 900,
                transform: "scale(0.36)",
                transformOrigin: "top left",
                pointerEvents: "none",
                position: "absolute",
                top: 0,
                left: 0,
                backgroundColor: isDarkBg ? DARK_BG : "#fff",
                display: "flex",
                flexDirection: "column",
              }}>
                {/* Real Header */}
                <Header
                  models={["google.gemini-2.5-pro"]}
                  selectedModel="google.gemini-2.5-pro"
                  onModelChange={() => {}}
                  onNewConversation={() => {}}
                  chatHistory={[]}
                  showLabChip={uiSettings.showLabChip !== false}
                  showLabIcon={uiSettings.showLabIcon !== false}
                  appTitle={uiSettings.appTitle}
                  accentColor={pAccent}
                  isDarkBg={isDarkBg}
                />

                {/* Body: sidebar + divider + chat */}
                <Box sx={{ display: "flex", flex: 1, pt: "60px", height: "100%", boxSizing: "border-box" }}>
                  {/* Real ChatSidebar */}
                  <ChatSidebar
                    uiSettings={uiSettings}
                    showTextField={true}
                    chatHistoryLength={0}
                    inputRef={{ current: null }}
                    onSubmit={() => {}}
                    onStop={() => {}}
                    recentConversations={[
                      { id: "1", title: "Sales pipeline analysis Q4" },
                      { id: "2", title: "Draft marketing email" },
                      { id: "3", title: "K8s deployment help" },
                    ]}
                    activeConversationId="1"
                    onConversationClick={() => {}}
                    onConversationDelete={() => {}}
                    onRefreshConversations={() => {}}
                    isLoading={false}
                    width={30}
                    selectedModel="google.gemini-2.5-pro"
                    accentColor={pAccent}
                    isDarkBg={isDarkBg}
                  />

                  {/* Divider */}
                  <Box sx={{
                    width: "9px",
                    position: "relative",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    "&::before": {
                      content: '""',
                      position: "absolute",
                      top: 0,
                      bottom: 0,
                      left: "50%",
                      transform: "translateX(-50%)",
                      width: "1px",
                      backgroundColor: isDarkBg ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)",
                    },
                  }}>
                    <Box sx={{
                      width: "8px",
                      height: "28px",
                      borderRadius: "4px",
                      backgroundColor: isDarkBg ? DARK_BG : "#fff",
                      border: `1px solid ${isDarkBg ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.08)"}`,
                      zIndex: 1,
                    }} />
                  </Box>

                  {/* Chat area (lightweight mock — no ChatMessage needed) */}
                  <Box sx={{
                    flex: 1,
                    pt: 4,
                    px: 5,
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    color: isDarkBg ? "#e5e5e5" : "inherit",
                  }}>
                    <Box sx={{ maxWidth: 700 }}>
                      {/* User message */}
                      <Typography sx={{
                        textAlign: "right",
                        fontSize: "1rem",
                        fontWeight: 300,
                        color: isDarkBg ? "#e5e5e5" : "#000",
                        opacity: 0.8,
                        mb: 2,
                      }}>
                        Tell me about the latest sales numbers
                      </Typography>
                      {/* Assistant response */}
                      <Typography sx={{
                        fontSize: "1rem",
                        fontWeight: 300,
                        color: isDarkBg ? "#e5e5e5" : "#000",
                        opacity: 0.6,
                        lineHeight: 1.7,
                      }}>
                        Based on the Q4 data, total revenue increased 12% compared to last quarter, reaching $2.4M across all regions. The EMEA region showed the strongest growth at 18%, while APAC maintained steady performance.
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                {/* FAB */}
                <Box sx={{
                  position: "absolute",
                  bottom: 24,
                  right: 24,
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  px: 2,
                  py: 1,
                  borderRadius: 10,
                  zIndex: 1200,
                  backgroundColor: isDarkBg ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.9)",
                  border: `1px solid ${isDarkBg ? "rgba(255,255,255,0.10)" : "rgba(0,0,0,0.12)"}`,
                  backdropFilter: "blur(12px)",
                  boxShadow: isDarkBg ? "0 2px 12px rgba(0,0,0,0.3)" : "0 2px 12px rgba(0,0,0,0.08)",
                }}>
                  <Building2 size={16} color={isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.6)"} strokeWidth={2.2} />
                  <Typography sx={{
                    fontSize: "0.75rem",
                    fontWeight: 600,
                    color: isDarkBg ? "rgba(255,255,255,0.8)" : "rgba(0,0,0,0.7)",
                    letterSpacing: "0.02em",
                  }}>
                    Internal
                  </Typography>
                </Box>
              </Box>
            </ThemeProvider>
          </Box>
        </Box>
      </Box>

      <Box sx={{ display: "flex", flexDirection: "column", gap: 3.5 }}>

        {/* ── Branding ── */}
        <Box>
          <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--dm-muted, rgba(0,0,0,0.35))", mb: 1.5 }}>
            Branding
          </Typography>
          <Box sx={{ display: "flex", gap: 3, mb: 2.5 }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography sx={{ fontSize: "0.82rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.75 }}>
                Application Title
              </Typography>
              <TextField
                value={uiSettings.appTitle}
                onChange={(e) => setUiSettings({ ...uiSettings, appTitle: e.target.value })}
                placeholder="Enter application title..."
                variant="outlined"
                size="small"
                fullWidth
                helperText="Browser tab and page title"
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography sx={{ fontSize: "0.82rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.75 }}>
                Application Logo
              </Typography>
              <Box sx={{ display: "flex", gap: 1.5, alignItems: "flex-start" }}>
                <TextField
                  value={uiSettings.appLogo || ""}
                  onChange={(e) => {
                    setUiSettings({ ...uiSettings, appLogo: e.target.value });
                    setLogoError(false);
                  }}
                  placeholder="Enter logo URL..."
                  variant="outlined"
                  size="small"
                  fullWidth
                  helperText="URL to your logo image"
                />
                <Box
                  sx={{
                    width: 40,
                    height: 40,
                    backgroundColor: isDarkBg ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.04)",
                    borderRadius: "10px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    overflow: "hidden",
                    flexShrink: 0,
                    border: `1px solid ${isDarkBg ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)"}`,
                    padding: "4px",
                  }}
                >
                  {!logoError && (
                    <img
                      src={uiSettings.appLogo || "/oracle-logo-building.svg"}
                      alt="Logo preview"
                      style={{
                        maxWidth: "100%",
                        maxHeight: "100%",
                        objectFit: "contain",
                        ...(isDarkBg && !uiSettings.appLogo && { filter: "brightness(0) invert(1)", opacity: 0.7 }),
                      }}
                      onError={(e) => {
                        if (uiSettings.appLogo) setLogoError(true);
                      }}
                    />
                  )}
                  {logoError && (
                    <Typography variant="caption" sx={{ color: "var(--dm-muted, rgba(0,0,0,0.4))", fontSize: "0.55rem" }}>!</Typography>
                  )}
                </Box>
              </Box>
            </Box>
          </Box>

          {/* Accent Color + Dark Mode — inline row */}
          <Box sx={{ display: "flex", alignItems: "flex-end", gap: 3 }}>
            <Box>
              <Typography sx={{ fontSize: "0.82rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.75 }}>
                Accent Color
              </Typography>
              <style>{`
                .rounded-color-picker::-webkit-color-swatch-wrapper { padding: 0; }
                .rounded-color-picker::-webkit-color-swatch { border: none; border-radius: 8px; }
                .rounded-color-picker::-moz-color-swatch { border: none; border-radius: 8px; }
              `}</style>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <input
                  type="color"
                  className="rounded-color-picker"
                  value={uiSettings.accentColor || "#C74634"}
                  onChange={(e) => setUiSettings({ ...uiSettings, accentColor: e.target.value })}
                  style={{ width: 36, height: 32, border: `1px solid ${isDarkBg ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.12)"}`, borderRadius: 10, cursor: "pointer", padding: 2 }}
                />
                <TextField
                  value={uiSettings.accentColor || "#C74634"}
                  onChange={(e) => setUiSettings({ ...uiSettings, accentColor: e.target.value })}
                  variant="outlined"
                  size="small"
                  sx={{ width: 120 }}
                />
              </Box>
            </Box>

            {/* Dark mode button */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, pb: 0.5 }}>
              <IconButton
                onClick={() => setUiSettings({ ...uiSettings, darkMode: !uiSettings.darkMode })}
                sx={{
                  width: 36,
                  height: 36,
                  borderRadius: "10px",
                  border: `1px solid ${isDarkBg ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.10)"}`,
                  backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.03)",
                  transition: "all 0.25s ease",
                  "&:hover": {
                    backgroundColor: isDarkBg ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.07)",
                  },
                }}
              >
                {uiSettings.darkMode ? (
                  <Sun size={16} color="var(--dm-text, #e5e5e5)" />
                ) : (
                  <Moon size={16} color="rgba(0,0,0,0.55)" />
                )}
              </IconButton>
              <Typography sx={{ fontSize: "0.8rem", color: "var(--dm-muted, rgba(0,0,0,0.45))", fontWeight: 400 }}>
                {uiSettings.darkMode ? "Light mode" : "Dark mode"}
              </Typography>
            </Box>
          </Box>
        </Box>

        {/* Subtle divider */}
        <Box sx={{ borderTop: `1px solid ${isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"}` }} />

        {/* ── Content ── */}
        <Box>
          <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--dm-muted, rgba(0,0,0,0.35))", mb: 1.5 }}>
            Content
          </Typography>
          <Box sx={{ display: "flex", gap: 3 }}>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography sx={{ fontSize: "0.82rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.75 }}>
                Welcome Message
              </Typography>
              <TextField
                value={uiSettings.welcomeMessage}
                onChange={(e) => setUiSettings({ ...uiSettings, welcomeMessage: e.target.value })}
                placeholder="Enter welcome message..."
                variant="outlined"
                size="small"
                fullWidth
                helperText="Shown when users first load the chat"
              />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography sx={{ fontSize: "0.82rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.75 }}>
                Input Placeholder
              </Typography>
              <TextField
                value={uiSettings.inputPlaceholder}
                onChange={(e) => setUiSettings({ ...uiSettings, inputPlaceholder: e.target.value })}
                placeholder="Enter input placeholder text..."
                variant="outlined"
                size="small"
                fullWidth
                helperText="Shown in the empty chat input field"
              />
            </Box>
          </Box>
        </Box>

        {/* Subtle divider */}
        <Box sx={{ borderTop: `1px solid ${isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.06)"}` }} />

        {/* ── Header Elements ── */}
        <Box>
          <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--dm-muted, rgba(0,0,0,0.35))", mb: 1.5 }}>
            Header Elements
          </Typography>
          <Box sx={{ display: "flex", gap: 3 }}>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <IOSSwitch
                checked={uiSettings.showLabChip !== false}
                onChange={(e) => setUiSettings({ ...uiSettings, showLabChip: e.target.checked })}
                sx={{ transform: "scale(0.8)" }}
              />
              <Chip
                label="BLACK BELTS LAB"
                size="small"
                variant="outlined"
                sx={{
                  fontSize: "0.55rem",
                  height: 18,
                  borderRadius: "4px",
                  borderColor: isDarkBg ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.2)",
                  color: isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.5)",
                  fontWeight: 500,
                  letterSpacing: "0.1em",
                }}
              />
              <Typography sx={{ fontSize: "0.82rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>chip</Typography>
            </Box>
            <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <IOSSwitch
                checked={uiSettings.showLabIcon !== false}
                onChange={(e) => setUiSettings({ ...uiSettings, showLabIcon: e.target.checked })}
                sx={{ transform: "scale(0.8)" }}
              />
              <Image src="/entypo--lab-flask.svg" alt="" width={16} height={16} style={{ opacity: 0.7, ...(isDarkBg && { filter: "brightness(0) invert(1)" }) }} />
              <Typography sx={{ fontSize: "0.82rem", color: "var(--dm-muted, rgba(0,0,0,0.5))" }}>icon next to title</Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}