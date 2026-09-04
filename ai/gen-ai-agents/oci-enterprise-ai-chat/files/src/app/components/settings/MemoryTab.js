"use client";

import { Box, FormControl, Select, MenuItem as MuiMenuItem, TextField, Tooltip, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { Database, Info, RefreshCw, Zap } from "lucide-react";
import { useState, useEffect } from "react";
import IOSSwitch from "../ui/IOSSwitch";

function generateSubjectId() {
  return "user_" + crypto.randomUUID().replace(/-/g, "").slice(0, 12);
}

const DEFAULT_AI_SETTINGS = {
  ltmEnabled: false,
  ltmSubjectId: "",
  ltmAccessPolicy: "recall_and_store",
  stmoEnabled: false,
};

const ACCESS_POLICY_OPTIONS = [
  {
    value: "recall_and_store",
    label: "Recall & Store",
    description: "The AI remembers past info and saves new info from this conversation.",
  },
  {
    value: "recall_only",
    label: "Recall Only",
    description: "The AI remembers past info but won't save anything new from this conversation.",
  },
  {
    value: "store_only",
    label: "Store Only",
    description: "The AI saves new info from this conversation but can't recall past memories.",
  },
];

export default function MemoryTab() {
  const [aiSettings, setAiSettings] = useState(DEFAULT_AI_SETTINGS);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    try {
      const stored = localStorage.getItem("aiSettings");
      if (stored) {
        const parsed = JSON.parse(stored);
        if (!["recall_and_store", "recall_only", "store_only"].includes(parsed.ltmAccessPolicy)) {
          parsed.ltmAccessPolicy = "recall_and_store";
        }
        setAiSettings({ ...DEFAULT_AI_SETTINGS, ...parsed });
      }
    } catch {}
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem("aiSettings", JSON.stringify(aiSettings));
    }
  }, [aiSettings, isHydrated]);

  const updateAiSetting = (key, value) => setAiSettings(prev => ({ ...prev, [key]: value }));

  const handleLtmToggle = (enabled) => {
    updateAiSetting("ltmEnabled", enabled);
    if (enabled && !aiSettings.ltmSubjectId) {
      updateAiSetting("ltmSubjectId", generateSubjectId());
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Typography
        variant="h5"
        sx={{
          fontSize: "1.1rem",
          fontWeight: 400,
          color: "var(--dm-text, #1a1a1a)",
          mb: 3
        }}
      >
        Memory
      </Typography>

      <Box sx={{ display: "flex", gap: 2, alignItems: "flex-start" }}>
      {/* Long-Term Memory Card */}
      <Box sx={{
        flex: 1,
        border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
        borderRadius: 1.5,
        px: 2.5,
        py: 2,
        backgroundColor: "var(--dm-surface)",
      }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box sx={{
              p: 0.75,
              borderRadius: 1,
              backgroundColor: "rgba(59, 130, 246, 0.1)",
              display: "flex",
              flexShrink: 0,
            }}>
              <Database size={18} color="#3B82F6" />
            </Box>
            <Typography sx={{ fontSize: "0.9rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)" }}>
              Long-Term Memory
            </Typography>
          </Box>
          <IOSSwitch
            checked={aiSettings.ltmEnabled}
            onChange={(e) => handleLtmToggle(e.target.checked)}
          />
        </Box>
        <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", lineHeight: 1.4, mb: aiSettings.ltmEnabled ? 2 : 0 }}>
          The AI remembers preferences, facts, and context across conversations. Must be enabled in your OCI GenAI Project.
        </Typography>
        {aiSettings.ltmEnabled && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {/* Memory ID */}
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.75 }}>
                <Typography sx={{ fontSize: "0.78rem", fontWeight: 500, color: "var(--dm-text, rgba(0,0,0,0.7))" }}>
                  Memory ID
                </Typography>
                <Tooltip
                  title="This ID links memory across conversations. Same ID = shared memory. Change it to start fresh or separate users."
                  arrow
                  placement="top"
                >
                  <Box sx={{ display: "inline-flex", cursor: "help" }}>
                    <Info size={13} color="var(--dm-muted, rgba(0,0,0,0.3))" />
                  </Box>
                </Tooltip>
              </Box>
              <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                <TextField
                  value={aiSettings.ltmSubjectId}
                  onChange={(e) => updateAiSetting("ltmSubjectId", e.target.value)}
                  variant="outlined"
                  size="small"
                  fullWidth
                  sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.82rem", fontFamily: "monospace" } }}
                />
                <Tooltip title="Generate new ID (resets memory link)" arrow placement="top">
                  <Box
                    onClick={() => updateAiSetting("ltmSubjectId", generateSubjectId())}
                    sx={{
                      p: 0.75,
                      borderRadius: 1,
                      cursor: "pointer",
                      color: "var(--dm-muted, rgba(0,0,0,0.35))",
                      "&:hover": { backgroundColor: "rgba(0,0,0,0.05)", color: "var(--dm-text, rgba(0,0,0,0.6))" },
                      display: "flex",
                      flexShrink: 0,
                    }}
                  >
                    <RefreshCw size={15} />
                  </Box>
                </Tooltip>
              </Box>
              <Typography sx={{ fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", mt: 0.5, lineHeight: 1.4 }}>
                Same ID = shared memory. Change it to start fresh.
              </Typography>
            </Box>

            {/* Access Policy */}
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.75 }}>
                <Typography sx={{ fontSize: "0.78rem", fontWeight: 500, color: "var(--dm-text, rgba(0,0,0,0.7))" }}>
                  Access Policy
                </Typography>
              </Box>
              <FormControl size="small" fullWidth>
                <Select
                  value={aiSettings.ltmAccessPolicy}
                  onChange={(e) => updateAiSetting("ltmAccessPolicy", e.target.value)}
                  sx={{ fontSize: "0.82rem" }}
                >
                  {ACCESS_POLICY_OPTIONS.map(opt => (
                    <MuiMenuItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </MuiMenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography sx={{ fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", mt: 0.5, lineHeight: 1.4 }}>
                {ACCESS_POLICY_OPTIONS.find(o => o.value === aiSettings.ltmAccessPolicy)?.description}
              </Typography>
            </Box>
          </Box>
        )}
      </Box>

      {/* Short-Term Memory Optimization Card */}
      <Box sx={{
        flex: 1,
        border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
        borderRadius: 1.5,
        px: 2.5,
        py: 2,
        backgroundColor: "var(--dm-surface)",
      }}>
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Box sx={{
              p: 0.75,
              borderRadius: 1,
              backgroundColor: "rgba(245, 158, 11, 0.1)",
              display: "flex",
              flexShrink: 0,
            }}>
              <Zap size={18} color="#F59E0B" />
            </Box>
            <Typography sx={{ fontSize: "0.9rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)" }}>
              Short-Term Memory Optimization
            </Typography>
          </Box>
          <IOSSwitch
            checked={aiSettings.stmoEnabled}
            onChange={(e) => updateAiSetting("stmoEnabled", e.target.checked)}
          />
        </Box>
        <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", lineHeight: 1.4 }}>
          Automatically summarizes chat history to save tokens in long conversations. Must be enabled in your OCI GenAI Project.
        </Typography>
      </Box>
      </Box>

      <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", mt: 1.5, lineHeight: 1.4 }}>
        Both features must be enabled in your OCI GenAI Project (Console → Analytics & AI → Generative AI → Projects).
      </Typography>
    </motion.div>
  );
}
