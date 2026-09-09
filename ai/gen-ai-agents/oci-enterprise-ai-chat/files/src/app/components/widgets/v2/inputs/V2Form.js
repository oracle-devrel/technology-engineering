"use client";
import { Box } from "@mui/material";
import { WidgetV2FormProvider } from "../WidgetV2FormContext";

export default function V2Form({ attrs = {}, children, onSubmit, disabled }) {
  return (
    <WidgetV2FormProvider onSubmit={onSubmit} disabled={disabled}>
      <Box sx={{ display: "flex", flexDirection: "column", gap: "12px", width: "100%" }}>
        {children}
      </Box>
    </WidgetV2FormProvider>
  );
}
