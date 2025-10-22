"use client";

import { createTheme, ThemeProvider } from "@mui/material/styles";
import { useMemo } from "react";
import { APP_CONFIG } from "../config/app";

export default function DynamicThemeProvider({
  children,
  projectConfig = null,
}) {
  const theme = useMemo(() => {
    const baseTheme = createTheme({
      palette: {
        mode: "light",
        primary: {
          main: projectConfig?.mainColor || APP_CONFIG.defaults.color,
          light: projectConfig?.mainColor || APP_CONFIG.defaults.color,
          dark: projectConfig?.mainColor || APP_CONFIG.defaults.color,
          contrastText: "#FFFFFF",
        },
        secondary: {
          main: "#3FB37F",
          light: "#52C08D",
          dark: "#36A071",
          contrastText: "#EDEBE6",
        },
        background: {
          default: "#F5F5F5",
          paper: "#FFFFFF",
        },
      },
      shape: {
        borderRadius: 14,
      },
    });

    return baseTheme;
  }, [projectConfig]);

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
}
