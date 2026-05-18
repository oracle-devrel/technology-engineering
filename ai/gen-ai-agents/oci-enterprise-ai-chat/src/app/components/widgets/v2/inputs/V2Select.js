"use client";
import { useMemo, useState } from "react";
import { Box, MenuItem, Select, Typography } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export function V2Option() { return null; }

export default function V2Select({ attrs = {}, node }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "select";
  const [localValue, setLocalValue] = useState(attrs.value || attrs.default || "");

  const options = useMemo(() => {
    if (!node?.children) return [];
    return node.children
      .filter(c => typeof c !== "string" && c.tag === "option")
      .map(c => c.children.join("").trim());
  }, [node]);

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
      <Select
        value={value}
        onChange={(e) => update(key, e.target.value)}
        disabled={disabled}
        size="small"
        fullWidth
        displayEmpty
        sx={{ fontSize: "0.85rem", backgroundColor: "rgba(0,0,0,0.02)" }}
      >
        <MenuItem value="" disabled>{attrs.placeholder || "Select..."}</MenuItem>
        {options.map((opt, i) => (
          <MenuItem key={i} value={opt}>{opt}</MenuItem>
        ))}
      </Select>
    </Box>
  );
}
