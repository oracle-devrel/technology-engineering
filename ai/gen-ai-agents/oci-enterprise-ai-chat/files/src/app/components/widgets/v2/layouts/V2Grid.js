"use client";
import { Box } from "@mui/material";

export default function V2Grid({ attrs = {}, children }) {
  const cols = parseInt(attrs.cols, 10) || 3;
  return (
    <Box sx={{
      display: "grid",
      gridTemplateColumns: {
        xs: cols > 2 ? "1fr" : `repeat(${cols}, 1fr)`,
        sm: `repeat(${Math.min(cols, 2)}, 1fr)`,
        md: `repeat(${cols}, 1fr)`,
      },
      gap: `${attrs.gap || 16}px`,
      width: "100%",
      minWidth: 0,
      "& > *": { minWidth: 0 },
    }}>
      {children}
    </Box>
  );
}
