export const lightPalette = {
  mode: "light",
  primary: { main: "#007AFF" }, // iOS Blue
  secondary: { main: "#34C759" }, // iOS Green
  error: { main: "#FF453A" }, // iOS Red
  warning: {
    main: "#FF9500", // iOS Orange
    light: "#FFD60A", // Light yellow/gold
  },
  info: {
    main: "#5AC8FA", // iOS Light Blue
    dark: "#0A84FF", // Darker blue
  },
  success: { main: "#34C759" }, // iOS Green
  background: {
    default: "#FFFFFF", // White background
    paper: "#F8F9FA", // Light grey background
    elevated: "#F0F0F0", // Elevated light background
    dark: "#000000", // Dark overlay
  },
  text: {
    primary: "#000000", // Black text
    secondary: "#666666", // Grey text
    disabled: "#999999", // Disabled text
    tertiary: "#888888", // Tertiary text
  },
  common: {
    white: "#FFFFFF",
    black: "#000000",
  },
  grey: {
    50: "#FAFAFA",
    100: "#F5F5F5",
    200: "#EEEEEE",
    300: "#E0E0E0",
    400: "#BDBDBD",
    500: "#9E9E9E",
    600: "#757575",
    700: "#616161",
    800: "#424242",
    900: "#212121",
  },
  accent: {
    cyan: "#06b6d4",
    cyanLight: "#22d3ee",
    purple: "#8b5cf6",
    gold: "#fbbf24",
    yellow: "#eab308",
  },
  divider: "rgba(0, 0, 0, 0.12)",
};

export const darkPalette = {
  mode: "dark",
  primary: { main: "#0A84FF" }, // Brighter blue for dark mode
  secondary: { main: "#32D74B" }, // Brighter green for dark mode
  error: { main: "#FF453A" }, // iOS Red
  warning: {
    main: "#FF9F0A", // iOS Orange
    light: "#FFD60A", // Light yellow/gold
  },
  info: {
    main: "#64D2FF", // Brighter info blue
    dark: "#0A84FF", // Darker blue
  },
  success: { main: "#32D74B" }, // Brighter green for dark mode
  background: {
    default: "#000000", // Black background
    paper: "#1C1C1E", // Dark grey background
    elevated: "#2C2C2E", // Elevated dark background
    dark: "#000000", // Pure black
  },
  text: {
    primary: "#FFFFFF", // White text
    secondary: "#ABABAB", // Light grey text
    disabled: "#666666", // Disabled text
    tertiary: "#8E8E93", // Tertiary text
  },
  common: {
    white: "#FFFFFF",
    black: "#000000",
  },
  grey: {
    50: "#FAFAFA",
    100: "#F5F5F5",
    200: "#EEEEEE",
    300: "#E0E0E0",
    400: "#8E8E93",
    500: "#636366",
    600: "#48484A",
    700: "#3A3A3C",
    800: "#2C2C2E",
    900: "#1C1C1E",
  },
  accent: {
    cyan: "#5AC8FA",
    cyanLight: "#64D2FF",
    purple: "#BF5AF2",
    gold: "#FFD60A",
    yellow: "#FFD60A",
  },
  divider: "rgba(255, 255, 255, 0.12)",
};

// Export the current palette (change this to switch themes)
export const palette = lightPalette;
