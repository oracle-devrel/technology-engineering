"use client";

import { Box, FormControlLabel, Tab, Tabs, TextField, Typography } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import IOSSwitch from "../ui/IOSSwitch";
import { useState, useEffect } from "react";
import { WIDGET_INLINE_PROMPT } from "../../utils/widgetInlinePrompt";
import { WIDGET_LAYOUT_PROMPT } from "../../utils/widgetLayoutPrompt";
import { CONCISE_SYSTEM_PROMPT } from "../../utils/concisePrompt";
import { BASE_SYSTEM_PROMPT } from "../../utils/baseSystemPrompt";
import { FileText, Pencil, Puzzle, Zap } from "lucide-react";
import WidgetCarousel from "../widgets/WidgetCarousel";

const mdComponents = {
  h1: ({ children }) => <Typography variant="subtitle1" sx={{ fontWeight: 600, mt: 1.5, mb: 0.5, fontSize: "0.85rem", fontFamily: "inherit" }}>{children}</Typography>,
  h2: ({ children }) => <Typography variant="subtitle2" sx={{ fontWeight: 600, mt: 1.5, mb: 0.5, fontSize: "0.8rem", color: "var(--dm-text, rgba(0,0,0,0.75))", fontFamily: "inherit" }}>{children}</Typography>,
  h3: ({ children }) => <Typography variant="subtitle2" sx={{ fontWeight: 500, mt: 1, mb: 0.25, fontSize: "0.78rem", color: "var(--dm-text, rgba(0,0,0,0.7))", fontFamily: "inherit" }}>{children}</Typography>,
  p: ({ children }) => <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-text, rgba(0,0,0,0.6))", lineHeight: 1.6, mb: 0.5, fontFamily: "inherit" }}>{children}</Typography>,
  ul: ({ children }) => <Box component="ul" sx={{ pl: 2, my: 0.25, "& li": { fontSize: "0.75rem", color: "var(--dm-text, rgba(0,0,0,0.6))", lineHeight: 1.6, mb: 0.15, fontFamily: "inherit" } }}>{children}</Box>,
  ol: ({ children }) => <Box component="ol" sx={{ pl: 2, my: 0.25, "& li": { fontSize: "0.75rem", color: "var(--dm-text, rgba(0,0,0,0.6))", lineHeight: 1.6, mb: 0.15, fontFamily: "inherit" } }}>{children}</Box>,
  strong: ({ children }) => <Box component="span" sx={{ fontWeight: 600, color: "var(--dm-text, rgba(0,0,0,0.75))" }}>{children}</Box>,
  code: ({ children }) => <Box component="code" sx={{ fontSize: "0.72rem", backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.05))", px: 0.5, py: 0.15, borderRadius: 0.5, fontFamily: "inherit" }}>{children}</Box>,
};

const STORAGE_KEYS = {
  SYSTEM_PROMPT: 'systemPrompt',
  WIDGETS_ENABLED: 'widgetsEnabled',
  CONCISE_ENABLED: 'conciseEnabled',
};

const PREVIEW_TABS = [
  { value: 'v1', label: 'Components' },
  { value: 'v2', label: 'Layouts' },
];

const DEFAULT_SYSTEM_PROMPT = 'You are a helpful AI assistant.';

const PROMPT_TABS = [
  { label: "Instructions", icon: <Pencil size={15} /> },
  { label: "System", icon: <FileText size={15} /> },
  { label: "Widgets", icon: <Puzzle size={15} /> },
  { label: "Concise", icon: <Zap size={15} /> },
];

