/**
 * Dark mode CSS overrides for MUI components.
 * Apply to a container's `sx` prop to theme all children.
 */

export const DARK_BG = "#1a1a1a";
export const DARK_SURFACE = "#242424";
export const DARK_TEXT = "#e5e5e5";
export const DARK_MUTED = "rgba(255,255,255,0.5)";
export const DARK_BORDER = "rgba(255,255,255,0.10)";
export const DARK_SUBTLE = "rgba(255,255,255,0.05)";

export const darkCssVars = {
  "--dm-bg": DARK_BG,
  "--dm-surface": DARK_SURFACE,
  "--dm-widget-bg": "#2a2a2a",
  "--dm-text": DARK_TEXT,
  "--dm-muted": DARK_MUTED,
  "--dm-border": DARK_BORDER,
  "--dm-subtle": DARK_SUBTLE,
  "--dm-overlay-opacity": "1",
};

export const lightCssVars = {
  "--dm-bg": "#ffffff",
  "--dm-surface": "#ffffff",
  "--dm-widget-bg": "#FAFAF9",
  "--dm-text": "#1a1a1a",
  "--dm-muted": "rgba(0,0,0,0.5)",
  "--dm-border": "rgba(0,0,0,0.08)",
  "--dm-subtle": "rgba(0,0,0,0.03)",
  "--dm-overlay-opacity": "0",
};

export const darkModeOverrides = {
  color: DARK_TEXT,

  // Typography
  "& .MuiTypography-root": { color: "inherit" },

  // Inputs & text fields
  "& .MuiInputBase-root": { color: DARK_TEXT },
  "& .MuiOutlinedInput-root": { backgroundColor: DARK_SUBTLE },
  "& .MuiOutlinedInput-notchedOutline": { borderColor: `${DARK_BORDER} !important` },
  "& .MuiInputBase-root:hover .MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.25) !important" },
  "& .MuiInputBase-root.Mui-focused .MuiOutlinedInput-notchedOutline": { borderColor: "rgba(255,255,255,0.4) !important" },
  "& .MuiFormHelperText-root": { color: "rgba(255,255,255,0.35)" },
  "& .MuiInputLabel-root": { color: DARK_MUTED },
  "& .MuiSelect-icon": { color: DARK_MUTED },

  // Chips
  "& .MuiChip-root": { borderColor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.6)" },
  "& .MuiChip-outlined": { borderColor: "rgba(255,255,255,0.15)" },

  // Dividers
  "& .MuiDivider-root": { borderColor: "rgba(255,255,255,0.08)" },

  // Paper / Cards
  "& .MuiPaper-root": { backgroundColor: DARK_SURFACE, color: DARK_TEXT },

  // Tabs
  "& .MuiTab-root": { color: DARK_MUTED },
  "& .MuiTab-root.Mui-selected": { color: DARK_TEXT },
  "& .MuiTabs-indicator": { backgroundColor: DARK_TEXT },

  // Buttons & Icons
  "& .MuiIconButton-root": { color: DARK_MUTED },
  "& .MuiButton-outlined": { borderColor: "rgba(255,255,255,0.15)", color: DARK_TEXT },

  // Switch — restyle only the unchecked track; reassert green for checked (iOS-style)
  "& .MuiSwitch-switchBase:not(.Mui-checked) + .MuiSwitch-track": {
    backgroundColor: "rgba(255,255,255,0.15) !important",
  },
  "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
    backgroundColor: "#65C466 !important",
    opacity: "1 !important",
  },

  // Links
  "& a": { color: "rgba(255,255,255,0.7)" },

  // Tooltips
  "& .MuiTooltip-tooltip": { backgroundColor: "#333" },

  // Borders in custom components (Box with border)
  "& [style*='border']": { borderColor: DARK_BORDER },

  // Scrollbars — Firefox
  scrollbarColor: "rgba(255,255,255,0.18) transparent",
  "& *": { scrollbarColor: "rgba(255,255,255,0.18) transparent" },
  // Scrollbars — WebKit (own element + descendants, including textarea)
  "&::-webkit-scrollbar, & ::-webkit-scrollbar": { width: "10px", height: "10px" },
  "&::-webkit-scrollbar-track, & ::-webkit-scrollbar-track": { background: "transparent" },
  "&::-webkit-scrollbar-thumb, & ::-webkit-scrollbar-thumb": {
    background: "rgba(255,255,255,0.15)",
    borderRadius: "6px",
    border: "2px solid transparent",
    backgroundClip: "padding-box",
  },
  "&::-webkit-scrollbar-thumb:hover, & ::-webkit-scrollbar-thumb:hover": {
    background: "rgba(255,255,255,0.28)",
    backgroundClip: "padding-box",
    border: "2px solid transparent",
  },
  "&::-webkit-scrollbar-corner, & ::-webkit-scrollbar-corner": { background: "transparent" },

  // Lists (Menu items)
  "& .MuiMenuItem-root": { color: DARK_TEXT },
  "& .MuiListSubheader-root": { color: DARK_MUTED, backgroundColor: DARK_BG },
  "& .MuiMenu-paper": { backgroundColor: `${DARK_SURFACE} !important` },

  // Markdown / code blocks
  "& pre, & code": { backgroundColor: `${DARK_SURFACE} !important`, color: DARK_TEXT },
  "& table th": { backgroundColor: `${DARK_SURFACE} !important`, color: DARK_TEXT },
  "& table td": { borderColor: `${DARK_BORDER} !important` },
  "& table th": { borderColor: `${DARK_BORDER} !important` },
  "& blockquote": { borderLeftColor: DARK_BORDER, color: DARK_MUTED },

  // Badge
  "& .MuiBadge-badge": { color: "#fff" },

  // Accordion
  "& .MuiAccordion-root": { backgroundColor: DARK_SURFACE, color: DARK_TEXT },

  // Alert
  "& .MuiAlert-root": { backgroundColor: DARK_SURFACE },

  // Skeleton
  "& .MuiSkeleton-root": { backgroundColor: "rgba(255,255,255,0.08) !important" },

};

/**
 * Use this function in component sx to adapt a hardcoded background.
 * Example: backgroundColor: darkAware(isDarkBg, "#fff")
 */
export function darkAware(isDark, lightValue, darkValue) {
  return isDark ? (darkValue || DARK_SURFACE) : lightValue;
}
