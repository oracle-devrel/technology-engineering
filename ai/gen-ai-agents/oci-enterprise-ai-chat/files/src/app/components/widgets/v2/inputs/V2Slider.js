"use client";
import { useState } from "react";
import { Box, Slider, Typography } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Slider({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "slider";
  const min = parseInt(attrs.min) || 0;
  const max = parseInt(attrs.max) || 100;
  const step = parseInt(attrs.step) || 1;
  const defaultValue = parseInt(attrs.value || attrs.default) || min;
  const [localValue, setLocalValue] = useState(defaultValue);

  const value = hasFormCtx ? (form.state[key] ?? defaultValue) : localValue;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalValue(v);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 0.5 }}>
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500, color: COLORS.text.secondary, fontFamily: "inherit" }}>
          {attrs.label}
        </Typography>
        <Typography sx={{ fontSize: "0.8rem", color: COLORS.text.secondary, fontFamily: "inherit" }}>
          {value}
        </Typography>
      </Box>
      <Slider
        value={value}
        onChange={(_, v) => update(key, v)}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        size="small"
        sx={{ color: COLORS.primary }}
      />
    </Box>
  );
}