export default function PromptsTab() {
  const [systemPrompt, setSystemPrompt] = useState(DEFAULT_SYSTEM_PROMPT);
  const [widgetsEnabled, setWidgetsEnabled] = useState(false);
  const [conciseEnabled, setConciseEnabled] = useState(false);
  const [previewTab, setPreviewTab] = useState('v1');
  const [isHydrated, setIsHydrated] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // Load from localStorage after mount (client-only)
  useEffect(() => {
    const storedSystemPrompt = localStorage.getItem(STORAGE_KEYS.SYSTEM_PROMPT);
    if (storedSystemPrompt) {
      setSystemPrompt(storedSystemPrompt);
    }

    const storedWidgetsEnabled = localStorage.getItem(STORAGE_KEYS.WIDGETS_ENABLED);
    if (storedWidgetsEnabled === 'true') {
      setWidgetsEnabled(true);
    }

    const storedConciseEnabled = localStorage.getItem(STORAGE_KEYS.CONCISE_ENABLED);
    if (storedConciseEnabled === 'true') {
      setConciseEnabled(true);
    }

    setIsHydrated(true);
  }, []);

  // Save system prompt to localStorage whenever it changes (after hydration)
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem(STORAGE_KEYS.SYSTEM_PROMPT, systemPrompt);
    }
  }, [systemPrompt, isHydrated]);

  // Save widgets enabled to localStorage whenever it changes (after hydration)
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem(STORAGE_KEYS.WIDGETS_ENABLED, widgetsEnabled.toString());
    }
  }, [widgetsEnabled, isHydrated]);

  // Save concise enabled to localStorage whenever it changes (after hydration)
  useEffect(() => {
    if (isHydrated) {
      localStorage.setItem(STORAGE_KEYS.CONCISE_ENABLED, conciseEnabled.toString());
    }
  }, [conciseEnabled, isHydrated]);


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
          mb: 2.5
        }}
      >
        Prompts
      </Typography>

      {/* Tabs — contained pill style */}
      <Box sx={{
        display: "flex",
        justifyContent: "flex-start",
        mb: 3,
      }}>
        <Box sx={{
          display: "flex",
          gap: 0.5,
          p: 0.5,
          borderRadius: 2.5,
          backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.04))",
          border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
        }}>
          {PROMPT_TABS.map((tab, i) => (
            <Box
              key={i}
              onClick={() => setActiveTab(i)}
              sx={{
                display: "flex",
                alignItems: "center",
                gap: 0.75,
                px: 3,
                py: 1,
                borderRadius: 2,
                cursor: "pointer",
                transition: "all 0.2s ease",
                backgroundColor: activeTab === i ? "var(--dm-surface, #fff)" : "transparent",
                boxShadow: activeTab === i ? "0 1px 3px rgba(0,0,0,0.1)" : "none",
                color: activeTab === i ? "var(--dm-text, #1a1a1a)" : "var(--dm-muted, rgba(0,0,0,0.45))",
                fontWeight: activeTab === i ? 600 : 450,
                "&:hover": {
                  color: activeTab === i ? "var(--dm-text, #1a1a1a)" : "var(--dm-text, rgba(0,0,0,0.65))",
                },
              }}
            >
              {tab.icon}
              <Typography sx={{
                fontSize: "0.88rem",
                fontWeight: "inherit",
                color: "inherit",
              }}>
                {tab.label}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Tab content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >
          {/* Instructions tab */}
          {activeTab === 0 && (
            <Box>
              <Typography variant="caption" sx={{ display: "block", color: "var(--dm-muted, rgba(0,0,0,0.55))", mb: 1.5 }}>
                Custom instructions added after the base prompt to customize the AI's behavior.
              </Typography>
              <TextField
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Add custom instructions for the AI..."
                variant="outlined"
                size="small"
                fullWidth
                multiline
                rows={16}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    fontSize: "0.85rem",
                  },
                }}
              />
            </Box>
          )}

          {/* System tab */}
          {activeTab === 1 && (
            <Box>
              <Typography variant="caption" sx={{ display: "block", color: "var(--dm-muted, rgba(0,0,0,0.55))", mb: 1.5 }}>
                This is always sent to the AI automatically. Cannot be modified.
              </Typography>
              <Box sx={{
                p: 2,
                backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                borderRadius: 1.5,
                border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                maxHeight: 400,
                overflow: "auto",
                fontFamily: "monospace",
              }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                  {BASE_SYSTEM_PROMPT}
                </ReactMarkdown>
              </Box>
            </Box>
          )}

          {/* Widgets tab */}
          {activeTab === 2 && (
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Box>
                  <Typography variant="caption" sx={{ display: "block", color: "var(--dm-muted, rgba(0,0,0,0.55))" }}>
                    When enabled, the AI can embed interactive widgets (cards, stats, charts, forms, etc.) in responses.
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <IOSSwitch
                      checked={widgetsEnabled}
                      onChange={(e) => setWidgetsEnabled(e.target.checked)}
                      sx={{ ml: 1 }}
                    />
                  }
                  label=""
                  sx={{ mr: 0, ml: 2, flexShrink: 0 }}
                />
              </Box>
              <Box sx={{
                opacity: widgetsEnabled ? 1 : 0.35,
                pointerEvents: widgetsEnabled ? "auto" : "none",
                transition: "opacity 0.25s ease",
              }}>
                  <Box sx={{
                    mb: 2,
                    borderRadius: 1.5,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                    backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                    overflow: "hidden",
                  }}>
                    {/* Preview tabs: Components / Layouts */}
                    <Tabs
                      value={previewTab}
                      onChange={(_, v) => setPreviewTab(v)}
                      centered
                      sx={{
                        minHeight: 36,
                        borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                        "& .MuiTabs-indicator": {
                          backgroundColor: "var(--dm-text, #1a1a1a)",
                          height: 2,
                          borderRadius: 1,
                        },
                        "& .MuiTab-root": {
                          minHeight: 36,
                          textTransform: "none",
                          fontSize: "0.82rem",
                          fontWeight: 450,
                          color: "var(--dm-muted, rgba(0,0,0,0.45))",
                          padding: "6px 14px",
                          minWidth: "auto",
                          "&.Mui-selected": {
                            color: "var(--dm-text, #1a1a1a)",
                            fontWeight: 550,
                          },
                        },
                      }}
                    >
                      {PREVIEW_TABS.map((tab) => (
                        <Tab key={tab.value} value={tab.value} label={tab.label} />
                      ))}
                    </Tabs>
                    <Box sx={{
                      py: 2,
                      height: 450,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}>
                      <WidgetCarousel showDots={false} version={previewTab} />
                    </Box>
                  </Box>

                  {/* Prompt reference */}
                  <Box sx={{
                    p: 2,
                    mb: 2,
                    backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                    borderRadius: 1.5,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                    maxHeight: 400,
                    overflow: "auto",
                    fontFamily: "monospace",
                  }}>
                    <Typography variant="caption" sx={{ display: "block", fontWeight: 500, mb: 1, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: 0.5 }}>
                      Widgets prompt — single widgets (auto-appended)
                    </Typography>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                      {WIDGET_INLINE_PROMPT}
                    </ReactMarkdown>
                  </Box>
                  <Box sx={{
                    p: 2,
                    backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                    borderRadius: 1.5,
                    border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                    maxHeight: 400,
                    overflow: "auto",
                    fontFamily: "monospace",
                  }}>
                    <Typography variant="caption" sx={{ display: "block", fontWeight: 500, mb: 1, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: 0.5 }}>
                      Layouts prompt — composable layouts (auto-appended)
                    </Typography>
                    <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                      {WIDGET_LAYOUT_PROMPT}
                    </ReactMarkdown>
                  </Box>
              </Box>
            </Box>
          )}

          {/* Concise Mode tab */}
          {activeTab === 3 && (
            <Box>
              <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 2 }}>
                <Box>
                  <Typography variant="caption" sx={{ display: "block", color: "var(--dm-muted, rgba(0,0,0,0.55))" }}>
                    Strips filler, articles, and pleasantries while keeping full technical accuracy. Reduces token usage significantly.
                  </Typography>
                </Box>
                <FormControlLabel
                  control={
                    <IOSSwitch
                      checked={conciseEnabled}
                      onChange={(e) => setConciseEnabled(e.target.checked)}
                      sx={{ ml: 1 }}
                    />
                  }
                  label=""
                  sx={{ mr: 0, ml: 2, flexShrink: 0 }}
                />
              </Box>
              <Box sx={{
                opacity: conciseEnabled ? 1 : 0.35,
                pointerEvents: conciseEnabled ? "auto" : "none",
                transition: "opacity 0.25s ease",
              }}>
                {/* Token savings metrics */}
                <Box sx={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr",
                  gap: 1,
                  mb: 2,
                }}>
                  {[
                    { label: "System prompts", reduction: "58%", example: "171 \u2192 72 tokens" },
                    { label: "API docs", reduction: "42%", example: "137 \u2192 79 tokens" },
                    { label: "General text", reduction: "~25%", example: "avg across content" },
                  ].map((metric) => (
                    <Box
                      key={metric.label}
                      sx={{
                        p: 1.25,
                        borderRadius: 1.5,
                        border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                        backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                        textAlign: "center",
                      }}
                    >
                      <Typography sx={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--dm-text, rgba(0,0,0,0.75))", lineHeight: 1.2 }}>
                        {metric.reduction}
                      </Typography>
                      <Typography sx={{ fontSize: "0.68rem", fontWeight: 550, color: "var(--dm-muted, rgba(0,0,0,0.55))", mt: 0.25 }}>
                        {metric.label}
                      </Typography>
                      <Typography sx={{ fontSize: "0.62rem", color: "var(--dm-muted, rgba(0,0,0,0.35))", mt: 0.15 }}>
                        {metric.example}
                      </Typography>
                    </Box>
                  ))}
                </Box>

                {/* Before/After example — two columns */}
                <Box sx={{
                  mb: 2,
                  borderRadius: 1.5,
                  border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                  overflow: "hidden",
                }}>
                  <Box sx={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
                    {/* Before */}
                    <Box sx={{ p: 1.5, borderRight: "1px solid var(--dm-border, rgba(0,0,0,0.06))" }}>
                      <Typography sx={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: 0.5, mb: 0.75 }}>
                        Before — 69 tokens
                      </Typography>
                      <Typography sx={{ fontSize: "0.73rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", lineHeight: 1.55, fontStyle: "italic" }}>
                        "The reason your React component is re-rendering is likely because you're creating a new object reference on each render cycle. When you pass an inline object as a prop, React's shallow comparison sees it as a different object every time, which triggers a re-render. I'd recommend using useMemo to memoize the object."
                      </Typography>
                    </Box>
                    {/* After */}
                    <Box sx={{ p: 1.5 }}>
                      <Typography sx={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: 0.5, mb: 0.75 }}>
                        After — 19 tokens (72% less)
                      </Typography>
                      <Typography sx={{ fontSize: "0.73rem", color: "var(--dm-text, rgba(0,0,0,0.8))", lineHeight: 1.55, fontWeight: 500 }}>
                        "New object ref each render. Inline object prop = new ref = re-render. Wrap in <Box component="code" sx={{ fontSize: "0.7rem", backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.06))", px: 0.4, py: 0.1, borderRadius: 0.5 }}>useMemo</Box>."
                      </Typography>
                    </Box>
                  </Box>
                </Box>

                {/* Prompt reference */}
                <Box sx={{
                  p: 2,
                  backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.02))",
                  borderRadius: 1.5,
                  border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                  maxHeight: 400,
                  overflow: "auto",
                  fontFamily: "monospace",
                }}>
                  <Typography variant="caption" sx={{ display: "block", fontWeight: 500, mb: 1, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: 0.5 }}>
                    Concise mode prompt (auto-appended)
                  </Typography>
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={mdComponents}>
                    {CONCISE_SYSTEM_PROMPT}
                  </ReactMarkdown>
                </Box>
              </Box>
            </Box>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
}
