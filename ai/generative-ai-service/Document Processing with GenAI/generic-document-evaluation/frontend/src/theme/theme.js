"use client";
import { createTheme } from "@mui/material/styles";
import { palette } from "./palette";

const theme = createTheme({
  palette,
  typography: {
    fontFamily: "var(--font-roboto)",
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 20, // You can adjust this value for more or less rounding
        },
      },
    },
  },
});

export default theme;
