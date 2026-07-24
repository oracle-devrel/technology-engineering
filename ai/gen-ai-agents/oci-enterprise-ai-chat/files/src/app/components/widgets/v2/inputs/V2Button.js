"use client";
import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useV2Form } from "../WidgetV2FormContext";
import { getColor, COLORS, BUTTON } from "../../../../config/widgetTheme";

export default function V2Button({ attrs = {} }) {
  const { state, disabled, onSubmit } = useV2Form();
  const [clicked, setClicked] = useState(false);
  const color = getColor(attrs.color) || COLORS.primary;

  const handleClick = () => {
    if (disabled || clicked) return;
    setClicked(true);
    onSubmit?.({ ...state, _action: attrs.action || attrs.label || "submit" });
  };

  return (
    <motion.div whileHover={!disabled && !clicked ? { scale: 1.02 } : {}} whileTap={!disabled && !clicked ? { scale: 0.98 } : {}}>
      <Box
        onClick={handleClick}
        sx={{
          display: "inline-flex",
          px: 2.5,
          py: 1,
          borderRadius: `${BUTTON.borderRadius}px`,
          backgroundColor: clicked ? COLORS.success : color,
          color: "#fff",
          cursor: disabled || clicked ? "default" : "pointer",
          opacity: disabled ? 0.5 : 1,
          transition: "all 0.2s ease",
          fontFamily: "inherit",
        }}
      >
        <Typography sx={{ fontSize: "0.85rem", fontWeight: 500, color: "inherit", fontFamily: "inherit" }}>
          {clicked ? "Submitted" : (attrs.label || "Submit")}
        </Typography>
      </Box>
    </motion.div>
  );
}
