"use client";
import { Box } from "@mui/material";

export default function V2Row({ attrs = {}, children }) {
  const useGrid = attrs.wrap !== "false";

  if (useGrid) {
    return (
      <Box sx={{
        display: "grid",
        // Cards inside a row fill their grid cell and can shrink (V2Card is
        // width:100% / minWidth:0), so a small min keeps two cards side by side at
        // typical chat widths and only wraps to one column when truly narrow.
        gridTemplateColumns: `repeat(auto-fit, minmax(${attrs.min || 140}px, 1fr))`,
        gap: `${attrs.gap || 16}px`,
        alignItems: attrs.align || "stretch",
        width: "100%",
        minWidth: 0,
      }}>
        {children}
      </Box>
    );
  }

  // nowrap mode — plain flex, no wrapping
  return (
    <Box sx={{
      display: "flex",
      flexDirection: "row",
      gap: `${attrs.gap || 16}px`,
      alignItems: attrs.align || "stretch",
      justifyContent: attrs.justify || "flex-start",
      flexWrap: "nowrap",
      width: "100%",
      minWidth: 0,
      "& > *": {
        flex: 1,
        minWidth: 0,
      },
    }}>
      {children}
    </Box>
  );
}
