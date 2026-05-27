"use client";

import { memo, useMemo, useState, useEffect, useRef } from "react";
import { Close as CloseIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogContent,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { Check, Copy, ChevronDown as ChevronDownIcon, Code, FileText, X, Brain, Terminal, RotateCcw, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import JsonView from "@uiw/react-json-view";

import Sources from "../agent/Sources";
import DotMatrixLoader from "../ui/DotMatrixLoader";
import CostBenefitChart from "../charts/CostBenefitChart";
import ProcessDiagram from "../charts/ProcessDiagram";
import RadarChart from "../charts/RadarChart";
import ScatterChart from "../charts/ScatterChart";
import ProgressTracker from "../demo/ProgressTracker";
import SupplierCard from "../demo/SupplierCard";
import DustReveal from "../ui/DustReveal";
import DynamicChip from "../ui/DynamicChip";
import InteractiveChoice from "../ui/InteractiveChoice";
import TypingEffect from "../ui/TypingEffect";
import CitationCard from "../ui/CitationCard";
import { Widget, WidgetV2 } from "../widgets";
import { serializeWidgetV2Tree } from "../../utils/widgetV2Parser";
import { groupMessages } from "../../utils/messageUtils";
import { AlertTriangle, Mail, ChevronDown, KeyRound } from "lucide-react";

// Friendly names for OCI internal tools
const OCI_INTERNAL_LABELS = {
  oci_internal_search_memory: 'Memory',
};

// Format tool names: "text_to_speech" -> "Text to speech"
const formatToolName = (name) => {
  if (!name) return name;
  if (OCI_INTERNAL_LABELS[name]) return OCI_INTERNAL_LABELS[name];
  return name
    .replace(/_/g, ' ')
    .replace(/-/g, ' ')
    .replace(/\b\w/, c => c.toUpperCase());
};

// Copy to clipboard button with check feedback
function CopyTextButton({ content }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <IconButton size="small" onClick={handleCopy} title="Copy to clipboard">
      {copied ? <Check size={16} style={{ color: "#10B981" }} /> : <Copy size={16} />}
    </IconButton>
  );
}

// Bouncing dots animation for in-progress reasoning
function BouncingDots() {
  return (
    <Box component="span" sx={{ display: "inline-flex", gap: "2.5px", alignItems: "baseline", ml: 0.5 }}>
      {[0, 1, 2].map(i => (
        <motion.span
          key={i}
          animate={{ y: [0, -2, 0] }}
          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2, ease: "easeInOut" }}
          style={{
            display: "inline-block",
            width: 3.5,
            height: 3.5,
            borderRadius: "50%",
            backgroundColor: "var(--dm-muted, rgba(0, 0, 0, 0.35))",
          }}
        />
      ))}
    </Box>
  );
}

// Reasoning summary block — matches mcp_chip_row style with staged entrance.
function ReasoningBlock({ text, done }) {
  const [isOpen, setIsOpen] = useState(false);
  const isStreaming = !done;
  return (
    <Box sx={{ my: 1 }}>
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 20, stiffness: 400 }}
        style={{ display: "inline-block" }}
      >
        <Box
          onClick={() => setIsOpen(!isOpen)}
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: 1,
            px: 1.5,
            py: 0.75,
            borderRadius: "16px",
            backgroundColor: isOpen ? "var(--dm-subtle, rgba(0, 0, 0, 0.08))" : "var(--dm-subtle, rgba(0, 0, 0, 0.04))",
            border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.15))",
            fontFamily: "var(--font-oracle-sans), sans-serif",
            fontSize: "0.8rem",
            color: "var(--dm-muted, rgba(0, 0, 0, 0.6))",
            transition: "all 0.2s ease",
            cursor: "pointer",
            userSelect: "none",
            "&:hover": {
              backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.08))",
              transform: "scale(1.03)",
            },
          }}
        >
          <Brain size={14} />
          <span>Reasoning</span>
          {isStreaming ? (
            <BouncingDots />
          ) : (
            <ChevronDown
              size={14}
              style={{
                transition: "transform 0.2s ease",
                transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
              }}
            />
          )}
        </Box>
      </motion.div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -8 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.15 }}
            style={{ overflow: "hidden" }}
          >
            <Paper
              elevation={0}
              sx={{
                mt: 1,
                pt: 2,
                px: 2,
                pb: 2,
                backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.02))",
                border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
                borderRadius: "20px",
                fontFamily: "var(--font-oracle-sans), sans-serif",
                fontSize: "0.8rem",
                color: "var(--dm-muted, rgba(0, 0, 0, 0.55))",
                lineHeight: 1.6,
              }}
            >
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {text}
              </ReactMarkdown>
            </Paper>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}

// Code execution block — matches mcp_chip_row style with staged entrance.
// Supports streaming states: writing / interpreting / completed.
function CodeExecutionBlock({ code, output, status }) {
  const isActive = status === 'writing' || status === 'in_progress' || status === 'interpreting';
  const isDone = status === 'completed' || !!output;
  // Auto-expand while active so the user sees streaming code. Collapse when done.
  const [userOpened, setUserOpened] = useState(null); // null = follow auto, true/false = user override
  const autoOpen = isActive;
  const isOpen = userOpened == null ? autoOpen : userOpened;

  const label = status === 'writing' ? 'Writing code…'
    : status === 'interpreting' ? 'Executing…'
    : status === 'in_progress' ? 'Starting…'
    : 'Code executed';

  return (
    <Box sx={{ my: 1 }}>
      <motion.div
        initial={{ scale: 0.6, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", damping: 20, stiffness: 400 }}
        style={{ display: "inline-block" }}
      >
        <Box
          onClick={() => setUserOpened(!isOpen)}
          sx={{
            display: "inline-flex",
            alignItems: "center",
            gap: 1,
            px: 1.5,
            py: 0.75,
            borderRadius: "16px",
            backgroundColor: isOpen ? "var(--dm-subtle, rgba(0, 0, 0, 0.08))" : "var(--dm-subtle, rgba(0, 0, 0, 0.04))",
            border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.15))",
            fontFamily: "var(--font-oracle-sans), sans-serif",
            fontSize: "0.8rem",
            color: "var(--dm-muted, rgba(0, 0, 0, 0.6))",
            transition: "all 0.2s ease",
            cursor: "pointer",
            userSelect: "none",
            "&:hover": {
              backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.08))",
              transform: "scale(1.03)",
            },
          }}
        >
          <Terminal size={14} />
          <span>{label}</span>
          {isActive ? <BouncingDots /> : (
            <ChevronDown
              size={14}
              style={{
                transition: "transform 0.2s ease",
                transform: isOpen ? "rotate(180deg)" : "rotate(0deg)",
              }}
            />
          )}
        </Box>
      </motion.div>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -8 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -8 }}
            transition={{ duration: 0.3, ease: [0.25, 0.46, 0.45, 0.94], delay: 0.15 }}
            style={{ overflow: "hidden" }}
          >
            <Box sx={{ mt: 1, borderRadius: "20px", overflow: "hidden", border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))" }}>
              <Box sx={{ backgroundColor: "#1e1e1e", p: 1.5, overflowX: "auto" }}>
                <Typography component="pre" sx={{
                  fontFamily: "monospace",
                  fontSize: "0.75rem",
                  color: "#d4d4d4",
                  lineHeight: 1.5,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  m: 0,
                }}>
                  {code}
                </Typography>
              </Box>
              {output && (
                <Box sx={{
                  backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.03))",
                  p: 1.5,
                  borderTop: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
                }}>
                  <Typography sx={{ fontSize: "0.65rem", fontWeight: 600, color: "var(--dm-muted, rgba(0, 0, 0, 0.35))", textTransform: "uppercase", letterSpacing: "0.5px", mb: 0.5 }}>
                    Output
                  </Typography>
                  <Typography component="pre" sx={{
                    fontFamily: "monospace",
                    fontSize: "0.75rem",
                    color: "var(--dm-text, rgba(0, 0, 0, 0.7))",
                    lineHeight: 1.5,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    m: 0,
                  }}>
                    {output}
                  </Typography>
                </Box>
              )}
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Box>
  );
}

// Collapsible user message component
function CollapsibleUserMessage({ text, fontSize, isLatest }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  const isLongMessage = text.length > 150;

  const textStyles = {
    color: "inherit",
    fontSize: fontSize,
    fontWeight: "100",
    lineHeight: isLatest ? 2 : 1.6,
  };

  // Mark animation as complete after initial render
  useEffect(() => {
    if (isLatest && !hasAnimated) {
      const timer = setTimeout(() => setHasAnimated(true), 1000);
      return () => clearTimeout(timer);
    }
  }, [isLatest, hasAnimated]);

  if (!isLongMessage) {
    return isLatest ? (
      <DustReveal text={text} duration={8} delay={0} sx={textStyles} />
    ) : (
      <Typography sx={textStyles}>{text}</Typography>
    );
  }

  const clampStyles = {
    display: "-webkit-box",
    WebkitLineClamp: 2,
    WebkitBoxOrient: "vertical",
    overflow: "hidden",
  };

  return (
    <Box
      onClick={() => setIsExpanded(!isExpanded)}
      sx={{ cursor: "pointer" }}
    >
      {isLatest && !hasAnimated ? (
        <DustReveal
          text={text}
          duration={8}
          delay={0}
          sx={{ ...textStyles, ...(!isExpanded && clampStyles) }}
        />
      ) : (
        <Typography sx={{ ...textStyles, ...(!isExpanded && clampStyles) }}>
          {text}
        </Typography>
      )}
      <motion.div
        animate={{ rotate: isExpanded ? 180 : 0 }}
        transition={{ duration: 0.2 }}
        style={{ display: "inline-flex", alignItems: "center", marginTop: "4px" }}
      >
        <ChevronDownIcon
          size={16}
          style={{ color: "rgba(0, 0, 0, 0.5)" }}
        />
      </motion.div>
    </Box>
  );
}

const TYPING_SPEED = 8;

// Component to render mailto links as buttons
function MailtoButton({ href, children }) {
  const handleClick = () => {
    window.location.href = href;
  };

  return (
    <button
      onClick={handleClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding: "8px 16px",
        backgroundColor: "#C74634",
        color: "white",
        border: "none",
        borderRadius: "6px",
        fontSize: "0.9rem",
        fontWeight: 500,
        cursor: "pointer",
        marginTop: "8px",
        marginBottom: "8px",
      }}
    >
      <Mail size={16} />
      {children || "Open email"}
    </button>
  );
}

// Custom link component that opens in new tab
const MarkdownLink = ({ href, children }) => (
  <a href={href} target="_blank" rel="noopener noreferrer">
    {children}
  </a>
);

