"use client";

import { Box, TextField, Typography, Select, MenuItem, FormControl, InputLabel, Tooltip } from "@mui/material";
import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { Zap, Database, Sparkles, RefreshCw, Info } from "lucide-react";
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

const SettingRow = ({ icon: Icon, iconColor, title, description, children }) => (
  <Box sx={{
    display: "flex",
    alignItems: "flex-start",
    gap: 2,
    py: 2,
    borderBottom: "1px solid rgba(0, 0, 0, 0.06)",
    "&:last-child": { borderBottom: "none" },
  }}>
    <Box sx={{
      mt: 0.25,
      p: 0.75,
      borderRadius: 1,
      backgroundColor: `${iconColor}10`,
      display: "flex",
      flexShrink: 0,
    }}>
      <Icon size={18} color={iconColor} />
    </Box>
    <Box sx={{ flex: 1, minWidth: 0 }}>
      <Typography sx={{ fontSize: "0.9rem", fontWeight: 500, color: "var(--dm-text, #1a1a1a)", mb: 0.25 }}>
        {title}
      </Typography>
      <Typography sx={{ fontSize: "0.78rem", color: "rgba(0, 0, 0, 0.5)", lineHeight: 1.4, mb: children ? 1.5 : 0 }}>
        {description}
      </Typography>
      {children}
    </Box>
  </Box>
);

export default function AITab() {
  const [settings, setSettings] = useState(DEFAULT_AI_SETTINGS);
  const [isHydrated, setIsHydrated] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("aiSettings");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Fix invalid access policy values from older versions
        if (!["recall_and_store", "recall_only", "store_only"].includes(parsed.ltmAccessPolicy)) {
          parsed.ltmAccessPolicy = "recall_and_store";
        }
        setSettings({ ...DEFAULT_AI_SETTINGS, ...parsed });
      } catch (e) {
        console.error("Error parsing AI settings:", e);
      }
    }
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem("aiSettings", JSON.stringify(settings));
    }
  }, [settings, isHydrated]);

  const update = (key, value) => setSettings(prev => ({ ...prev, [key]: value }));

  // Auto-generate subject ID when LTM is enabled and no ID exists
  const handleLtmToggle = (enabled) => {
    update("ltmEnabled", enabled);
    if (enabled && !settings.ltmSubjectId) {
      update("ltmSubjectId", generateSubjectId());
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      {/* Memory Section */}
      <Typography variant="h6" sx={{ fontSize: "1.1rem", fontWeight: 400, color: "var(--dm-text, #1a1a1a)", mb: 1 }}>
        Memory
      </Typography>
      <Box sx={{
        border: "1px solid rgba(0, 0, 0, 0.08)",
        borderRadius: 2,
        px: 2.5,
        mb: 4,
        backgroundColor: "rgba(255, 255, 255, 0.5)",
      }}>
        <SettingRow
          icon={Database}
          iconColor="#3B82F6"
          title="Long-Term Memory"
          description="Use long-term memory so the AI remembers information across conversations — preferences, facts, and context from past chats. LTM must first be enabled in your OCI GenAI Project."
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: settings.ltmEnabled ? 1.5 : 0 }}>
            <IOSSwitch
              checked={settings.ltmEnabled}
              onChange={(e) => handleLtmToggle(e.target.checked)}
            />
          </Box>
          {settings.ltmEnabled && (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {/* Subject ID */}
              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.75 }}>
                  <Typography sx={{ fontSize: "0.78rem", fontWeight: 500, color: "rgba(0,0,0,0.7)" }}>
                    Memory ID
                  </Typography>
                  <Tooltip
                    title="This ID links memory across conversations. Same ID = shared memory. Change it to start fresh or separate users."
                    arrow
                    placement="top"
                  >
                    <Box sx={{ display: "inline-flex", cursor: "help" }}>
                      <Info size={13} color="rgba(0,0,0,0.3)" />
                    </Box>
                  </Tooltip>
                </Box>
                <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
                  <TextField
                    value={settings.ltmSubjectId}
                    onChange={(e) => update("ltmSubjectId", e.target.value)}
                    variant="outlined"
                    size="small"
                    fullWidth
                    sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.82rem", fontFamily: "monospace" } }}
                  />
                  <Tooltip title="Generate new ID (resets memory link)" arrow placement="top">
                    <Box
                      onClick={() => update("ltmSubjectId", generateSubjectId())}
                      sx={{
                        p: 0.75,
                        borderRadius: 1,
                        cursor: "pointer",
                        color: "rgba(0,0,0,0.35)",
                        "&:hover": { backgroundColor: "rgba(0,0,0,0.05)", color: "rgba(0,0,0,0.6)" },
                        display: "flex",
                        flexShrink: 0,
                      }}
                    >
                      <RefreshCw size={15} />
                    </Box>
                  </Tooltip>
                </Box>
                <Typography sx={{ fontSize: "0.7rem", color: "rgba(0,0,0,0.4)", mt: 0.5, lineHeight: 1.4 }}>
                  All conversations with this ID share the same memory. Changing it starts a separate memory space.
                </Typography>
              </Box>

              {/* Access Policy */}
              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, mb: 0.75 }}>
                  <Typography sx={{ fontSize: "0.78rem", fontWeight: 500, color: "rgba(0,0,0,0.7)" }}>
                    Access Policy
                  </Typography>
                </Box>
                <FormControl size="small" fullWidth>
                  <Select
                    value={settings.ltmAccessPolicy}
                    onChange={(e) => update("ltmAccessPolicy", e.target.value)}
                    sx={{ fontSize: "0.82rem" }}
                  >
                    {ACCESS_POLICY_OPTIONS.map(opt => (
                      <MenuItem key={opt.value} value={opt.value}>
                        {opt.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                <Typography sx={{ fontSize: "0.7rem", color: "rgba(0,0,0,0.4)", mt: 0.5, lineHeight: 1.4 }}>
                  {ACCESS_POLICY_OPTIONS.find(o => o.value === settings.ltmAccessPolicy)?.description}
                </Typography>
              </Box>
            </Box>
          )}
        </SettingRow>

        <SettingRow
          icon={Zap}
          iconColor="#F59E0B"
          title="Short-Term Memory Optimization"
          description="Use STMO to automatically condense chat history into compact summaries, preserving key information while reducing token usage in long conversations. STMO must first be enabled in your OCI GenAI Project."
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
            <IOSSwitch
              checked={settings.stmoEnabled}
              onChange={(e) => update("stmoEnabled", e.target.checked)}
            />
          </Box>
        </SettingRow>
      </Box>

      {/* Info note */}
      <Box sx={{
        display: "flex",
        gap: 1.5,
        p: 2,
        borderRadius: 1.5,
        backgroundColor: "rgba(59, 130, 246, 0.04)",
        border: "1px solid rgba(59, 130, 246, 0.1)",
      }}>
        <Sparkles size={16} color="#3B82F6" style={{ flexShrink: 0, marginTop: 2 }} />
        <Typography sx={{ fontSize: "0.78rem", color: "rgba(0, 0, 0, 0.55)", lineHeight: 1.5 }}>
          LTM and STMO require enabling the corresponding features in your OCI GenAI Project settings (Console → Analytics & AI → Generative AI → Projects).
        </Typography>
      </Box>
    </motion.div>
  );
}
