"use client";
import { useState } from "react";
import { Box, TextField, Typography } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Time({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "time";
  const [localValue, setLocalValue] = useState(attrs.value || attrs.default || "");

  const value = hasFormCtx ? (form.state[key] ?? (attrs.value || attrs.default || "")) : localValue;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalValue(v);

  return (
    <Box>
      {attrs.label && (
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500, color: COLORS.text.secondary, mb: 0.5, fontFamily: "inherit" }}>
          {attrs.label}
        </Typography>
      )}
      <TextField
        type="time"
        value={value}
        onChange={(e) => update(key, e.target.value)}
        disabled={disabled}
        size="small"
        fullWidth
        sx={{ "& .MuiOutlinedInput-root": { fontSize: "0.85rem", backgroundColor: "rgba(0,0,0,0.02)" } }}
      />
    </Box>
  );
}
