"use client";

import { Box, Typography, Popover, Chip } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { Lock } from "lucide-react";
import { Icon } from "@iconify/react";

const PROVIDER_META = {
  openai: { label: "OpenAI", color: "#1a1a1a", bg: "#f5f5f5", icon: "simple-icons:openai" },
  xai: { label: "xAI", color: "#1a1a1a", bg: "#f5f5f5", icon: "simple-icons:x" },
  google: { label: "Google", color: "#1a1a1a", bg: "#f5f5f5", icon: "simple-icons:google" },
  cohere: { label: "Cohere", color: "#1a1a1a", bg: "#f5f5f5", icon: "simple-icons:cohere" },
  meta: { label: "Meta", color: "#1a1a1a", bg: "#f5f5f5", icon: "simple-icons:meta" },
};

const RECOMMENDED = "google.gemini-2.5-pro";

// Uniform color per level — visually distinct from each other
const LEVEL_COLORS = {
  family: "#6366f1",   // indigo for all Level 2 (family) bubbles
  version: "#ec4899",  // pink for all Level 3 (version) bubbles
};

const SELECTED_COLOR = "#C74634"; // Oracle red — used for selection state across all levels

// Internal use only = all OpenAI models EXCEPT gpt-oss
function isInternalOnly(model) {
  const name = model.replace(/^[a-z]+\./, "");
  return model.startsWith("openai.") && !name.startsWith("gpt-oss");
}

function formatModelName(model) {
  return model.replace(/^[a-z]+\./, "");
}

// Extract model family from a full model id (without provider prefix)
// Each point release is its own family:
//   "gpt-5-mini" → "gpt-5", "gpt-5.1-codex" → "gpt-5.1", "gpt-5.2-pro" → "gpt-5.2"
//   "gpt-4o-mini" → "gpt-4o", "gpt-4.1" → "gpt-4.1"
//   "grok-3-mini-fast" → "grok-3", "grok-4-1-fast-reasoning" → "grok-4-1"
//   "o1" → "o-series", "o3-mini" → "o-series", "o4-mini" → "o-series"
function getFamily(modelName) {
  // o-series: o1, o3-mini, o4-mini → "o-series"
  if (/^o\d/.test(modelName)) return "o-series";
  // gpt-oss special case
  if (modelName.startsWith("gpt-oss")) return "gpt-oss";
  // gpt-X.Y (e.g. gpt-5.1, gpt-5.2, gpt-4.1) → family "gpt-X.Y"
  const gptDotMatch = modelName.match(/^(gpt-\d+\.\d+)/);
  if (gptDotMatch) return gptDotMatch[1];
  // gpt-Xo (e.g. gpt-4o, gpt-4o-mini) → family "gpt-4o"
  const gptOMatch = modelName.match(/^(gpt-\d+o)/);
  if (gptOMatch) return gptOMatch[1];
  // gpt-X (e.g. gpt-5, gpt-5-mini) → family "gpt-X"
  const gptMatch = modelName.match(/^(gpt-\d+)/);
  if (gptMatch) return gptMatch[1];
  // grok-X-Y (e.g. grok-4-1-fast-reasoning) → family "grok-X-Y" where Y is a single digit
  const grokSubMatch = modelName.match(/^(grok-\d+-\d+)/);
  if (grokSubMatch) return grokSubMatch[1];
  // grok-X (e.g. grok-3, grok-4) → family "grok-X"
  const grokMatch = modelName.match(/^(grok-\d+)/);
  if (grokMatch) return grokMatch[1];
  // fallback
  return modelName;
}

function formatFamilyLabel(family) {
  if (family === "o-series") return "o-series";
  if (family === "gpt-oss") return "OSS";
  // gpt-5.1 → "GPT-5.1", gpt-4o → "GPT-4o", grok-4-1 → "Grok 4.1"
  if (family.startsWith("gpt-")) return "GPT-" + family.slice(4);
  if (family.startsWith("grok-")) {
    const ver = family.slice(5).replace("-", ".");
    return "Grok " + ver;
  }
  return family;
}

