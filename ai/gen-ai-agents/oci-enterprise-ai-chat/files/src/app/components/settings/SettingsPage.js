"use client";

import { ArrowLeft, Settings, Building2, Users } from "lucide-react";
import Header from "../ui/Header";
import { darkModeOverrides, darkCssVars, lightCssVars, DARK_BG } from "../../config/darkMode";
import { Box, IconButton, Typography, ThemeProvider, createTheme, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import VerticalTabs from "../ui/VerticalTabs";
import GeneralTab from "./GeneralTab";
import PromptsTab from "./PromptsTab";
import ToolsTab from "./ToolsTab";
import MemoryTab from "./MemoryTab";
import ObservabilityTab from "./ObservabilityTab";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { APP_VERSION } from "../../config/version";
import { INTERNAL_MODELS } from "../../config/models-internal";

const INTERNAL_MODE_AVAILABLE = INTERNAL_MODELS.length > 0;

const TAB_ROUTES = {
  0: '/settings/prompts',
  1: '/settings/tools',
  2: '/settings/memory',
  3: '/settings/observability',
  4: '/settings/appearance',
};

const ROUTE_TO_TAB = {
  'prompts': 0,
  'tools': 1,
  'memory': 2,
  'observability': 3,
  'appearance': 4,
};

export default function SettingsPage({ defaultTab = 'prompts' }) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState(ROUTE_TO_TAB[defaultTab] ?? 0);
  const [appMode, setAppMode] = useState("client");
  const [uiSettings, setUiSettings] = useState({});
  const parentTheme = useTheme();

  useEffect(() => {
    const saved = localStorage.getItem("appMode");
    if (saved === "client" || saved === "internal") setAppMode(saved);
    try {
      const stored = localStorage.getItem("uiSettings");
      if (stored) setUiSettings(JSON.parse(stored));
    } catch {}

    const handleUiSettingsChanged = (e) => setUiSettings(e.detail);
    window.addEventListener('uiSettingsChanged', handleUiSettingsChanged);
    return () => window.removeEventListener('uiSettingsChanged', handleUiSettingsChanged);
  }, []);

  const darkTheme = uiSettings.darkMode ? createTheme({
    ...parentTheme,
    palette: {
      ...parentTheme.palette,
      mode: "dark",
      background: { default: DARK_BG, paper: "#242424" },
      text: { primary: "#e5e5e5", secondary: "rgba(255,255,255,0.5)" },
      divider: "rgba(255,255,255,0.08)",
    },
  }) : parentTheme;

  const handleToggleAppMode = () => {
    const newMode = appMode === "internal" ? "client" : "internal";
    setAppMode(newMode);
    localStorage.setItem("appMode", newMode);
  };

  // Handle tab change with URL update (no navigation, just URL sync)
  const handleTabChange = (newTab) => {
    setActiveTab(newTab);
    const route = TAB_ROUTES[newTab];
    if (route) {
      window.history.replaceState(null, '', route);
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
    <Box
      sx={{
        height: "100vh",
        width: "100%",
        backgroundImage: uiSettings.darkMode ? "none" : "url('/backgrounds/white-red-background.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        backgroundColor: uiSettings.darkMode ? DARK_BG : undefined,
        ...(uiSettings.darkMode ? { ...darkCssVars, ...darkModeOverrides } : lightCssVars),
        pt: 0,
        px: { xs: 2, md: 4 },
        pb: 0,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      {/* Main Header */}
      <Header
        onNewConversation={() => router.push("/")}
        showLabChip={uiSettings.showLabChip !== false}
        showLabIcon={uiSettings.showLabIcon !== false}
        appTitle={uiSettings.appTitle}
        accentColor={uiSettings.accentColor}
        isDarkBg={uiSettings.darkMode === true}
        minimal
      />

      <Box sx={{ width: "100%", display: "flex", flexDirection: "column", flex: 1, minHeight: 0, pt: "68px" }}>
        {/* Settings sub-header */}
        <Box sx={{ display: "flex", alignItems: "center", mb: 2, flexShrink: 0 }}>
          <IconButton
            onClick={() => router.push("/")}
            sx={{
              mr: 2,
              color: uiSettings.darkMode ? "rgba(255,255,255,0.6)" : "rgba(0, 0, 0, 0.6)",
              "&:hover": {
                backgroundColor: "rgba(0, 0, 0, 0.04)",
              },
            }}
          >
            <ArrowLeft size={20} />
          </IconButton>
          <motion.div
            initial={{ rotate: 0 }}
            animate={{ rotate: 180 }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 0.2 }}
            style={{ display: "flex", alignItems: "center", marginRight: "12px" }}
          >
            <Settings size={24} style={{ color: uiSettings.darkMode ? "#e5e5e5" : "#1a1a1a" }} />
          </motion.div>
          <Typography
            variant="h4"
            sx={{
              fontSize: { xs: "1.5rem", sm: "2rem" },
              fontWeight: 300,
              color: uiSettings.darkMode ? "#e5e5e5" : "#1a1a1a",
              fontFamily: "var(--font-oracle-sans), sans-serif",
            }}
          >
            Settings
          </Typography>
        </Box>

        {/* Content with vertical tabs */}
        <VerticalTabs
          activeTab={activeTab}
          onTabChange={handleTabChange}
          tabs={["Prompts", "Tools", "Memory", "Observability", "Appearance"]}
          footer={
            <Typography sx={{
              fontSize: "0.7rem",
              fontWeight: 500,
              color: uiSettings.darkMode ? "rgba(255,255,255,0.4)" : "rgba(0, 0, 0, 0.4)",
              letterSpacing: "0.05em",
              fontFamily: "monospace",
              userSelect: "none",
            }}>
              v{APP_VERSION}
            </Typography>
          }
        >
          {activeTab === 0 && <PromptsTab />}
          {activeTab === 1 && <ToolsTab />}
          {activeTab === 2 && <MemoryTab />}
          {activeTab === 3 && <ObservabilityTab />}
          {activeTab === 4 && <GeneralTab />}
        </VerticalTabs>
      </Box>

      {/* App Mode FAB */}
      {INTERNAL_MODE_AVAILABLE && (
        <Box
          onClick={handleToggleAppMode}
          sx={{
            position: "fixed",
            bottom: 24,
            right: 24,
            display: "flex",
            alignItems: "center",
            gap: 1,
            px: 2,
            py: 1,
            borderRadius: 10,
            cursor: "pointer",
            zIndex: 1200,
            backgroundColor: uiSettings.darkMode ? "rgba(255,255,255,0.08)" : "rgba(255, 255, 255, 0.9)",
            border: `1px solid ${uiSettings.darkMode ? "rgba(255,255,255,0.10)" : "rgba(0, 0, 0, 0.12)"}`,
            backdropFilter: "blur(12px)",
            boxShadow: uiSettings.darkMode ? "0 2px 12px rgba(0,0,0,0.3)" : "0 2px 12px rgba(0,0,0,0.08)",
            transition: "all 0.3s ease",
            "&:hover": {
              transform: "translateY(-2px)",
              boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
            },
            "&:active": {
              transform: "translateY(0)",
            },
          }}
        >
          {appMode === "internal" ? (
            <Building2 size={16} color={uiSettings.darkMode ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.6)"} strokeWidth={2.2} />
          ) : (
            <Users size={16} color={uiSettings.darkMode ? "rgba(255,255,255,0.5)" : "rgba(0,0,0,0.6)"} strokeWidth={2.2} />
          )}
          <Typography sx={{
            fontSize: "0.75rem",
            fontWeight: 600,
            color: uiSettings.darkMode ? "rgba(255,255,255,0.8)" : "rgba(0, 0, 0, 0.7)",
            letterSpacing: "0.02em",
            userSelect: "none",
          }}>
            {appMode === "internal" ? "Internal" : "Client"}
          </Typography>
        </Box>
      )}
    </Box>
    </ThemeProvider>
  );
}