// Markdown components config - defined at module level for reuse
const markdownComponents = {
  a: MarkdownLink,
};

// Preprocess text to extract mailto links and render them separately
function TextWithMailto({ content }) {
  // Check if content contains mailto: links
  const mailtoRegex = /(mailto:[^\s\]]+)/g;
  const matches = content.match(mailtoRegex);

  if (!matches) {
    return <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>{content}</ReactMarkdown>;
  }

  // Split content by mailto links
  const parts = content.split(mailtoRegex);

  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith("mailto:")) {
          return <MailtoButton key={index} href={part} />;
        }
        return part ? (
          <ReactMarkdown key={index} remarkPlugins={[remarkGfm]} components={markdownComponents}>
            {part}
          </ReactMarkdown>
        ) : null;
      })}
    </>
  );
}

// Renders the expanded chip content with all its variants
function ChipExpandedContent({ activeChip }) {
  if (!activeChip) return null;

  const { content, label } = activeChip;

  return (
    <>
      <Typography
        variant="subtitle2"
        sx={{
          fontWeight: 500,
          fontSize: "14px !important",
          marginBottom: 1,
          paddingRight: 3,
        }}
      >
        {label}
      </Typography>

      {typeof content === "string" ? (
        <Typography sx={{ fontSize: "13px !important", fontFamily: "monospace" }}>
          {content}
        </Typography>
      ) : content?.citations !== undefined ? (
        // Retrieval trace with citations
        <Box>
          <Typography sx={{ fontSize: "13px !important", marginBottom: 2, lineHeight: 1.4 }}>
            {content.description}
          </Typography>
          {content.query && (
            <Box sx={{ mb: 2 }}>
              <Typography sx={{ fontWeight: 500, fontSize: "13px", mb: 0.5 }}>
                Search Query:
              </Typography>
              <Typography sx={{ fontSize: "13px", color: "rgba(0,0,0,0.7)", fontStyle: "italic" }}>
                &quot;{content.query}&quot;
              </Typography>
            </Box>
          )}
          {content.citations?.length > 0 && (
            <Box>
              <Typography sx={{ fontWeight: 500, fontSize: "13px", mb: 1 }}>
                Sources Found ({content.citations.length}):
              </Typography>
              <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
                {content.citations.map((citation, idx) => (
                  <CitationCard key={idx} citation={citation} index={idx} />
                ))}
              </Box>
            </Box>
          )}
        </Box>
      ) : content?.description !== undefined || content?.details ? (
        <Box>
          <Typography sx={{ fontSize: "13px !important", marginBottom: 2, lineHeight: 1.4 }}>
            {content.description}
          </Typography>
          {content.details ? (
            <Box sx={{ fontSize: "13px !important" }}>
              {content.details.input && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 500, fontSize: "13px", mb: 0.5 }}>Input:</Typography>
                  <Typography sx={{ fontSize: "13px", color: "rgba(0,0,0,0.7)" }}>
                    &quot;{content.details.input}&quot;
                  </Typography>
                </Box>
              )}
              {content.details.output && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 500, fontSize: "13px", mb: 0.5 }}>Output:</Typography>
                  <ActionObservationOutput output={content.details.output} />
                </Box>
              )}
              {content.details.toolName && (
                <Box sx={{ mb: 2 }}>
                  <Typography sx={{ fontWeight: 500, fontSize: "13px", mb: 0.5 }}>Tool Details:</Typography>
                  <Box sx={{ fontSize: "12px", color: "rgba(0,0,0,0.7)" }}>
                    <Typography sx={{ fontSize: "12px" }}>Tool: {content.details.toolName}</Typography>
                    {content.details.invocation && (
                      <Box sx={{ mt: 1 }}>
                        <Typography sx={{ fontSize: "12px", fontWeight: 500, mb: 0.5 }}>Invocation:</Typography>
                        <JsonView
                          value={(() => {
                            try {
                              return JSON.parse(content.details.invocation);
                            } catch {
                              return { raw: content.details.invocation };
                            }
                          })()}
                          collapsed={false}
                          style={{ backgroundColor: "rgba(0,0,0,0.02)", fontSize: "12px", padding: "8px", borderRadius: "4px" }}
                        />
                      </Box>
                    )}
                  </Box>
                </Box>
              )}
            </Box>
          ) : (
            <JsonView
              value={{ function: content.function, endpoint: content.endpoint, parameters: content.parameters }}
              collapsed={1}
              style={{ backgroundColor: "transparent", fontSize: "13px" }}
            />
          )}
        </Box>
      ) : (
        <Box>
          <JsonView value={content} collapsed={1} style={{ backgroundColor: "transparent", fontSize: "13px" }} />
        </Box>
      )}
    </>
  );
}

// Parses and renders action/observation output
function ActionObservationOutput({ output }) {
  const sections = [];
  const actionRegex = /Action:\s*```\s*([\s\S]*?)\s*```/g;
  let lastIndex = 0;
  let match;

  while ((match = actionRegex.exec(output)) !== null) {
    const textBefore = output.substring(lastIndex, match.index).trim();
    if (textBefore?.startsWith("Observation:")) {
      sections.push({ type: "observation", content: textBefore.replace("Observation:", "").trim() });
    }
    sections.push({ type: "action", content: match[1] });
    lastIndex = match.index + match[0].length;
  }

  const remaining = output.substring(lastIndex).trim();
  if (remaining) {
    if (remaining.startsWith("Observation:")) {
      sections.push({ type: "observation", content: remaining.replace("Observation:", "").trim() });
    } else {
      sections.push({ type: "text", content: remaining });
    }
  }

  return (
    <Box>
      {sections.map((section, index) => (
        <Box key={index} sx={{ mb: index < sections.length - 1 ? 2 : 0 }}>
          {section.type === "action" && (
            <>
              <Typography sx={{ fontSize: "12px", fontWeight: 500, mb: 0.5 }}>Action:</Typography>
              <JsonView
                value={(() => {
                  try {
                    return JSON.parse(section.content);
                  } catch {
                    return { error: "Invalid JSON", raw: section.content };
                  }
                })()}
                collapsed={false}
                style={{ backgroundColor: "rgba(0,0,0,0.02)", fontSize: "12px", padding: "8px", borderRadius: "4px" }}
              />
            </>
          )}
          {section.type === "observation" && (
            <>
              <Typography sx={{ fontSize: "12px", fontWeight: 500, mb: 0.5 }}>Observation:</Typography>
              <Typography sx={{ fontSize: "12px", color: "rgba(0,0,0,0.7)", whiteSpace: "pre-wrap" }}>
                {section.content}
              </Typography>
            </>
          )}
          {section.type === "text" && (
            <Typography sx={{ fontSize: "12px", fontFamily: "monospace", whiteSpace: "pre-wrap" }}>
              {section.content}
            </Typography>
          )}
        </Box>
      ))}
    </Box>
  );
}

// ─── MCP approval card ────────────────────────────────────────────────────
// Renders an inline Approve / Reject prompt when an MCP tool call requires
// human approval. Args are parsed into a nice key-value table with a fallback
// "raw JSON" toggle for inspection. The decision is dispatched via the
// onApprovalSubmit callback wired from useChat.
// Apple-style easing — "ease-out-expo": fast off the line, settles gently.
const APPLE_EASE = [0.16, 1, 0.3, 1];

const cardVariants = {
  hidden:  { opacity: 0, y: 10, scale: 0.96, filter: 'blur(10px)' },
  visible: {
    opacity: 1, y: 0, scale: 1, filter: 'blur(0px)',
    transition: {
      type: 'spring', stiffness: 240, damping: 28, mass: 0.85,
      filter:  { duration: 0.5, ease: APPLE_EASE },
      opacity: { duration: 0.35, ease: APPLE_EASE },
      staggerChildren: 0.05,
      delayChildren: 0.12,
    },
  },
};

const childVariants = {
  hidden:  { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.35, ease: APPLE_EASE } },
};

function ApprovalArgsTable({ args }) {
  if (!args || typeof args !== 'object') return null;
  const entries = Object.entries(args);
  if (entries.length === 0) return null;
  return (
    <Box
      component={motion.div}
      variants={childVariants}
      sx={{ display: 'grid', gridTemplateColumns: 'auto 1fr', columnGap: 2, rowGap: 1, mt: 1.5 }}
    >
      {entries.map(([k, v], idx) => {
        const isObj = v !== null && typeof v === 'object';
        const text = isObj ? JSON.stringify(v, null, 2) : String(v);
        const isMultiline = !isObj && (text.length > 80 || text.includes('\n'));
        return (
          <motion.div
            key={k}
            style={{ display: 'contents' }}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.32, ease: APPLE_EASE, delay: 0.18 + idx * 0.04 }}
          >
            <Typography sx={{ fontSize: '0.72rem', fontWeight: 600, color: 'var(--dm-muted, rgba(0,0,0,0.55))', textTransform: 'uppercase', letterSpacing: '0.04em', pt: isMultiline || isObj ? '4px' : 0 }}>
              {k}
            </Typography>
            {isObj || isMultiline ? (
              <Box component="pre" sx={{
                m: 0, p: 1, borderRadius: 1, fontSize: '0.78rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                backgroundColor: 'var(--dm-subtle, rgba(0,0,0,0.04))',
                border: '1px solid var(--dm-border, rgba(0,0,0,0.06))',
                color: 'var(--dm-text, #1a1a1a)',
              }}>{text}</Box>
            ) : (
              <Typography sx={{ fontSize: '0.88rem', color: 'var(--dm-text, #1a1a1a)', wordBreak: 'break-word' }}>{text}</Typography>
            )}
          </motion.div>
        );
      })}
    </Box>
  );
}

