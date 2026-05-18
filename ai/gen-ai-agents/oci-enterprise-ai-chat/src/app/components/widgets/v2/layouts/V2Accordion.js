"use client";
import { useState } from "react";
import { Box, Collapse, Typography } from "@mui/material";
import { ChevronDown } from "lucide-react";
import { COLORS } from "../../../../config/widgetTheme";

export function V2Section({ attrs = {}, children }) {
  const [open, setOpen] = useState(attrs.open === "true");

  return (
    <Box sx={{ borderBottom: "1px solid rgba(0,0,0,0.06)" }}>
      <Box
        onClick={() => setOpen(!open)}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 1.5,
          cursor: "pointer",
          "&:hover": { backgroundColor: "rgba(0,0,0,0.02)" },
        }}
      >
        <Typography sx={{ fontSize: "0.9rem", fontWeight: 600, color: "inherit", fontFamily: "inherit" }}>
          {attrs.title || "Section"}
        </Typography>
        <ChevronDown
          size={18}
          style={{
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s ease",
            color: "inherit",
          }}
        />
      </Box>
      <Collapse in={open}>
        <Box sx={{ px: 1.5, pb: 1.5 }}>
          {children}
        </Box>
      </Collapse>
    </Box>
  );
}

export default function V2Accordion({ attrs = {}, children }) {
  return (
    <Box sx={{
      border: "1px solid rgba(0,0,0,0.08)",
      borderRadius: 2,
      overflow: "hidden",
      width: "100%",
    }}>
      {children}
    </Box>
  );
}
