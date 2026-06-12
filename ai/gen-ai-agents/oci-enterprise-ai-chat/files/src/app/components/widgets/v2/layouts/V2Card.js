"use client";
import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { getColor, COLORS, BORDER } from "../../../../config/widgetTheme";

export default function V2Card({ attrs = {}, children }) {
  const isDark = attrs.dark === "true" || attrs.dark === "1";
  const bgColor = isDark
    ? COLORS.slate[150]
    : (getColor(attrs.bg) || COLORS.background.widget);
  const titleColor = isDark ? COLORS.text.inverse : COLORS.text.primary;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
    >
      <Box sx={{
        p: `${attrs.padding || 16}px`,
        borderRadius: `${BORDER.radius}px`,
        backgroundColor: bgColor,
        border: isDark ? "none" : (attrs.border !== "false" ? "1px solid rgba(0,0,0,0.08)" : "none"),
        boxShadow: attrs.shadow === "true" ? "0 2px 8px rgba(0,0,0,0.06)" : "none",
        width: "fit-content",
        minWidth: 280,
        maxWidth: "100%",
        boxSizing: "border-box",
        color: isDark ? COLORS.text.inverse : "inherit",
        "& .MuiTypography-root": isDark ? { color: "rgba(255,255,255,0.85)" } : {},
      }}>
        {attrs.title && (
          <Typography sx={{
            fontSize: "1rem",
            fontWeight: 600,
            color: titleColor,
            mb: 1.5,
            fontFamily: "inherit",
          }}>
            {attrs.title}
          </Typography>
        )}
        <Box sx={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {children}
        </Box>
      </Box>
    </motion.div>
  );
}