function ApprovalCard({ group, onApprovalSubmit }) {
  const [showRaw, setShowRaw] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const parsed = (() => {
    try { return JSON.parse(group.arguments || '{}'); } catch { return null; }
  })();
  const decided = group.decision === 'approved' || group.decision === 'rejected';
  const disabled = decided || submitting;

  const submit = async (approve) => {
    if (disabled || !onApprovalSubmit) return;
    setSubmitting(true);
    try {
      await onApprovalSubmit(group.requestId, approve);
    } finally {
      setSubmitting(false);
    }
  };

  const accent = decided
    ? (group.decision === 'approved' ? '#2e7d32' : '#c62828')
    : '#0A84FF'; // Apple system blue for the pending state — actionable, neutral, modern.
  const accentBg = decided
    ? (group.decision === 'approved' ? 'rgba(46, 125, 50, 0.06)' : 'rgba(198, 40, 40, 0.06)')
    : 'rgba(10, 132, 255, 0.07)';
  const IconCmp = decided
    ? (group.decision === 'approved' ? ShieldCheck : ShieldX)
    : ShieldAlert;

  const titleText = decided
    ? (group.decision === 'approved' ? 'Approved' : 'Rejected')
    : 'Approval required';
  const descriptionText = decided
    ? (group.decision === 'approved'
        ? 'The assistant is now running the tool with the arguments below.'
        : 'The assistant skipped this tool call.')
    : `The assistant wants to run ${group.toolName || 'this tool'} with the arguments below. Approve to continue or reject to cancel this specific action.`;

  return (
    <Paper
      component={motion.div}
      elevation={0}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      layout
      sx={{
        p: 2.25,
        backgroundColor: accentBg,
        border: `1px solid ${accent}40`,
        borderRadius: 2,
        transition: 'background-color 0.4s ease, border-color 0.4s ease',
        willChange: 'transform, opacity, filter',
      }}
    >
      <Box component={motion.div} variants={childVariants} sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 0.5 }}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={decided ? group.decision : 'pending'}
            initial={{ opacity: 0, scale: 0.6, rotate: -12 }}
            animate={{ opacity: 1, scale: 1, rotate: 0 }}
            exit={{ opacity: 0, scale: 0.6, rotate: 12 }}
            transition={{ type: 'spring', stiffness: 380, damping: 22 }}
            style={{ display: 'inline-flex' }}
          >
            <IconCmp size={18} style={{ color: accent, flexShrink: 0 }} />
          </motion.div>
        </AnimatePresence>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={titleText}
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.25, ease: APPLE_EASE }}
          >
            <Typography sx={{ fontWeight: 600, fontSize: '0.92rem', color: 'var(--dm-text, #1a1a1a)' }}>
              {titleText}
            </Typography>
          </motion.div>
        </AnimatePresence>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 0.75, alignItems: 'center' }}>
          {group.serverLabel && (
            <Chip
              size="small"
              label={group.serverLabel}
              sx={{ fontSize: '0.7rem', height: 22, backgroundColor: 'var(--dm-subtle, rgba(0,0,0,0.05))' }}
            />
          )}
          {group.toolName && (
            <Chip
              size="small"
              icon={<Code size={12} />}
              label={group.toolName}
              sx={{ fontSize: '0.7rem', height: 22, backgroundColor: 'var(--dm-surface, white)', border: '1px solid var(--dm-border, rgba(0,0,0,0.1))' }}
            />
          )}
        </Box>
      </Box>

      <Box component={motion.div} variants={childVariants}>
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={descriptionText}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25, ease: APPLE_EASE }}
          >
            <Typography sx={{ fontSize: '0.8rem', color: 'var(--dm-muted, rgba(0,0,0,0.6))' }}>
              {descriptionText}
            </Typography>
          </motion.div>
        </AnimatePresence>
      </Box>

      {parsed ? (
        <ApprovalArgsTable args={parsed} />
      ) : (
        <Box
          component={motion.pre}
          variants={childVariants}
          sx={{
            m: 0, mt: 1.5, p: 1, borderRadius: 1,
            fontSize: '0.78rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            backgroundColor: 'var(--dm-subtle, rgba(0,0,0,0.04))',
          }}
        >{group.arguments || '(no arguments)'}</Box>
      )}

      {parsed && (
        <Box component={motion.div} variants={childVariants} sx={{ mt: 1 }}>
          <Button
            size="small"
            onClick={() => setShowRaw(s => !s)}
            sx={{ textTransform: 'none', fontSize: '0.72rem', color: 'var(--dm-muted, rgba(0,0,0,0.55))', minWidth: 'auto', px: 0.5 }}
          >
            {showRaw ? 'Hide raw JSON' : 'Show raw JSON'}
          </Button>
          <Collapse in={showRaw}>
            <Box component="pre" sx={{
              m: 0, mt: 0.5, p: 1, borderRadius: 1,
              fontSize: '0.72rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
              backgroundColor: 'var(--dm-subtle, rgba(0,0,0,0.04))',
            }}>{group.arguments || ''}</Box>
          </Collapse>
        </Box>
      )}

      <AnimatePresence initial={false}>
        {!decided && (
          <motion.div
            key="actions"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0, transition: { duration: 0.35, ease: APPLE_EASE, delay: 0.22 } }}
            exit={{ opacity: 0, y: -4, height: 0, marginTop: 0, transition: { duration: 0.25, ease: APPLE_EASE } }}
            style={{ overflow: 'hidden' }}
          >
            <Box sx={{ display: 'flex', gap: 1, mt: 2, justifyContent: 'flex-end' }}>
              <Box component={motion.div} whileTap={{ scale: 0.97 }} whileHover={{ y: -1 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }}>
                <Button
                  size="small"
                  variant="outlined"
                  disabled={disabled}
                  onClick={() => submit(false)}
                  startIcon={submitting ? <CircularProgress size={12} /> : <X size={14} />}
                  sx={{
                    textTransform: 'none',
                    borderColor: 'rgba(198, 40, 40, 0.4)',
                    color: '#c62828',
                    '&:hover': { borderColor: '#c62828', backgroundColor: 'rgba(198, 40, 40, 0.04)' },
                  }}
                >
                  Reject
                </Button>
              </Box>
              <Box component={motion.div} whileTap={{ scale: 0.97 }} whileHover={{ y: -1 }} transition={{ type: 'spring', stiffness: 400, damping: 25 }}>
                <Button
                  size="small"
                  variant="contained"
                  disabled={disabled}
                  onClick={() => submit(true)}
                  startIcon={submitting ? <CircularProgress size={12} sx={{ color: 'white' }} /> : <Check size={14} />}
                  sx={{
                    textTransform: 'none',
                    backgroundColor: '#0A84FF',
                    boxShadow: '0 1px 2px rgba(10,132,255,0.25)',
                    '&:hover': { backgroundColor: '#0066CC', boxShadow: '0 2px 6px rgba(10,132,255,0.35)' },
                  }}
                >
                  Approve
                </Button>
              </Box>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>
    </Paper>
  );
}

const MIN_DISPLAY_TIME = 1000; // Minimum time to show loading/thinking indicators

