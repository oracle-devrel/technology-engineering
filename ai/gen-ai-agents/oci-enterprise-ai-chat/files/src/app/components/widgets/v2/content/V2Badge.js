"use client";
import { Box, Typography } from "@mui/material";
import { getColor, COLORS } from "../../../../config/widgetTheme";

export default function V2Badge({ attrs = {} }) {
  const color = getColor(attrs.color) || COLORS.primary;
  return (
    <Box
      component="span"
      sx={{
        display: "inline-flex",
        px: 1.5,
        py: 0.25,
        borderRadius: 10,
        backgroundColor: `${color}15`,
        border: `1px solid ${color}30`,
      }}
    >
      <Typography sx={{ fontSize: "0.75rem", fontWeight: 600, color, fontFamily: "inherit" }}>
        {attrs.text || attrs.label}
      </Typography>
    </Box>
  );
}
