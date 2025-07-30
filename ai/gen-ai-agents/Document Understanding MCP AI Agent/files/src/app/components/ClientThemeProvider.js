"use client";
import { CssBaseline, ThemeProvider } from "@mui/material";
import { ProjectProvider } from "../contexts/ProjectsContext";
import theme from "../theme/theme";

export default function ClientThemeProvider({ children }) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ProjectProvider>{children}</ProjectProvider>
    </ThemeProvider>
  );
}
