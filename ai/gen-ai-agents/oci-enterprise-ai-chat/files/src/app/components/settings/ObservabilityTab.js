"use client";

import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { ExternalLink, Activity, BarChart3, Plug, ArrowDown, GitFork } from "lucide-react";

const DESTINATIONS = [
  {
    icon: BarChart3,
    title: "OCI LangFuse",
    color: "#4C825C",
    tag: "Managed",
    desc: "Zero-config tracing. Every LLM call, tool invocation, and token counted automatically.",
    bullets: ["Input / Output", "Token usage", "Latency", "Tool calls", "Reasoning"],
    links: [],
  },
  {
    icon: Plug,
    title: "Client BYO",
    color: "#35535C",
    tag: "Flexible",
    desc: "Bring your own stack. We export OpenTelemetry — you choose where it lands.",
    links: [
      { label: "LangFuse Cloud", url: "https://cloud.langfuse.com/" },
      { label: "Datadog", url: "https://www.datadoghq.com/" },
      { label: "Splunk", url: "https://www.splunk.com/" },
      { label: "Grafana", url: "https://grafana.com/" },
      { label: "OCI Monitoring", url: "https://cloud.oracle.com/monitoring" },
    ],
  },
];

export default function ObservabilityTab() {
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Typography
        variant="h5"
        sx={{ fontWeight: 400, color: "var(--dm-text, #1a1a1a)", mb: 3, fontSize: "1.1rem" }}
      >
        Observability
      </Typography>

      {/* Horizontal pipeline */}
      <Box sx={{
        display: "flex",
        alignItems: "center",
        gap: 0,
        mb: 3,
        px: 1,
      }}>
        {/* Source chip */}
        <Typography sx={{
          px: 2.5, py: 1, borderRadius: "10px",
          background: "linear-gradient(135deg, #C74634, #a33828)",
          color: "#fff", fontSize: "0.82rem", fontWeight: 600,
          whiteSpace: "nowrap",
          boxShadow: "0 1px 4px rgba(199,70,52,0.15)",
          flexShrink: 0,
        }}>
          OCI Responses API
        </Typography>

        {/* Arrow */}
        <Box sx={{ display: "flex", alignItems: "center", px: 1, flexShrink: 0 }}>
          <Box sx={{ width: 24, height: "1.5px", backgroundColor: "var(--dm-muted, rgba(0,0,0,0.15))" }} />
          <ArrowDown size={12} color="var(--dm-muted, rgba(0,0,0,0.2))" style={{ transform: "rotate(-90deg)", marginLeft: -3 }} />
        </Box>

        {/* OTel chip */}
        <Box sx={{
          px: 2.5, py: 1, borderRadius: "10px",
          backgroundColor: "#312d2a",
          display: "flex", alignItems: "center", gap: 0.75,
          flexShrink: 0,
        }}>
          <Activity size={12} color="#f5f0eb" />
          <Typography sx={{ fontSize: "0.82rem", fontWeight: 600, color: "#f5f0eb" }}>
            OpenTelemetry
          </Typography>
        </Box>

        {/* Fork arrow */}
        <Box sx={{ display: "flex", alignItems: "center", px: 1, flexShrink: 0 }}>
          <Box sx={{ width: 16, height: "1.5px", backgroundColor: "var(--dm-muted, rgba(0,0,0,0.15))" }} />
          <GitFork size={14} color="var(--dm-muted, rgba(0,0,0,0.2))" style={{ transform: "rotate(90deg)", marginLeft: -2 }} />
        </Box>

        {/* Destination labels */}
        <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
          {DESTINATIONS.map((opt, i) => (
            <Box key={i} sx={{ display: "flex", alignItems: "center", gap: 0.75 }}>
              <Box sx={{ width: 7, height: 7, borderRadius: "50%", backgroundColor: opt.color, flexShrink: 0 }} />
              <Typography sx={{ fontSize: "0.8rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", fontWeight: 500 }}>
                {opt.title}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>

      {/* Destination cards */}
      <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", sm: "1fr 1fr" }, gap: 2 }}>
        {DESTINATIONS.map((opt, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.15 + i * 0.08 }}
          >
            <Box sx={{
              p: 2.5, borderRadius: "14px",
              backgroundColor: "var(--dm-surface)",
              border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
              boxShadow: "0 1px 3px rgba(0,0,0,0.03)",
              transition: "all 0.2s ease",
              "&:hover": {
                boxShadow: "0 3px 10px rgba(0,0,0,0.05)",
                borderColor: `${opt.color}30`,
              },
              height: "100%",
              display: "flex",
              flexDirection: "column",
            }}>
              {/* Card header */}
              <Box sx={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", mb: 1.5 }}>
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.25 }}>
                  <Box sx={{
                    width: 34, height: 34, borderRadius: "9px",
                    backgroundColor: `${opt.color}10`,
                    border: `1px solid ${opt.color}1a`,
                    display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
                  }}>
                    <opt.icon size={16} style={{ color: opt.color }} />
                  </Box>
                  <Typography sx={{ fontSize: "0.92rem", fontWeight: 600, color: "var(--dm-text, #1a1a1a)" }}>
                    {opt.title}
                  </Typography>
                </Box>
                <Typography sx={{
                  fontSize: "0.6rem", fontWeight: 600, color: opt.color,
                  backgroundColor: `${opt.color}0c`,
                  border: `1px solid ${opt.color}18`,
                  px: 0.8, py: 0.2, borderRadius: "5px",
                  textTransform: "uppercase", letterSpacing: "0.04em",
                }}>
                  {opt.tag}
                </Typography>
              </Box>

              {/* Description */}
              <Typography sx={{ fontSize: "0.78rem", color: "var(--dm-muted, rgba(0,0,0,0.5))", lineHeight: 1.6, mb: 1.5 }}>
                {opt.desc}
              </Typography>

              {/* Bullets as inline chips */}
              {opt.bullets && (
                <Box sx={{ display: "flex", gap: 0.6, flexWrap: "wrap", mt: "auto" }}>
                  {opt.bullets.map((b, j) => (
                    <Typography key={j} sx={{
                      fontSize: "0.66rem", fontWeight: 500,
                      color: opt.color,
                      backgroundColor: `${opt.color}08`,
                      border: `1px solid ${opt.color}15`,
                      px: 0.9, py: 0.25, borderRadius: "5px",
                    }}>
                      {b}
                    </Typography>
                  ))}
                </Box>
              )}

              {/* Integration links */}
              {opt.links.length > 0 && (
                <Box sx={{ display: "flex", gap: 0.6, flexWrap: "wrap", mt: "auto" }}>
                  {opt.links.map((link, j) => (
                    <Typography
                      key={j}
                      component="span"
                      onClick={() => window.open(link.url, "_blank")}
                      sx={{
                        display: "inline-flex", alignItems: "center", gap: 0.4,
                        px: 1, py: 0.35, borderRadius: "6px",
                        backgroundColor: "rgba(0,0,0,0.025)", border: "1px solid var(--dm-border, rgba(0,0,0,0.06))",
                        cursor: "pointer", fontSize: "0.68rem", fontWeight: 500, color: "var(--dm-muted, rgba(0,0,0,0.5))",
                        transition: "all 0.15s ease",
                        "&:hover": {
                          backgroundColor: `${opt.color}08`,
                          borderColor: `${opt.color}20`,
                          color: opt.color,
                        },
                      }}
                    >
                      {link.label}
                      <ExternalLink size={8} />
                    </Typography>
                  ))}
                </Box>
              )}
            </Box>
          </motion.div>
        ))}
      </Box>
    </motion.div>
  );
}
