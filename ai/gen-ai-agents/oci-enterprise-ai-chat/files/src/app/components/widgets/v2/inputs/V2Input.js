"use client";
import { useState } from "react";
import { TextField, Typography, Box } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Input({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "input";

  // Local state fallback when not inside a <form> context
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
        value={value}
        onChange={(e) => update(key, e.target.value)}
        placeholder={attrs.placeholder || ""}
        disabled={disabled}
        size="small"
        fullWidth
        type={attrs.type || "text"}
        multiline={!!attrs.multiline}
        minRows={attrs.multiline ? Number(attrs.rows) || 3 : undefined}
        maxRows={attrs.multiline ? Number(attrs.maxrows) || 10 : undefined}
        sx={{
          "& .MuiOutlinedInput-root": {
            fontSize: "0.85rem",
            backgroundColor: "rgba(0,0,0,0.02)",
          },
        }}
      />
    </Box>
  );
}
