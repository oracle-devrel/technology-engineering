"use client";
import { useMemo, useState } from "react";
import { Box, FormControlLabel, Radio, RadioGroup, Typography } from "@mui/material";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Radio({ attrs = {}, node }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "radio";
  const [localValue, setLocalValue] = useState(attrs.value || attrs.default || "");

  const options = useMemo(() => {
    if (attrs.options) return attrs.options.split(";").map(o => o.trim());
    if (node?.children) {
      return node.children
        .filter(c => typeof c !== "string" && c.tag === "option")
        .map(c => c.children.join("").trim());
    }
    return [];
  }, [attrs.options, node]);

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
      <RadioGroup value={value} onChange={(e) => update(key, e.target.value)}>
        {options.map((opt, i) => (
          <FormControlLabel
            key={i}
            value={opt}
            control={<Radio size="small" disabled={disabled} sx={{ "&.Mui-checked": { color: COLORS.primary } }} />}
            label={opt}
            sx={{ "& .MuiFormControlLabel-label": { fontSize: "0.85rem", fontFamily: "inherit" } }}
          />
        ))}
      </RadioGroup>
    </Box>
  );
}
