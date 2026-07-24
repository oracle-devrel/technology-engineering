"use client";
import { useState } from "react";
import { Box, Switch, Typography } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Toggle({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "toggle";
  const defaultChecked = attrs.checked === "true" || attrs.default === "true";
  const [localChecked, setLocalChecked] = useState(defaultChecked);

  const checked = hasFormCtx ? (form.state[key] ?? defaultChecked) : localChecked;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalChecked(v);

  return (
    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
      <Typography sx={{ fontSize: "0.85rem", color: "inherit", fontFamily: "inherit" }}>
        {attrs.label}
      </Typography>
      <Switch
        checked={!!checked}
        onChange={(e) => update(key, e.target.checked)}
        disabled={disabled}
        size="small"
        sx={{ "& .Mui-checked": { color: COLORS.primary }, "& .Mui-checked + .MuiSwitch-track": { backgroundColor: COLORS.primary } }}
      />
    </Box>
  );
}