const ChatMessage = memo(function ChatMessage({
  exchange,
  exchangeIndex,
  latestMessageRef,
  contentFontSizes,
  activeChips,
  onChipChange,
  copiedId,
  onCopy,
  getCopyContent,
  onWidgetSubmit,
  onOptionSelect,
  onRetry,
  onApprovalSubmit,
  isLoading,
}) {
  const [textDialogOpen, setTextDialogOpen] = useState(null);
  const [imageDialogOpen, setImageDialogOpen] = useState(null);
  const [showRaw, setShowRaw] = useState(false);
  const [traceDialogOpen, setTraceDialogOpen] = useState(false);

  // Single unified indicator: dots show continuously from loading through thinking.
  // "Thinking..." label fades in when thinking message arrives — no gap, no flicker.
  const [showIndicator, setShowIndicator] = useState(false);
  const indicatorStartRef = useRef(null);

  // Content is ready when indicator is not showing or content already exists
  const hasContent = exchange.responses.some(r => (r.type === "text" && r.content) || r.type === "widget" || r.type === "widget_v2" || r.type === "generated_image");
  const contentReady = !showIndicator || hasContent;

  // Compute grouping at render time instead of storing in state
  const groupedResponses = useMemo(() => {
    const groups = groupMessages(exchange.responses);
    const sourcesGroups = groups.filter(g => g.type === 'sources');
    if (sourcesGroups.length > 0) console.log('[ChatMessage] Sources groups found:', sourcesGroups.length, sourcesGroups);
    return groups;
  }, [exchange.responses]);

  const getRawContent = () => {
    return groupedResponses.map(group => {
      if (group.type === "text") return group.content;
      if (group.type === "widget" && group.widgetProps) {
        const entries = Object.entries(group.widgetProps).map(([k, v]) => `${k}:${v}`).join('|');
        return `§§${entries}§§`;
      }
      if (group.type === "widget_v2" && group.tree) {
        return `@@widget\n${serializeWidgetV2Tree(group.tree)}\n@@`;
      }
      return "";
    }).filter(Boolean).join("\n");
  };

  // Conditions from props/exchange
  const isInitialLoading = exchange.isLatest && isLoading && exchange.responses.length === 0;
  const hasThinkingMessage = exchange.isLatest && exchange.responses.some(r => r.type === "thinking");
  const hasCallingChips = exchange.isLatest && exchange.responses.some(r => r.type === "mcp_chip" && r.status === "calling");
  // Detect gap after tool completion: chips are done but no text has arrived yet
  const waitingAfterTools = exchange.isLatest && isLoading &&
    exchange.responses.some(r => r.type === "mcp_chip" && r.status === "completed") &&
    !exchange.responses.some(r => (r.type === "text" && r.content) || r.type === "widget" || r.type === "widget_v2");
  // Show indicator when loading/thinking, or waiting after tool call — but not while chips are actively calling
  const shouldShowIndicator = (isInitialLoading || hasThinkingMessage || waitingAfterTools) && !hasCallingChips;

  useEffect(() => {
    if (shouldShowIndicator && !showIndicator) {
      indicatorStartRef.current = Date.now();
      setShowIndicator(true);
    } else if (!shouldShowIndicator && showIndicator) {
      // Calling chips skip MIN_DISPLAY_TIME — the chip IS the progress indicator
      if (hasCallingChips) {
        setShowIndicator(false);
        return;
      }
      const elapsed = Date.now() - (indicatorStartRef.current || 0);
      const remaining = MIN_DISPLAY_TIME - elapsed;
      if (remaining > 0) {
        const timer = setTimeout(() => setShowIndicator(false), remaining);
        return () => clearTimeout(timer);
      } else {
        setShowIndicator(false);
      }
    }
  }, [shouldShowIndicator, showIndicator, hasCallingChips]);

  return (
    <Box
      ref={exchange.isLatest ? latestMessageRef : null}
      sx={{
        width: "100%",
        overflow: "visible",
        mb: exchange.isLatest ? 0 : 6,
        "&:hover .copy-button": { opacity: 1 },
      }}
    >
      {/* User message */}
      <Box sx={{ marginBottom: "0.5rem", "&:hover .copy-button": { opacity: 1 } }}>
        <motion.div
          initial={false}
          animate={{ opacity: 1, scale: exchange.isLatest ? 1 : 0.85 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          style={{ transformOrigin: "left center" }}
        >
          {exchange.widgetResponse ? null : (
            <>
              {/* Attached images (current session) */}
              {exchange.attachedImages && exchange.attachedImages.length > 0 && (
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
                  {exchange.attachedImages.map((img, idx) => (
                    <Box
                      key={idx}
                      onClick={() => setImageDialogOpen(img)}
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: 1,
                        overflow: "hidden",
                        border: "1px solid rgba(0,0,0,0.1)",
                        cursor: "pointer",
                        "&:hover": { border: "1px solid rgba(0,0,0,0.25)" },
                      }}
                    >
                      <img
                        src={img.preview}
                        alt={img.name || `Attached image ${idx + 1}`}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "cover",
                        }}
                      />
                    </Box>
                  ))}
                </Box>
              )}
              {/* Image placeholder (loaded from history) */}
              {exchange.hasImageAttachment && !exchange.attachedImages && (
                <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1 }}>
                  {Array.from({ length: exchange.imageCount || 1 }).map((_, idx) => (
                    <Box
                      key={idx}
                      sx={{
                        width: 80,
                        height: 80,
                        borderRadius: 1,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        backgroundColor: "rgba(0,0,0,0.05)",
                        border: "1px dashed rgba(0,0,0,0.15)",
                      }}
                    >
                      <Typography sx={{ fontSize: "1.5rem", opacity: 0.3 }}>🖼️</Typography>
                    </Box>
                  ))}
                </Box>
              )}
              {/* Attached texts */}
              {exchange.attachedTexts && exchange.attachedTexts.length > 0 && (
                <Box sx={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: 1.5,
                  mb: 1,
                }}>
                  {exchange.attachedTexts.map((txt, idx) => {
                    const fileStyles = {
                      csv: { border: "#4CAF50", chip: "rgba(76, 175, 80, 0.15)", chipText: "#2e7d32" },
                      json: { border: "#FF9800", chip: "rgba(255, 152, 0, 0.15)", chipText: "#e65100" },
                      pdf: { border: "#F44336", chip: "rgba(244, 67, 54, 0.15)", chipText: "#c62828" },
                      txt: { border: "#42A5F5", chip: "rgba(66, 165, 245, 0.15)", chipText: "#1976d2" },
                      md: { border: "#2196F3", chip: "rgba(33, 150, 243, 0.15)", chipText: "#1565c0" },
                      sql: { border: "#9C27B0", chip: "rgba(156, 39, 176, 0.15)", chipText: "#7b1fa2" },
                      py: { border: "#3776AB", chip: "rgba(55, 118, 171, 0.15)", chipText: "#2c5f8a" },
                      js: { border: "#F7DF1E", chip: "rgba(247, 223, 30, 0.2)", chipText: "#8a7800" },
                      ts: { border: "#3178C6", chip: "rgba(49, 120, 198, 0.15)", chipText: "#235a9e" },
                      default: { border: "#9E9E9E", chip: "rgba(0,0,0,0.1)", chipText: "rgba(0,0,0,0.5)" },
                    };
                    const style = fileStyles[txt.ext] || fileStyles.default;
                    const extLabel = txt.ext || "txt";
                    return (
                    <Box
                      key={txt.id || idx}
                      onClick={() => setTextDialogOpen(txt)}
                      sx={{
                        position: "relative",
                        cursor: "pointer",
                        width: 120,
                        mb: "4px",
                        mr: "4px",
                      }}
                    >
                      {/* Stacked back layer */}
                      <Box sx={{ position: "absolute", bottom: -4, left: 3, right: -3, top: 0, borderRadius: 0.75, backgroundColor: `${style.border}12`, border: `1px solid ${style.border}20` }} />
                      {/* Main card */}
                      <Box sx={{
                        position: "relative",
                        display: "flex",
                        flexDirection: "column",
                        p: 1.25,
                        height: 120,
                        borderRadius: 0.75,
                        backgroundColor: "var(--dm-surface, white)",
                        border: `1px solid ${style.border}30`,
                        boxShadow: `0 2px 8px ${style.border}12`,
                        overflow: "hidden",
                        transition: "all 0.2s",
                        "&:hover": { transform: "translateY(-2px)", boxShadow: `0 8px 20px ${style.border}20` },
                      }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.75 }}>
                          <FileText size={12} style={{ color: style.border, flexShrink: 0 }} />
                          <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, color: style.chipText, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
                            {txt.name || "Pasted"}
                          </Typography>
                        </Box>
                        <Box sx={{ flex: 1, overflow: "hidden" }}>
                          <Typography sx={{
                            fontSize: "0.6rem",
                            color: "rgba(0,0,0,1)",
                            lineHeight: 1.4,
                            overflow: "hidden",
                            display: "-webkit-box",
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: "vertical",
                            wordBreak: "break-all",
                          }}>
                            {txt.preview}
                          </Typography>
                        </Box>
                        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 0.75 }}>
                          <Box sx={{ display: "flex", gap: 0.25 }}>
                            {[0.3, 0.5, 0.8].map((o, i) => <Box key={i} sx={{ width: 3, height: 3, borderRadius: "50%", backgroundColor: style.border, opacity: o }} />)}
                          </Box>
                          <Box sx={{ px: 0.5, py: 0.15, borderRadius: 0.5, backgroundColor: style.chip }}>
                            <Typography sx={{ fontSize: "0.55rem", fontWeight: 700, color: style.chipText }}>.{extLabel}</Typography>
                          </Box>
                        </Box>
                      </Box>
                    </Box>
                    );
                  })}
                </Box>
              )}
              {/* Text message */}
              {exchange.userMessage &&
               !exchange.userMessage.match(/^\[[\d]+ images?\]$/) &&
               !(exchange.userMessage === '[Pasted content]' && exchange.attachedTexts?.length > 0) && (
                <CollapsibleUserMessage
                  text={exchange.userMessage.replace(/\s*\[\d+ images?\]$/, '')}
                  fontSize={contentFontSizes}
                  isLatest={exchange.isLatest}
                />
              )}
            </>
          )}
        </motion.div>
      </Box>

      {/* Response */}
      <Box sx={{ marginTop: exchange.isLatest ? 2 : 1 }}>
        <Box>
        {groupedResponses
          .filter(group => {
            if (group.type === "thinking") return false;
            if (!exchange.isLatest) return true;
            if (!contentReady) return ["chipRow", "mcp_chip_row", "mcp_connecting", "reasoning", "mcp_approval_request"].includes(group.type);
            return true;
          })
          .map((group, groupIndex) => (
          <Box key={group.messageIndex ?? `g-${groupIndex}`} sx={{ mb: 4 }}>
            {group.type === "chipRow" && (
              <Box>
                <Stack direction="row" spacing={2} sx={{ minHeight: "40px", justifyContent: "flex-start" }}>
                  {group.chips.map((chip) => {
                    const chipKey = `${exchangeIndex}-${groupIndex}-${chip.messageIndex}`;
                    return (
                      <DynamicChip
                        key={chipKey}
                        icon={chip.icon}
                        label={chip.label}
                        status={chip.status}
                        content={chip.content}
                        onExpand={(chipData) => onChipChange(chipData, chipKey)}
                        isActive={activeChips[chipKey]?.label === chip.label}
                        startDelay={0}
                      />
                    );
                  })}
                </Stack>

                <Collapse in={Object.keys(activeChips).some((key) => key.startsWith(`${exchangeIndex}-${groupIndex}-`))}>
                  <Paper
                    elevation={0}
                    sx={{
                      mt: 1,
                      p: 2,
                      backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.02))",
                      border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
                      borderRadius: 2,
                      fontSize: "13px !important",
                      width: "100%",
                      position: "relative",
                      "& *": { fontSize: "13px !important" },
                    }}
                  >
                    <IconButton
                      onClick={() => {
                        const activeChipKey = Object.keys(activeChips).find((key) =>
                          key.startsWith(`${exchangeIndex}-${groupIndex}-`)
                        );
                        if (activeChipKey) onChipChange(null, activeChipKey);
                      }}
                      sx={{
                        position: "absolute",
                        top: 8,
                        right: 8,
                        padding: 0.5,
                        color: "var(--dm-muted, rgba(0, 0, 0, 0.4))",
                        "&:hover": { backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.04))", color: "var(--dm-text, rgba(0, 0, 0, 0.6))" },
                      }}
                    >
                      <CloseIcon sx={{ fontSize: "16px" }} />
                    </IconButton>

                    <ChipExpandedContent
                      activeChip={
                        activeChips[
                          Object.keys(activeChips).find((key) => key.startsWith(`${exchangeIndex}-${groupIndex}-`))
                        ]
                      }
                    />
                  </Paper>
                </Collapse>
              </Box>
            )}

            {group.type === "text" && (
              <Box>
                <Box
                  sx={{
                    fontFamily: "var(--font-oracle-sans), sans-serif",
                    lineHeight: 1.6,
                    fontSize: exchange.isLatest ? "inherit" : { xs: "0.95rem", sm: "1rem", md: "1.05rem" },
                    color: "inherit",
                    opacity: exchange.isLatest ? 1 : 0.7,
                    "& *": { fontFamily: "var(--font-oracle-sans), sans-serif !important", lineHeight: "inherit !important", color: "inherit" },
                    "& table": { borderCollapse: "collapse", width: "100%", marginBottom: 2 },
                    "& th, & td": { border: "1px solid #ddd", padding: "8px", textAlign: "left" },
                    "& th": { backgroundColor: "#f5f5f5", fontWeight: "bold" },
                    "& pre, & code": {
                      overflowX: "auto",
                      maxWidth: "100%",
                      display: "block",
                    },
                    "& p": {
                      overflowX: "auto",
                      overflowY: "hidden",
                      maxWidth: "100%",
                    },
                  }}
                >
                  <TextWithMailto content={group.content} isLatest={exchange.isLatest} />
                  <Sources sources={group.sources} delay={exchange.isLatest ? 0.3 : 0} />
                </Box>
              </Box>
            )}

            {group.type === "sources" && (
              <Sources sources={group.sources} delay={exchange.isLatest ? 0.3 : 0} />
            )}

            {group.type === "widget" && (
              <Box sx={{ my: 2 }}>
                <Widget
                  props={group.widgetProps}
                  streamingKey={group.streamingKey}
                  streamingValue={group.streamingValue}
                  isComplete={group.isComplete}
                  selectedData={group.selectedData}
                  disabled={group.disabled}
                  onSubmit={onWidgetSubmit}
                />
              </Box>
            )}

            {group.type === "widget_v2" && (
              <Box sx={{ my: 2 }}>
                <WidgetV2
                  tree={group.tree}
                  isComplete={group.isComplete}
                  onSubmit={onWidgetSubmit}
                  disabled={group.disabled}
                />
              </Box>
            )}

            {group.type === "generated_image" && (() => {
              const imgSrc = `data:image/png;base64,${group.content}`;
              return (
                <Box sx={{ my: 1 }}>
                  <Box
                    onClick={() => {
                      const w = window.open();
                      w.document.write(`<img src="${imgSrc}" style="max-width:100%;height:auto" />`);
                      w.document.title = "Generated Image";
                    }}
                    sx={{
                      cursor: "pointer",
                      borderRadius: 2,
                      overflow: "hidden",
                      border: "1px solid rgba(0,0,0,0.08)",
                      display: "inline-block",
                      maxWidth: 512,
                      transition: "box-shadow 0.2s",
                      "&:hover": { boxShadow: "0 4px 20px rgba(0,0,0,0.12)" },
                    }}
                  >
                    <img
                      src={imgSrc}
                      alt={group.revisedPrompt || "Generated image"}
                      style={{ width: "100%", height: "auto", display: "block" }}
                    />
                  </Box>
                  {group.revisedPrompt && (
                    <Typography sx={{ fontSize: "0.78rem", color: "rgba(0,0,0,0.4)", mt: 0.75, fontStyle: "italic", maxWidth: 512 }}>
                      {group.revisedPrompt}
                    </Typography>
                  )}
                </Box>
              );
            })()}

            {group.type === "generated_image_placeholder" && (
              <Box sx={{ my: 1, p: 2, borderRadius: 2, border: "1px solid rgba(79, 70, 229, 0.15)", backgroundColor: "rgba(79, 70, 229, 0.04)", maxWidth: 512 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
                  <Image src="/ri--image-circle-ai-line.svg" alt="" width={18} height={18} style={{ opacity: 0.5 }} />
                  <Typography sx={{ fontSize: "0.82rem", color: "#4f46e5", fontWeight: 500 }}>
                    Image generated
                  </Typography>
                </Box>
                {group.revisedPrompt && (
                  <Typography sx={{ fontSize: "0.78rem", color: "rgba(0,0,0,0.45)", fontStyle: "italic" }}>
                    {group.revisedPrompt}
                  </Typography>
                )}
              </Box>
            )}

            {group.type === "reasoning" && (
              <ReasoningBlock text={group.text} done={group.done !== false} />
            )}

            {group.type === "code_execution" && (
              <CodeExecutionBlock code={group.code} output={group.output} status={group.status} />
            )}

            {group.type === "error" && group.content === "mcp_auth_expired" && (() => {
              // Resolve the failing server LOCALLY from storage so the banner can show
              // the right copy and the right action per auth type. No guessing, no alerts.
              const sanitize = (name) => {
                let l = (name || '').replace(/[^a-zA-Z0-9_-]/g, '_');
                if (!/^[a-zA-Z]/.test(l)) l = 'mcp_' + l;
                return l;
              };
              let stored = [];
              try {
                if (typeof window !== 'undefined') {
                  stored = JSON.parse(localStorage.getItem('mcpServers') || '[]');
                }
              } catch {}
              const enabled = stored.filter(s => s.enabled !== false && s.endpoint && !s.isNative);
              let server = null;
              if (group.serverEndpoint) {
                server = stored.find(s => s.endpoint === group.serverEndpoint) || null;
              }
              if (!server && group.serverLabel) {
                server = enabled.find(s => sanitize(s.name) === group.serverLabel) || null;
                // Also try matching among ALL stored (incl. disabled), in case the user
                // disabled it after the error
                if (!server) server = stored.find(s => sanitize(s.name) === group.serverLabel) || null;
              }
              if (!server && enabled.length === 1) {
                server = enabled[0];
              }
              if (typeof window !== 'undefined' && !window.__mcp_banner_logged) {
                window.__mcp_banner_logged = true;
                console.log('[mcp banner]', {
                  serverLabel: group.serverLabel,
                  serverEndpoint: group.serverEndpoint,
                  serverAuthType: group.serverAuthType,
                  resolved: server?.name || null,
                  enabledCount: enabled.length,
                  storedCount: stored.length,
                });
              }

              const displayName = (server && server.name) || group.serverLabel || 'MCP connector';
              const authType = server?.authType || group.serverAuthType || null;

              // Per-authType copy + action
              let title;
              let description;
              let buttonLabel;
              let onClickAction;
              const returnTo = typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/';
              const openOAuth = () => { window.location.href = `/api/mcp/oauth/authorize?endpoint=${encodeURIComponent(server.endpoint)}&returnTo=${encodeURIComponent(returnTo)}`; };
              const openSettings = () => { window.location.href = server ? `/settings/tools?focus=${encodeURIComponent(server.id)}` : '/settings/tools'; };

              if (authType === 'oauth2.1') {
                title = `Authorization needed — ${displayName}`;
                description = `Sign in to "${displayName}" to grant access. After authorizing you'll return here.`;
                buttonLabel = 'Authorize';
                onClickAction = openOAuth;
              } else if (authType === 'oauth2') {
                title = `${displayName} is unreachable`;
                description = `The OAuth 2.0 token was obtained, but the upstream server rejected the request. This is usually a temporary issue or a server-side bug. You can disable the tool or verify its configuration.`;
                buttonLabel = 'Open in Settings';
                onClickAction = openSettings;
              } else if (authType === 'api-key' || authType === 'bearer') {
                title = `${displayName} credential rejected`;
                description = `The upstream rejected the ${authType === 'bearer' ? 'bearer token' : 'API key'}. Update it in Settings to fix.`;
                buttonLabel = 'Update credential';
                onClickAction = openSettings;
              } else if (authType === 'none' || (server && !server.authType)) {
                title = `${displayName} is unreachable`;
                description = `The MCP server returned an error. This is likely a temporary upstream issue. You can disable the tool or check it later.`;
                buttonLabel = 'Open in Settings';
                onClickAction = openSettings;
              } else {
                title = `${displayName} is unavailable`;
                description = `An MCP connector failed. Open Settings to inspect.`;
                buttonLabel = 'Open in Settings';
                onClickAction = openSettings;
              }

              return (
                <Paper
                  elevation={0}
                  sx={{
                    p: 2.5,
                    backgroundColor: "rgba(255, 152, 0, 0.06)",
                    border: "1px solid rgba(255, 152, 0, 0.25)",
                    borderRadius: 2,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 2,
                  }}
                >
                  <Box>
                    <Typography sx={{ fontWeight: 500, fontSize: "0.9rem", color: "#e65100", mb: 0.5, display: "flex", alignItems: "center", gap: 1 }}>
                      <KeyRound size={16} /> {title}
                    </Typography>
                    <Typography sx={{ fontSize: "0.8rem", color: "rgba(0,0,0,0.55)", lineHeight: 1.5 }}>
                      {description}
                    </Typography>
                  </Box>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<KeyRound size={14} />}
                    onClick={onClickAction}
                    sx={{
                      flexShrink: 0,
                      textTransform: "none",
                      borderColor: "rgba(255, 152, 0, 0.4)",
                      color: "#e65100",
                      fontWeight: 500,
                      "&:hover": { borderColor: "#e65100", backgroundColor: "rgba(255, 152, 0, 0.08)" },
                    }}
                  >
                    {buttonLabel}
                  </Button>
                </Paper>
              );
            })()}

            {group.type === "error" && group.content !== "mcp_auth_expired" && (() => {
              // Parse tool-model incompatibility errors for a friendly message
              const toolModelMatch = group.content?.match(/Tool\(s\)\s*\[([^\]]+)\]\s*are only supported for\s*(.+?)\s*models/i);
              // Format tool names: web_search → Web Search
              const formatToolName = (name) => name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
              const friendlyMsg = toolModelMatch ? {
                tools: toolModelMatch[1].split(',').map(t => formatToolName(t.trim())).join(', '),
                providers: toolModelMatch[2],
              } : null;

              return (
                <Paper
                  elevation={0}
                  sx={{
                    p: 2,
                    backgroundColor: friendlyMsg ? "rgba(245, 158, 11, 0.05)" : "rgba(211, 47, 47, 0.04)",
                    border: `1px solid ${friendlyMsg ? "rgba(245, 158, 11, 0.25)" : "rgba(211, 47, 47, 0.2)"}`,
                    borderRadius: 2,
                  }}
                >
                  {friendlyMsg ? (
                    <>
                      <Typography
                        sx={{
                          fontWeight: 500,
                          fontSize: "0.9rem",
                          color: "#92400E",
                          mb: 1,
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                        }}
                      >
                        <AlertTriangle size={16} /> Tool not supported by this model
                      </Typography>
                      <Typography sx={{ fontSize: "0.85rem", color: "rgba(0,0,0,0.7)", lineHeight: 1.6 }}>
                        <strong>{friendlyMsg.tools}</strong> {friendlyMsg.tools.includes(',') ? 'are' : 'is'} only available with {friendlyMsg.providers} models. You can either:
                      </Typography>
                      <Typography component="div" sx={{ mt: 0.75, pl: 1.5, fontSize: "0.85rem", color: "rgba(0,0,0,0.7)", lineHeight: 2 }}>
                        • Switch to an {friendlyMsg.providers} model<br />
                        • Disable <strong>{friendlyMsg.tools}</strong> in <Box component="a" href="/settings/tools" sx={{ fontWeight: 600, color: "#92400E", textDecoration: "underline", cursor: "pointer", "&:hover": { color: "#78350F" } }}>Settings → Tools</Box>
                      </Typography>
                    </>
                  ) : (
                    <>
                      <Typography
                        sx={{
                          fontWeight: 500,
                          fontSize: "0.9rem",
                          color: "#c62828",
                          mb: 1,
                          display: "flex",
                          alignItems: "center",
                          gap: 1,
                        }}
                      >
                        <AlertTriangle size={16} /> Something went wrong
                      </Typography>
                      <Box
                        sx={{
                          backgroundColor: "var(--dm-subtle, #F8F8F7)",
                          border: "1px solid var(--dm-border, transparent)",
                          borderRadius: 1,
                          p: 1.5,
                          fontFamily: "monospace",
                          fontSize: "0.75rem",
                          color: "var(--dm-text, rgba(0, 0, 0, 0.7))",
                          overflowX: "auto",
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                        }}
                      >
                        {group.content}
                      </Box>
                      {(group.opcRequestId || group.timestamp) && (
                        <Box sx={{ mt: 1, display: "flex", flexDirection: "column", gap: 0.25, fontFamily: "monospace", fontSize: "0.68rem", color: "var(--dm-muted, rgba(0,0,0,0.45))" }}>
                          {group.opcRequestId && <Box>opc-request-id: <Box component="span" sx={{ color: "var(--dm-text, rgba(0,0,0,0.7))", userSelect: "all" }}>{group.opcRequestId}</Box></Box>}
                          {group.timestamp && <Box>time: {group.timestamp}</Box>}
                        </Box>
                      )}
                      {exchange.trace && (
                        <Box
                          onClick={() => setTraceDialogOpen(true)}
                          sx={{
                            display: "inline-flex", alignItems: "center", gap: 0.5,
                            fontSize: "0.7rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", cursor: "pointer", mt: 1,
                            fontFamily: "var(--font-oracle-sans), sans-serif",
                            "&:hover": { color: "#1976d2" },
                          }}
                        >
                          <Terminal size={12} /> View request trace
                        </Box>
                      )}
                    </>
                  )}
                </Paper>
              );
            })()}

            {group.type === "mcp_approval_request" && (
              <ApprovalCard group={group} onApprovalSubmit={onApprovalSubmit} />
            )}

            {group.type === "mcp_connecting" && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, minHeight: 24 }}>
                <DotMatrixLoader size="medium" />
              </Box>
            )}

            {group.type === "mcp_chip_row" && (() => {
              const rowKey = `mcp-row-${exchangeIndex}-${groupIndex}`;
              const selectedChipIndex = activeChips[rowKey]?.chipIndex;
              const selectedChip = selectedChipIndex !== undefined ? group.chips[selectedChipIndex] : null;
              const hasError = selectedChip?.status === "failed";
              const hasOutput = selectedChip?.output && selectedChip?.status === "completed";

              // Check if selected chip output contains audioBase64
              let audioBase64 = null;
              let outputMessage = null;
              if (hasOutput && selectedChip?.output) {
                try {
                  const parsed = JSON.parse(selectedChip.output);
                  if (parsed.audioBase64) {
                    audioBase64 = parsed.audioBase64;
                    outputMessage = parsed.message || (parsed.success ? "Audio generated successfully" : null);
                  }
                } catch (e) {
                  // Not JSON, that's fine
                }
              }

              // Find all chips with audio for direct display
              const audioChips = group.chips.filter(chip => {
                if (chip.output && chip.status === "completed") {
                  try {
                    const parsed = JSON.parse(chip.output);
                    return parsed.audioBase64;
                  } catch (e) {
                    return false;
                  }
                }
                return false;
              });

              const directAudioList = audioChips.map(chip => {
                try { return JSON.parse(chip.output).audioBase64; } catch (e) { return null; }
              }).filter(Boolean);

              return (
                <Box>
                  {/* Horizontal scrollable chip row */}
                  <Box
                    sx={{
                      display: "flex",
                      flexDirection: "row",
                      gap: 1,
                      overflowX: "auto",
                      overflowY: "visible",
                      pt: 0.5,
                      pb: 0.5,
                      mx: -0.5,
                      px: 0.5,
                      "&::-webkit-scrollbar": {
                        height: 4,
                      },
                      "&::-webkit-scrollbar-track": {
                        backgroundColor: "transparent",
                      },
                      "&::-webkit-scrollbar-thumb": {
                        backgroundColor: "rgba(0, 0, 0, 0.1)",
                        borderRadius: 2,
                      },
                    }}
                  >
                    {group.chips.map((chip, chipIdx) => {
                      const chipHasOutput = chip.output && chip.status === "completed";
                      const chipHasError = chip.status === "failed";
                      const isClickable = chipHasOutput || chipHasError;
                      const isSelected = selectedChipIndex === chipIdx;

                      return (
                        <Box
                          key={chipIdx}
                          onClick={() => {
                            if (isClickable) {
                              if (isSelected) {
                                onChipChange(null, rowKey);
                              } else {
                                onChipChange({ chipIndex: chipIdx }, rowKey);
                              }
                            }
                          }}
                          sx={{
                            display: "inline-flex",
                            alignItems: "center",
                            gap: 1,
                            px: 1.5,
                            py: 0.75,
                            borderRadius: "16px",
                            flexShrink: 0,
                            backgroundColor: isSelected
                              ? (chipHasError ? "rgba(211, 47, 47, 0.15)" : "rgba(76, 175, 80, 0.15)")
                              : chip.status === "completed"
                              ? "rgba(76, 175, 80, 0.08)"
                              : chip.status === "failed"
                              ? "rgba(211, 47, 47, 0.08)"
                              : "var(--dm-subtle, rgba(0, 0, 0, 0.04))",
                            border: isSelected
                              ? (chipHasError ? "1px solid rgba(211, 47, 47, 0.5)" : "1px solid rgba(76, 175, 80, 0.5)")
                              : chip.status === "completed"
                              ? "1px solid rgba(76, 175, 80, 0.3)"
                              : chip.status === "failed"
                              ? "1px solid rgba(211, 47, 47, 0.3)"
                              : "1px solid var(--dm-border, rgba(0, 0, 0, 0.1))",
                            fontFamily: "var(--font-oracle-sans), sans-serif",
                            fontSize: "0.8rem",
                            color: chip.status === "completed"
                              ? "#2e7d32"
                              : chip.status === "failed"
                              ? "#c62828"
                              : "var(--dm-muted, rgba(0, 0, 0, 0.6))",
                            transition: "all 0.2s ease",
                            cursor: isClickable ? "pointer" : "default",
                            userSelect: "none",
                            "&:hover": isClickable
                              ? {
                                  backgroundColor: chipHasError ? "rgba(211, 47, 47, 0.12)" : "rgba(76, 175, 80, 0.12)",
                                  transform: "scale(1.03)",
                                }
                              : {},
                          }}
                        >
                          <AnimatePresence mode="wait">
                            {chip.status === "completed" ? (
                              <motion.div
                                key="check"
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ duration: 0.2, ease: "easeOut" }}
                                style={{ display: "flex", alignItems: "center" }}
                              >
                                <Check size={14} />
                              </motion.div>
                            ) : chip.status === "failed" ? (
                              <motion.div
                                key="error"
                                initial={{ scale: 0, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ duration: 0.2, ease: "easeOut" }}
                                style={{ display: "flex", alignItems: "center" }}
                              >
                                <AlertTriangle size={14} />
                              </motion.div>
                            ) : (
                              <motion.div
                                key="loading"
                                style={{ display: "flex", alignItems: "center" }}
                              >
                                <CircularProgress size={14} sx={{ color: "var(--dm-muted, rgba(0, 0, 0, 0.4))" }} />
                              </motion.div>
                            )}
                          </AnimatePresence>
                          <span>{(() => {
                            const showCompleted = (chip.status === "completed" || chip.status === "failed") && chip.tool;
                            if (!showCompleted) return chip.label;
                            const baseName = formatToolName(chip.tool);
                            if (chip.tool === 'file_search') {
                              let queries = [];
                              try { queries = chip.arguments ? (JSON.parse(chip.arguments).queries || []) : []; } catch {}
                              const parts = [baseName];
                              if (queries.length === 1) {
                                const q = queries[0];
                                parts.push(`"${q.length > 40 ? q.slice(0, 40) + '…' : q}"`);
                              } else if (queries.length > 1) {
                                parts.push(`${queries.length} searches`);
                              }
                              if (typeof chip.chunkCount === 'number' && chip.chunkCount > 0) {
                                parts.push(`${chip.chunkCount} chunk${chip.chunkCount === 1 ? '' : 's'}`);
                              }
                              return parts.join(' · ');
                            }
                            return baseName;
                          })()}</span>
                          {isClickable && (
                            <ChevronDown
                              size={14}
                              style={{
                                transition: "transform 0.2s ease",
                                transform: isSelected ? "rotate(180deg)" : "rotate(0deg)",
                              }}
                            />
                          )}
                        </Box>
                      );
                    })}
                  </Box>

                  {/* Shared content panel */}
                  <Collapse in={selectedChip !== null}>
                    <Paper
                      elevation={0}
                      sx={{
                        mt: 1,
                        pt: 2,
                        px: 2,
                        pb: 0,
                        backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.02))",
                        border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.08))",
                        borderRadius: "20px",
                        position: "relative",
                      }}
                    >
                      <IconButton
                        onClick={() => onChipChange(null, rowKey)}
                        sx={{
                          position: "absolute",
                          top: -10,
                          right: -10,
                          padding: 0.5,
                          backgroundColor: "var(--dm-surface, white)",
                          border: "1px solid var(--dm-border, rgba(0, 0, 0, 0.1))",
                          color: "var(--dm-muted, rgba(0, 0, 0, 0.4))",
                          "&:hover": { backgroundColor: "var(--dm-subtle, rgba(0, 0, 0, 0.04))", color: "var(--dm-text, rgba(0, 0, 0, 0.6))" },
                        }}
                      >
                        <CloseIcon sx={{ fontSize: "14px" }} />
                      </IconButton>

                      {selectedChip && (
                        <Box
                          sx={{
                            display: "flex",
                            flexDirection: { xs: "column", md: "row" },
                            gap: 1.5,
                            mb: 2,
                          }}
                        >
                          {/* Arguments section */}
                          {selectedChip.arguments && (
                            <Box
                              sx={{
                                flex: 1,
                                minWidth: 0,
                                p: 1,
                                backgroundColor: "rgba(59, 130, 246, 0.06)",
                                borderRadius: 1,
                                maxHeight: "300px",
                                overflowY: "auto",
                                "& .w-rjv": { color: "var(--dm-text, inherit) !important" },
                                "& .w-rjv-line": { color: "var(--dm-text, inherit) !important" },
                              }}
                            >
                              <Typography sx={{ fontSize: "0.65rem", fontWeight: 500, mb: 0.5, textTransform: "uppercase", letterSpacing: "0.5px", color: "rgba(59, 130, 246, 0.6)" }}>
                                Arguments
                              </Typography>
                              <JsonView
                                value={typeof selectedChip.arguments === 'string'
                                  ? (() => { try { return JSON.parse(selectedChip.arguments); } catch { return { raw: selectedChip.arguments }; } })()
                                  : selectedChip.arguments}
                                collapsed={1}
                                displayDataTypes={false}
                                style={{
                                  "--w-rjv-color": "var(--dm-text, #212121)",
                                  "--w-rjv-key-string": "var(--dm-text, #212121)",
                                  "--w-rjv-background-color": "transparent",
                                  "--w-rjv-type-string-color": "#4caf50",
                                  "--w-rjv-type-int-color": "#1976d2",
                                  "--w-rjv-type-float-color": "#1976d2",
                                  "--w-rjv-type-boolean-color": "#f57c00",
                                  "--w-rjv-curlybraces-color": "var(--dm-muted, #5c5552)",
                                  "--w-rjv-brackets-color": "var(--dm-muted, #5c5552)",
                                  "--w-rjv-info-color": "var(--dm-muted, #5c5552)",
                                  "--w-rjv-ellipsis-color": "var(--dm-muted, #5c5552)",
                                  fontSize: "0.75rem",
                                  fontFamily: "monospace",
                                }}
                              />
                            </Box>
                          )}

                          {/* Output or Error section */}
                          <Box
                            sx={{
                              flex: selectedChip.arguments ? 1 : "auto",
                              minWidth: 0,
                              pt: 1,
                              px: 1,
                              pb: 1,
                              backgroundColor: hasError ? "rgba(211, 47, 47, 0.05)" : "var(--dm-subtle, rgba(0, 0, 0, 0.03))",
                              borderRadius: 1,
                              border: hasError ? "1px solid rgba(211, 47, 47, 0.2)" : "none",
                              maxHeight: hasError ? "none" : "300px",
                              overflowY: hasError ? "visible" : "auto",
                            }}
                          >
                            <Typography sx={{
                              fontSize: "0.65rem",
                              fontWeight: 500,
                              mb: 0.5,
                              textTransform: "uppercase",
                              letterSpacing: "0.5px",
                              color: hasError ? "rgba(211, 47, 47, 0.7)" : "var(--dm-muted, rgba(0, 0, 0, 0.4))"
                            }}>
                              {hasError ? "Error" : "Output"}
                            </Typography>
                            {hasError && (
                              <Box>
                                <Box sx={{
                                  fontSize: "0.8rem",
                                  color: "#c62828",
                                  fontFamily: "monospace",
                                  whiteSpace: "pre-wrap",
                                  wordBreak: "break-word",
                                  mb: 1,
                                }}>
                                  {selectedChip.error || selectedChip.output || "Tool execution failed"}
                                </Box>
                                {exchange.trace && (
                                  <Box
                                    onClick={() => setTraceDialogOpen(true)}
                                    sx={{
                                      display: "inline-flex",
                                      alignItems: "center",
                                      gap: 0.5,
                                      fontSize: "0.7rem",
                                      color: "var(--dm-muted, rgba(0,0,0,0.45))",
                                      cursor: "pointer",
                                      mb: selectedChip.output ? 1 : 0,
                                      "&:hover": { color: "#1976d2" },
                                    }}
                                  >
                                    <Terminal size={12} />
                                    View request trace
                                  </Box>
                                )}
                              </Box>
                            )}
                            {hasError && selectedChip.output && selectedChip.output !== selectedChip.error && (
                              <>
                                <Typography sx={{
                                  fontSize: "0.65rem",
                                  fontWeight: 500,
                                  mb: 0.5,
                                  textTransform: "uppercase",
                                  letterSpacing: "0.5px",
                                  color: "rgba(0, 0, 0, 0.4)"
                                }}>
                                  Output
                                </Typography>
                                <Box sx={{
                                  fontSize: "0.8rem",
                                  color: "inherit",
                                  wordBreak: "break-word",
                                  fontFamily: "monospace",
                                  whiteSpace: "pre-wrap",
                                }}>
                                  {selectedChip.output}
                                </Box>
                              </>
                            )}
                            {!hasError && (
                              <Box sx={{
                                fontSize: "0.8rem",
                                color: "var(--dm-text, inherit)",
                                wordBreak: "break-word",
                                "& p, & a, & li, & span": { fontFamily: "inherit" },
                              }}>
                                {audioBase64 ? (
                                  <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
                                    {outputMessage && (
                                      <Typography sx={{ fontSize: "0.8rem", color: "var(--dm-muted, rgba(0, 0, 0, 0.6))" }}>
                                        {outputMessage}
                                      </Typography>
                                    )}
                                    <audio
                                      controls
                                      src={`data:audio/mp3;base64,${audioBase64}`}
                                      style={{ width: "100%", height: 36, borderRadius: 8 }}
                                    />
                                  </Box>
                                ) : !selectedChip.output ? (
                                  <Typography sx={{ fontSize: "0.8rem", color: "var(--dm-muted, rgba(0, 0, 0, 0.4))", fontStyle: "italic" }}>
                                    No output returned
                                  </Typography>
                                ) : (() => {
                                  // Try to parse as JSON for nice rendering
                                  try {
                                    const parsed = JSON.parse(selectedChip.output);
                                    if (typeof parsed === 'object' && parsed !== null) {
                                      return (
                                        <JsonView
                                          value={parsed}
                                          collapsed={2}
                                          displayDataTypes={false}
                                          style={{
                                            "--w-rjv-color": "var(--dm-text, #212121)",
                                            "--w-rjv-key-string": "var(--dm-text, #212121)",
                                            "--w-rjv-background-color": "transparent",
                                            "--w-rjv-type-string-color": "#4caf50",
                                            "--w-rjv-type-int-color": "#1976d2",
                                            "--w-rjv-type-float-color": "#1976d2",
                                            "--w-rjv-type-boolean-color": "#f57c00",
                                            "--w-rjv-curlybraces-color": "var(--dm-muted, #5c5552)",
                                            "--w-rjv-brackets-color": "var(--dm-muted, #5c5552)",
                                            "--w-rjv-info-color": "var(--dm-muted, #5c5552)",
                                            "--w-rjv-ellipsis-color": "var(--dm-muted, #5c5552)",
                                            fontSize: "0.75rem",
                                            fontFamily: "monospace",
                                          }}
                                        />
                                      );
                                    }
                                    // Parsed to a primitive (string, number, boolean) — render as text
                                    return (
                                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                                        {String(parsed)}
                                      </ReactMarkdown>
                                    );
                                  } catch {
                                    // Not JSON, render as markdown
                                    return (
                                      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
                                        {selectedChip.output}
                                      </ReactMarkdown>
                                    );
                                  }
                                })()}
                              </Box>
                            )}
                          </Box>
                        </Box>
                      )}
                    </Paper>
                  </Collapse>

                  {/* Show audio players directly when chips have audio output */}
                  {directAudioList.length > 0 && directAudioList.map((audioBase64, audioIdx) => (
                    <Box key={audioIdx} sx={{ mt: 1.5, maxWidth: 400, overflow: "hidden" }}>
                      <motion.div
                        initial={{
                          clipPath: "inset(0 100% 0 0)",
                          opacity: 0,
                          x: -20
                        }}
                        animate={{
                          clipPath: "inset(0 0% 0 0)",
                          opacity: 1,
                          x: 0
                        }}
                        transition={{
                          clipPath: { duration: 0.5, ease: [0.65, 0, 0.35, 1] },
                          opacity: { duration: 0.3, delay: 0.1 + audioIdx * 0.15 },
                          x: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
                        }}
                      >
                        <audio
                          controls
                          src={`data:audio/mp3;base64,${audioBase64}`}
                          style={{
                            width: "100%",
                            height: 36,
                            borderRadius: 8
                          }}
                        />
                      </motion.div>
                    </Box>
                  ))}
                </Box>
              );
            })()}

            {group.type === "interactive" && (
              <Box sx={{ mt: 3, mb: 3 }}>
                <InteractiveChoice interactiveData={group.interactiveData} onChoiceSelect={onOptionSelect} />
              </Box>
            )}

            {group.type === "progress_tracker" && <ProgressTracker data={group.progressData} />}
            {/* data_table type removed - tables use WidgetTable via v1 widget system */}
            {group.type === "process_diagram" && <ProcessDiagram data={group.processData} />}
            {group.type === "supplier_card" && <SupplierCard data={group.supplierData} />}
            {group.type === "radar_chart" && <RadarChart data={group.radarData} title={group.radarData?.title} />}
            {group.type === "scatter_chart" && <ScatterChart data={group.scatterData} title={group.scatterData?.title} />}
            {group.type === "cost_benefit_chart" && (
              <CostBenefitChart data={group.costBenefitData} title={group.costBenefitData?.title} />
            )}
          </Box>
        ))}
        </Box>

        {/* Copy, PDF & Raw debug buttons */}
        <AnimatePresence>
        {groupedResponses.length > 0 && (!isLoading || !exchange.isLatest) && contentReady && (
          <motion.div
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.25, ease: "easeOut", delay: 0.4 }}
          >
          <Box
            className="copy-button"
            sx={{
              mt: -2,
              display: "flex",
              alignItems: "center",
              gap: 1.5,
              opacity: 0,
              transition: "opacity 0.2s ease",
            }}
          >
            <Tooltip title="Copy" placement="bottom">
              <IconButton
                onClick={() => onCopy(getCopyContent(exchange), `exchange-${exchange.id}`)}
                size="small"
                sx={{
                  color: "var(--dm-muted, rgba(0, 0, 0, 0.3))",
                  padding: 0,
                  "&:hover": { color: "var(--dm-text, rgba(0, 0, 0, 0.6))", backgroundColor: "transparent" },
                }}
              >
                {copiedId === `exchange-${exchange.id}` ? <Check size={16} /> : <Copy size={16} />}
              </IconButton>
            </Tooltip>
            <Tooltip title={showRaw ? "Hide raw" : "Show raw"} placement="bottom">
              <IconButton
                onClick={() => setShowRaw(prev => !prev)}
                size="small"
                sx={{
                  color: showRaw ? "var(--dm-text, rgba(0, 0, 0, 0.6))" : "var(--dm-muted, rgba(0, 0, 0, 0.3))",
                  padding: 0,
                  "&:hover": { color: "var(--dm-text, rgba(0, 0, 0, 0.6))", backgroundColor: "transparent" },
                }}
              >
                <Code size={16} />
              </IconButton>
            </Tooltip>
            {exchange.isLatest && onRetry && (
              <Tooltip title="Retry" placement="bottom">
                <IconButton
                  onClick={() => onRetry()}
                  size="small"
                  sx={{
                    color: "var(--dm-muted, rgba(0, 0, 0, 0.3))",
                    padding: 0,
                    "&:hover": { color: "var(--dm-text, rgba(0, 0, 0, 0.6))", backgroundColor: "transparent" },
                  }}
                >
                  <RotateCcw size={16} />
                </IconButton>
              </Tooltip>
            )}
          </Box>
          </motion.div>
        )}
        </AnimatePresence>

        {/* Raw debug view */}
        {showRaw && (
          <Box sx={{
            mt: 1,
            p: 1.5,
            backgroundColor: "var(--dm-subtle, #F8F8F7)",
            borderRadius: 1,
            border: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
            maxHeight: 300,
            overflow: "auto",
            position: "relative",
          }}>
            <IconButton
              size="small"
              onClick={() => onCopy(getRawContent(), `raw-${exchange.id}`)}
              sx={{
                position: "absolute",
                top: 6,
                right: 6,
                color: copiedId === `raw-${exchange.id}` ? "var(--dm-text, rgba(0,0,0,0.6))" : "var(--dm-muted, rgba(0,0,0,0.25))",
                padding: "3px",
                "&:hover": { color: "var(--dm-text, rgba(0,0,0,0.6))", backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.05))" },
              }}
            >
              {copiedId === `raw-${exchange.id}` ? <Check size={13} /> : <Copy size={13} />}
            </IconButton>
            <Typography
              component="pre"
              sx={{
                fontSize: "0.7rem",
                fontFamily: "monospace",
                whiteSpace: "pre-wrap",
                wordBreak: "break-all",
                color: "rgba(0,0,0,0.7)",
                m: 0,
              }}
            >
              {getRawContent()}
            </Typography>
          </Box>
        )}

        {/* Loading/Thinking indicator — single continuous element */}
        <AnimatePresence>
          {showIndicator && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, minHeight: 24 }}>
                <DotMatrixLoader size="medium" delay={!hasThinkingMessage ? 400 : 0} />
                <AnimatePresence>
                  {hasThinkingMessage && (
                    <motion.span
                      initial={{ opacity: 0, x: -5 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Typography
                        component="span"
                        sx={{
                          fontSize: "0.85rem",
                          color: "var(--dm-muted, rgba(0, 0, 0, 0.4))",
                          fontStyle: "italic",
                        }}
                      >
                        Thinking...
                      </Typography>
                    </motion.span>
                  )}
                </AnimatePresence>
              </Box>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      {/* Text preview dialog */}
      <Dialog
        open={Boolean(textDialogOpen)}
        onClose={() => setTextDialogOpen(null)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            maxHeight: "80vh",
            backgroundColor: "var(--dm-surface, #fff)",
          }
        }}
      >
        <DialogContent sx={{ p: 0 }}>
          {/* Header */}
          <Box sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            p: 2,
            pb: 1,
            borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
          }}>
            <Box>
              <Typography sx={{ fontWeight: 500, fontSize: "0.95rem", color: "var(--dm-text, rgba(0,0,0,0.8))" }}>
                Pasted content
              </Typography>
              <Typography sx={{ fontSize: "0.75rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", mt: 0.25 }}>
                {textDialogOpen?.content && (
                  <>
                    {(new Blob([textDialogOpen.content]).size / 1024).toFixed(2)} KB • {textDialogOpen.content.split('\n').length.toLocaleString()} lines
                  </>
                )}
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 0.5, mt: -0.5, mr: -0.5 }}>
              <CopyTextButton content={textDialogOpen?.content} />
              <IconButton size="small" onClick={() => setTextDialogOpen(null)} sx={{ color: "var(--dm-muted, inherit)" }}>
                <X size={18} />
              </IconButton>
            </Box>
          </Box>
          {/* Content */}
          <Box sx={{ p: 2, maxHeight: "60vh", overflow: "auto" }}>
            <Box
              sx={{
                backgroundColor: "var(--dm-subtle, rgba(0,0,0,0.04))",
                borderRadius: 1.5,
                p: 2,
              }}
            >
              <Typography
                component="pre"
                sx={{
                  fontFamily: "monospace",
                  fontSize: "0.8rem",
                  color: "var(--dm-text, rgba(0,0,0,0.7))",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  m: 0,
                  lineHeight: 1.5,
                }}
              >
                {textDialogOpen?.content}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Image preview dialog */}
      <Dialog
        open={Boolean(imageDialogOpen)}
        onClose={() => setImageDialogOpen(null)}
        maxWidth="md"
      >
        <DialogContent sx={{ p: 1 }}>
          {imageDialogOpen && (
            <img
              src={imageDialogOpen.preview}
              alt={imageDialogOpen.name || "Attached image"}
              style={{ maxWidth: "100%", maxHeight: "80vh", display: "block" }}
            />
          )}
        </DialogContent>
      </Dialog>
      {/* Request Trace Dialog */}
      <Dialog
        open={traceDialogOpen}
        onClose={() => setTraceDialogOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { backgroundColor: "var(--dm-surface, #fff)", borderRadius: 2 } }}
      >
        <DialogContent sx={{ p: 0 }}>
          {exchange.trace && (() => {
            const t = exchange.trace;
            const copyTrace = () => {
              const text = JSON.stringify(t, null, 2);
              navigator.clipboard.writeText(text);
            };
            return (
              <Box sx={{ fontFamily: "monospace", fontSize: "0.78rem" }}>
                {/* Header */}
                <Box sx={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  p: 2, borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.08))",
                }}>
                  <Typography sx={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--dm-text, #1a1a1a)" }}>
                    Request Trace
                  </Typography>
                  <Box sx={{ display: "flex", gap: 1 }}>
                    <Box
                      onClick={copyTrace}
                      sx={{
                        display: "flex", alignItems: "center", gap: 0.5, px: 1.5, py: 0.5,
                        borderRadius: 1, cursor: "pointer", fontSize: "0.72rem",
                        border: "1px solid var(--dm-border, rgba(0,0,0,0.12))",
                        color: "var(--dm-muted, rgba(0,0,0,0.5))",
                        "&:hover": { backgroundColor: "rgba(0,0,0,0.04)" },
                      }}
                    >
                      <Copy size={12} /> Copy JSON
                    </Box>
                    <IconButton size="small" onClick={() => setTraceDialogOpen(false)}>
                      <CloseIcon sx={{ fontSize: 18 }} />
                    </IconButton>
                  </Box>
                </Box>

                {/* Error banner */}
                {t.error && (
                  <Box sx={{
                    mx: 2, mt: 2, p: 1.5, borderRadius: 1,
                    backgroundColor: "rgba(211, 47, 47, 0.06)",
                    border: "1px solid rgba(211, 47, 47, 0.2)",
                    color: "#c62828", fontSize: "0.78rem", lineHeight: 1.5,
                  }}>
                    {t.error}
                  </Box>
                )}

                {/* Summary */}
                <Box sx={{ p: 2, display: "flex", flexWrap: "wrap", gap: 2, borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.06))" }}>
                  {[
                    ["Request ID", t.requestId],
                    ["OPC Request ID", t.opcRequestId],
                    ["Model", t.model],
                    ["Started", t.startedAt],
                    ["Duration", t.completion ? `${Math.round(t.completion.elapsed / 1000)}s` : "—"],
                    ["Status", t.completion?.status || "incomplete"],
                    ["Output Tokens", t.completion?.outputTokens],
                    ["Total Tokens", t.completion?.totalTokens],
                  ].filter(([, v]) => v).map(([label, value]) => (
                    <Box key={label} sx={{ minWidth: 120 }}>
                      <Typography sx={{ fontSize: "0.65rem", color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: "0.05em" }}>
                        {label}
                      </Typography>
                      <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-text, #1a1a1a)", wordBreak: "break-all" }}>
                        {value}
                      </Typography>
                    </Box>
                  ))}
                </Box>

                {/* Tools */}
                {Object.keys(t.tools).length > 0 && (
                  <Box sx={{ p: 2, borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.06))" }}>
                    <Typography sx={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: "0.05em", mb: 1 }}>
                      Tool Calls
                    </Typography>
                    {Object.entries(t.tools).map(([id, tool]) => (
                      <Box key={id} sx={{
                        display: "flex", alignItems: "center", gap: 1.5, py: 0.75,
                        borderBottom: "1px solid var(--dm-border, rgba(0,0,0,0.04))",
                      }}>
                        <Box sx={{
                          width: 8, height: 8, borderRadius: "50%", flexShrink: 0,
                          backgroundColor: tool.status === 'completed' ? '#4caf50'
                            : tool.status === 'failed' ? '#d32f2f'
                            : tool.status === 'orphaned' ? '#ff9800'
                            : '#9e9e9e',
                        }} />
                        <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-text, #1a1a1a)", fontWeight: 500 }}>
                          {tool.tool}
                        </Typography>
                        <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.4))" }}>
                          {tool.server}
                        </Typography>
                        <Box sx={{ flex: 1 }} />
                        <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.4))" }}>
                          {tool.startMs}ms{tool.endMs ? ` → ${tool.endMs}ms` : ""}
                        </Typography>
                        <Chip
                          label={tool.status}
                          size="small"
                          sx={{
                            height: 20, fontSize: "0.65rem",
                            backgroundColor: tool.status === 'completed' ? 'rgba(76,175,80,0.1)'
                              : tool.status === 'orphaned' ? 'rgba(255,152,0,0.1)'
                              : tool.status === 'failed' ? 'rgba(211,47,47,0.1)'
                              : 'rgba(0,0,0,0.05)',
                            color: tool.status === 'completed' ? '#2e7d32'
                              : tool.status === 'orphaned' ? '#e65100'
                              : tool.status === 'failed' ? '#c62828'
                              : 'inherit',
                          }}
                        />
                      </Box>
                    ))}
                  </Box>
                )}

                {/* Event Timeline */}
                <Box sx={{ p: 2 }}>
                  <Typography sx={{ fontSize: "0.72rem", fontWeight: 600, color: "var(--dm-muted, rgba(0,0,0,0.4))", textTransform: "uppercase", letterSpacing: "0.05em", mb: 1 }}>
                    Event Timeline
                  </Typography>
                  <Box sx={{ maxHeight: 300, overflow: "auto" }}>
                    {t.events.map((ev, i) => (
                      <Box key={i} sx={{ display: "flex", gap: 1.5, py: 0.3, fontSize: "0.72rem" }}>
                        <Typography sx={{ fontSize: "0.72rem", color: "var(--dm-muted, rgba(0,0,0,0.35))", minWidth: 50, textAlign: "right", fontFamily: "monospace" }}>
                          {ev.ts}ms
                        </Typography>
                        <Typography sx={{
                          fontSize: "0.72rem", fontFamily: "monospace",
                          color: ev.type.includes('orphan') || ev.type.includes('fail') || ev.type.includes('stall') || ev.type.includes('premature')
                            ? '#c62828' : "var(--dm-text, #333)",
                          fontWeight: ev.type.includes('orphan') || ev.type.includes('fail') ? 600 : 400,
                        }}>
                          {ev.type}
                          {ev.tool ? ` (${ev.tool})` : ""}
                          {ev.detail ? ` — ${ev.detail}` : ""}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              </Box>
            );
          })()}
        </DialogContent>
      </Dialog>
    </Box>
  );
});

export default ChatMessage;
