"use client";
import { useState } from "react";
import { FormControlLabel, Checkbox } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Checkbox({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "checkbox";
  const defaultChecked = attrs.checked === "true" || attrs.default === "true";
  const [localChecked, setLocalChecked] = useState(defaultChecked);

  const checked = hasFormCtx ? (form.state[key] ?? defaultChecked) : localChecked;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalChecked(v);

  return (
    <FormControlLabel
      control={
        <Checkbox
          checked={!!checked}
          onChange={(e) => update(key, e.target.checked)}
          disabled={disabled}
          size="small"
          sx={{ color: COLORS.text.secondary, "&.Mui-checked": { color: COLORS.primary } }}
        />
      }
      label={attrs.label || ""}
      sx={{ "& .MuiFormControlLabel-label": { fontSize: "0.85rem", fontFamily: "inherit" } }}
    />
  );
}
