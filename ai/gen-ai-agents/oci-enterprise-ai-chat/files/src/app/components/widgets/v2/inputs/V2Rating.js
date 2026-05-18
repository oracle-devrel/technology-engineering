"use client";
import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { Star } from "lucide-react";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Rating({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "rating";
  const max = parseInt(attrs.max) || 5;
  const defaultValue = parseInt(attrs.value || attrs.default) || 0;
  const [localValue, setLocalValue] = useState(defaultValue);
  const [hover, setHover] = useState(-1);

  const value = hasFormCtx ? (form.state[key] ?? defaultValue) : localValue;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalValue(v);

  return (
    <Box>
      {attrs.label && (
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500, color: COLORS.text.secondary, mb: 0.5, fontFamily: "inherit" }}>
          {attrs.label}
        </Typography>
      )}
      <Box sx={{ display: "flex", gap: 0.25 }}>
        {Array.from({ length: max }, (_, i) => (
          <Box
            key={i}
            onMouseEnter={() => !disabled && setHover(i)}
            onMouseLeave={() => setHover(-1)}
            onClick={() => !disabled && update(key, i + 1)}
            sx={{ cursor: disabled ? "default" : "pointer", transition: "transform 0.15s", "&:hover": { transform: disabled ? "none" : "scale(1.15)" } }}
          >
            <Star
              size={22}
              fill={(hover >= 0 ? i <= hover : i < value) ? "#F1B13F" : "none"}
              color={(hover >= 0 ? i <= hover : i < value) ? "#F1B13F" : "rgba(0,0,0,0.2)"}
            />
          </Box>
        ))}
      </Box>
    </Box>
  );
}
