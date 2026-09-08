"use client";
import { useState } from "react";
import { Box, Tabs, Tab as MuiTab } from "@mui/material";
import React from "react";
import { COLORS } from "../../../../config/widgetTheme";

export function V2Tab({ attrs = {}, children }) {
  // V2Tab is rendered by V2Tabs — just returns children when active
  return <Box sx={{ pt: 2 }}>{children}</Box>;
}

export default function V2Tabs({ attrs = {}, children, node }) {
  const [activeTab, setActiveTab] = useState(0);

  // Get tab children from the node tree (not React children, which are already rendered)
  const tabNodes = node?.children?.filter(c => typeof c !== 'string' && c.tag === 'tab') || [];
  const tabChildren = React.Children.toArray(children).filter(c => c?.type === V2Tab);

  return (
    <Box sx={{ width: "100%" }}>
      <Tabs
        value={Math.min(activeTab, Math.max(tabChildren.length - 1, 0))}
        onChange={(_, v) => setActiveTab(v)}
        sx={{
          minHeight: 36,
          borderBottom: "1px solid rgba(0,0,0,0.08)",
          "& .MuiTabs-indicator": { backgroundColor: COLORS.primary, height: 2 },
          "& .MuiTab-root": {
            minHeight: 36,
            textTransform: "none",
            fontSize: "0.85rem",
            fontWeight: 500,
            color: COLORS.text.secondary,
            "&.Mui-selected": { color: COLORS.text.primary, fontWeight: 600 },
          },
        }}
      >
        {tabNodes.map((tabNode, i) => (
          <MuiTab key={i} label={tabNode.attrs?.label || `Tab ${i + 1}`} />
        ))}
      </Tabs>
      {tabChildren[activeTab] || null}
    </Box>
  );
}
