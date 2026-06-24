"use client";

import { createTheme, ThemeProvider } from "@mui/material/styles";
import { useMemo } from "react";

export default function DynamicThemeProvider({
  children,
  projectConfig = null,
}) {
  const theme = useMemo(() => {
    const baseTheme = createTheme({
      palette: {
        mode: "light",
        primary: {
          main: projectConfig?.mainColor || "#007AFF",
          light: projectConfig?.mainColor || "#007AFF",
          dark: projectConfig?.mainColor || "#007AFF",
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
