"use client";
import { Box } from "@mui/material";

export default function V2Col({ attrs = {}, children }) {
  return (
    <Box sx={{
      display: "flex",
      flexDirection: "column",
      gap: `${attrs.gap || 12}px`,
      alignItems: attrs.align || "stretch",
      justifyContent: attrs.justify || "flex-start",
      width: "100%",
      "& > *": {
        minWidth: 0,
      },
    }}>
      {children}
    </Box>
  );
}
