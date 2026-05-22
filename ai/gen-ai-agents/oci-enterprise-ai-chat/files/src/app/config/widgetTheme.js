/**
 * Widget Theme Configuration
 * Centralizes all widget styles in one place
 */

// ═══════════════════════════════════════════════════════════
// COLORS
// ═══════════════════════════════════════════════════════════

function getAccentColor() {
  if (typeof window === "undefined") return "#C74634";
  try {
    const stored = localStorage.getItem("uiSettings");
    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed.accentColor) return parsed.accentColor;
    }
  } catch {}
  return "#C74634";
}

export const COLORS = {
  // ═══ ORACLE REDWOOD CORPORATE PALETTE ═══

  // Primary — reads accent color from settings
  get primary() { return getAccentColor(); },

  // Secondary (Warm dark brown)
  secondary: "#312d2a",

  // Neutral
  neutral: {
    30: "#F1EFED",   // Light background
  },

  // Dark tones (warm brown instead of cold slate)
  slate: {
    150: "#312d2a",  // Dark (warm brown)
    100: "#5c5552",  // Medium
    50: "#C2D4D4",   // Light
  },

  // Pine (Tech/OCI)
  pine: {
    170: "#1E3224",  // Darkest
    140: "#35535C",  // Dark
    100: "#4C825C",  // Medium (success green)
    90: "#5C926D",   // Light
  },

  // Brand Yellow
  brandYellow: {
    base: "#F1B13F",
    170: "#F0CC72",
    160: "#E2C06B",
  },

  // Sienna (warning/accent)
  sienna: {
    60: "#DEB068",
    50: "#99C2A6",
  },

  // Status colors (using approved palette)
  success: "#4C825C",    // Pine 100
  warning: "#F1B13F",    // Brand Yellow
  error: "#C74634",      // Oracle Red
  info: "#35535C",       // Pine 140

  // Colors available for _c:
  palette: {
    r: "#C74634",   // Oracle Red
    g: "#4C825C",   // Pine 100 (success)
    b: "#35535C",   // Pine 140 (info)
    y: "#F1B13F",   // Brand Yellow
    o: "#DEB068",   // Sienna 60
    p: "#5c5552",   // Medium brown (neutral accent)
    w: "#F1EFED",   // Neutral 30
    k: "#312d2a",   // Dark brown
    gr: "#5c5552",  // Medium brown
  },

  // Backgrounds (use CSS vars for dark mode support)
  background: {
    get widget() { return "var(--dm-widget-bg, #FAFAF9)"; },
    hover: "rgba(49, 45, 42, 0.05)",
    input: "rgba(49, 45, 42, 0.03)",
    light: "#F1EFED",  // Neutral 30
  },

  // Text (use CSS vars for dark mode support)
  text: {
    get primary() { return "var(--dm-text, #312d2a)"; },
    get secondary() { return "var(--dm-muted, #5c5552)"; },
    muted: "#C2D4D4",       // Light
    inverse: "#F1EFED",     // Neutral 30
  },
};

// ═══════════════════════════════════════════════════════════
// TYPOGRAPHY
// ═══════════════════════════════════════════════════════════

export const TYPOGRAPHY = {
  fontFamily: "var(--font-oracle-sans), sans-serif",

  sizes: {
    xs: { title: "0.85rem", text: "0.75rem", icon: 16 },
    s: { title: "1rem", text: "0.85rem", icon: 20 },
    m: { title: "1.2rem", text: "1rem", icon: 24 },
    l: { title: "1.5rem", text: "1.1rem", icon: 32 },
    xl: { title: "2rem", text: "1.3rem", icon: 40 },
  },
};

// ═══════════════════════════════════════════════════════════
// SPACING & LAYOUT
// ═══════════════════════════════════════════════════════════

export const SPACING = {
  container: {
    xs: 1,
    s: 1.5,
    m: 2,
    l: 2.5,
    xl: 3,
  },
  gap: 1,
};

export const BORDER = {
  radius: 12, // px base
  radiusSmall: 8,
};

// ═══════════════════════════════════════════════════════════
// BUTTONS
// ═══════════════════════════════════════════════════════════

export const BUTTON = {
  padding: "10px 20px",
  borderRadius: 8,
  fontSize: "0.9rem",
  fontWeight: 500,

  // States
  disabledOpacity: 0.6,
  hoverScale: 1.02,
  tapScale: 0.98,
};

// ═══════════════════════════════════════════════════════════
// INPUTS
// ═══════════════════════════════════════════════════════════

export const INPUT = {
  backgroundColor: COLORS.background.input,
  hoverBackground: COLORS.background.hover,
  border: "none",
};

// ═══════════════════════════════════════════════════════════
// ANIMATIONS
// ═══════════════════════════════════════════════════════════

export const ANIMATION = {
  duration: {
    fast: 0.2,
    normal: 0.3,
    slow: 0.4,
  },
  ease: "easeOut",
  loadingDelay: 300, // ms before showing "clicked" state
};

// ═══════════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════════

/**
 * Get a color from the palette
 */
export function getColor(colorCode) {
  if (!colorCode) return null;
  if (colorCode.startsWith("#")) return colorCode;
  return COLORS.palette[colorCode] || null;
}

/**
 * Get size configuration
 */
export function getSize(sizeCode) {
  return {
    container: SPACING.container[sizeCode] || SPACING.container.m,
    ...TYPOGRAPHY.sizes[sizeCode] || TYPOGRAPHY.sizes.m,
  };
}

// Default export with everything
export default {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  BORDER,
  BUTTON,
  INPUT,
  ANIMATION,
  getColor,
  getSize,
};