export default function BubbleModelSelector({
  models = [],
  selectedModel,
  onModelChange,
  anchorEl,
  open,
  onClose,
  accentColor = "#C74634",
}) {
  const [activeProvider, setActiveProvider] = useState(null);
  const [activeFamily, setActiveFamily] = useState(null);

  // Level 1: group by provider
  const providerGroups = {};
  models.forEach((model) => {
    const provider = model.split(".")[0];
    if (!providerGroups[provider]) providerGroups[provider] = [];
    providerGroups[provider].push(model);
  });

  // Level 2: within a provider, group by family
  const getFamilyGroups = (provider) => {
    const familyGroups = {};
    (providerGroups[provider] || []).forEach((model) => {
      const name = model.replace(/^[a-z]+\./, "");
      const family = getFamily(name);
      if (!familyGroups[family]) familyGroups[family] = [];
      familyGroups[family].push(model);
    });
    return familyGroups;
  };

  const providers = Object.keys(providerGroups);
  const selectedProvider = selectedModel?.split(".")[0];
  const selectedName = selectedModel?.replace(/^[a-z]+\./, "");
  const selectedFamily = selectedName ? getFamily(selectedName) : null;

  const handleProviderClick = (provider) => {
    if (activeProvider === provider) {
      setActiveProvider(null);
      setActiveFamily(null);
    } else {
      setActiveProvider(provider);
      setActiveFamily(null);
    }
  };

  const handleFamilyClick = (family, familyModels) => {
    // If only one model in family, select it directly
    if (familyModels.length === 1) {
      onModelChange(familyModels[0]);
      setActiveProvider(null);
      setActiveFamily(null);
      onClose();
      return;
    }
    setActiveFamily((prev) => (prev === family ? null : family));
  };

  const handleModelClick = (model) => {
    onModelChange(model);
    setActiveProvider(null);
    setActiveFamily(null);
    onClose();
  };

  const bubbleStyle = (isActive, isSelected, meta, size = "large") => {
    const large = size === "large";
    const sel = accentColor;
    // Priority: selected (red) > active (outline) > default (level color)
    const bw = large ? 2 : 1.5;
    let bg, fg, borderColor, shadow;
    if (isSelected) {
      bg = sel;
      fg = "white";
      borderColor = sel;
      shadow = `0 2px 8px ${sel}40`;
    } else if (isActive) {
      bg = "white";
      fg = meta.color;
      borderColor = meta.color;
      shadow = `0 4px 16px ${meta.color}25`;
    } else {
      bg = "rgba(255,255,255,0.95)";
      fg = large ? meta.color : "rgba(0,0,0,0.7)";
      borderColor = large ? "rgba(255,255,255,0.8)" : "rgba(0,0,0,0.1)";
      shadow = large ? "0 2px 8px rgba(0,0,0,0.1)" : "0 1px 4px rgba(0,0,0,0.08)";
    }
    return {
      display: "flex",
      alignItems: "center",
      gap: large ? 0.75 : 0.5,
      px: large ? 2.5 : 1.5,
      py: large ? 1.2 : 0.7,
      borderRadius: 10,
      cursor: "pointer",
      bgcolor: bg,
      color: fg,
      border: `${bw}px solid ${borderColor}`,
      boxShadow: shadow,
      transition: "all 0.2s ease",
      "&:hover": {
        bgcolor: isSelected ? sel : "white",
        border: `${bw}px solid ${sel}`,
        boxShadow: `0 4px 16px ${sel}30`,
        transform: "translateY(-1px)",
      },
      userSelect: "none",
    };
  };

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={() => {
        setActiveProvider(null);
        setActiveFamily(null);
        onClose();
      }}
      anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      transformOrigin={{ vertical: "top", horizontal: "center" }}
      marginThreshold={0}
      disableScrollLock
      slotProps={{
        paper: {
          sx: {
            mt: 1.5,
            borderRadius: 4,
            bgcolor: "transparent",
            boxShadow: "none",
            overflow: "visible",
          },
        },
      }}
    >
      <motion.div
        layout
        transition={{ type: "spring", stiffness: 500, damping: 42, mass: 0.8 }}
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          minWidth: 420,
          padding: 8,
        }}
      >
        {/* Level 1: Provider bubbles */}
        <Box sx={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 1.5 }}>
          {providers.map((provider, i) => {
            const meta = PROVIDER_META[provider] || { label: provider, color: "#666", bg: "#f5f5f5" };
            const isActive = activeProvider === provider;
            const isSelected = selectedProvider === provider;

            return (
              <motion.div
                key={provider}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: i * 0.05, duration: 0.2 }}
              >
                <Box onClick={() => handleProviderClick(provider)} sx={bubbleStyle(isActive, isSelected, meta, "large")}>
                  {meta.icon && <Icon icon={meta.icon} width={16} height={16} />}
                  <Typography sx={{ fontSize: "0.9rem", fontWeight: 700, whiteSpace: "nowrap" }}>
                    {meta.label}
                  </Typography>
                </Box>
              </motion.div>
            );
          })}
        </Box>

        {/* Level 2: Family bubbles */}
        <AnimatePresence mode="wait">
          {activeProvider && (
            <motion.div
              layout
              key={`families-${activeProvider}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              style={{ display: "flex", justifyContent: "center" }}
            >
              <Box sx={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 1 }}>
                {Object.entries(getFamilyGroups(activeProvider)).map(([family, familyModels], i) => {
                  const familyMeta = { color: LEVEL_COLORS.family };
                  const isActive = activeFamily === family;
                  const isSelected = selectedProvider === activeProvider && selectedFamily === family;

                  return (
                    <motion.div
                      key={family}
                      initial={{ opacity: 0, scale: 0.85 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.03, duration: 0.15 }}
                    >
                      <Box
                        onClick={() => handleFamilyClick(family, familyModels)}
                        sx={bubbleStyle(isActive, isSelected, familyMeta, "medium")}
                      >
                        <Typography sx={{ fontSize: "0.82rem", fontWeight: isActive || isSelected ? 700 : 500, whiteSpace: "nowrap" }}>
                          {formatFamilyLabel(family)}
                          {familyModels.length > 1 && (
                            <Box component="span" sx={{ ml: 0.5, fontSize: "0.7rem", opacity: 0.6 }}>
                              {familyModels.length}
                            </Box>
                          )}
                        </Typography>
                      </Box>
                    </motion.div>
                  );
                })}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Level 3: Version bubbles */}
        <AnimatePresence mode="wait">
          {activeFamily && activeProvider && (
            <motion.div
              layout
              key={`versions-${activeFamily}`}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.18, ease: "easeOut" }}
              style={{ display: "flex", justifyContent: "center" }}
            >
              <Box sx={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 1 }}>
                {(getFamilyGroups(activeProvider)[activeFamily] || []).map((model, i) => {
                  const isSelected = selectedModel === model;
                  const meta = { color: LEVEL_COLORS.version };

                  return (
                    <motion.div
                      key={model}
                      initial={{ opacity: 0, scale: 0.85 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: i * 0.03, duration: 0.15 }}
                    >
                      <Box
                        onClick={() => handleModelClick(model)}
                        sx={bubbleStyle(false, isSelected, meta, "small")}
                      >
                        <Typography sx={{ fontSize: "0.78rem", fontWeight: isSelected ? 600 : 400, whiteSpace: "nowrap" }}>
                          {formatModelName(model)}
                        </Typography>
                        {isInternalOnly(model) && (
                          <Box
                            component="span"
                            sx={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "3px",
                              ml: 0.3,
                              px: "5px",
                              py: "1px",
                              borderRadius: "8px",
                              bgcolor: isSelected ? "rgba(255,255,255,0.2)" : "rgba(245,158,11,0.12)",
                              color: isSelected ? "rgba(255,255,255,0.8)" : "#b45309",
                              fontFamily: "var(--font-exo2), sans-serif",
                              fontSize: "0.6rem",
                              fontWeight: 600,
                              lineHeight: 1.2,
                              whiteSpace: "nowrap",
                              letterSpacing: "0.01em",
                            }}
                          >
                            <Lock size={7} strokeWidth={2.5} />
                            internal
                          </Box>
                        )}
                        {model === RECOMMENDED && (
                          <Box
                            sx={{
                              width: 5,
                              height: 5,
                              borderRadius: "50%",
                              bgcolor: isSelected ? "rgba(255,255,255,0.6)" : "#1976d2",
                              flexShrink: 0,
                            }}
                          />
                        )}
                      </Box>
                    </motion.div>
                  );
                })}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </Popover>
  );
}
