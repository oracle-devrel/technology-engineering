"use client";

import { Box, Tabs, Tab, useMediaQuery, useTheme } from "@mui/material";

export default function VerticalTabs({
  activeTab,
  onTabChange,
  tabs,
  tabsWidth = "200px",
  footer,
  children
}) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));

  const tabsEl = (
    <Tabs
      orientation={isMobile ? "horizontal" : "vertical"}
      value={activeTab}
      onChange={(e, newValue) => onTabChange(newValue)}
      variant={isMobile ? "fullWidth" : "standard"}
      sx={{
        ...(isMobile
          ? { borderBottom: 1, borderColor: "divider" }
          : { minWidth: tabsWidth }),
        ".MuiTab-root": {
          textAlign: isMobile ? "center" : "right",
          alignItems: isMobile ? "center" : "flex-end",
          fontWeight: 300,
          fontSize: "0.95rem",
          color: "var(--dm-muted, rgba(0, 0, 0, 0.6))",
          minHeight: isMobile ? 42 : 48,
          "&.Mui-selected": {
            color: "var(--dm-text, #1a1a1a)",
            fontWeight: 400,
          },
        },
      }}
    >
      {tabs.map((tab, index) => (
        <Tab key={index} label={tab} />
      ))}
    </Tabs>
  );

  return (
    <Box sx={{ display: "flex", flexDirection: isMobile ? "column" : "row", gap: isMobile ? 2 : 3, flex: 1, minHeight: 0 }}>
      {isMobile ? tabsEl : (
        <Box sx={{ display: "flex", flexDirection: "column", minWidth: tabsWidth, flexShrink: 0, borderRight: 1, borderColor: "divider" }}>
          {tabsEl}
          {footer && (
            <Box sx={{ mt: "auto", display: "flex", justifyContent: "flex-end", pr: 2, pb: 2 }}>
              {footer}
            </Box>
          )}
        </Box>
      )}

      {/* Tab Content */}
      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflow: "auto",
          pl: isMobile ? 0 : 1,
          pr: isMobile ? 0 : 1,
          pb: 4,
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
