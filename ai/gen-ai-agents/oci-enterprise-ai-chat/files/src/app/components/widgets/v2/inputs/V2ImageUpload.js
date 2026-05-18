"use client";
import { useState, useRef, useCallback } from "react";
import { Box, Typography, IconButton } from "@mui/material";
import { Upload, X, Image as ImageIcon } from "lucide-react";
import { useV2Form } from "../WidgetV2FormContext";
import { COLORS, BORDER } from "../../../../config/widgetTheme";

export default function V2ImageUpload({ attrs = {} }) {
  const form = useV2Form();
  const hasFormCtx = form.__hasProvider;
  const key = attrs.name || attrs.label || "imageupload";

  const [localFile, setLocalFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const file = hasFormCtx ? form.state[key] || null : localFile;
  const disabled = hasFormCtx ? form.disabled : false;
  const update = hasFormCtx ? form.update : (k, v) => setLocalFile(v);

  const accept = attrs.accept || "image/*";
  const maxSize = Number(attrs.maxsize) || 5; // MB

  const processFile = useCallback((f) => {
    if (!f) return;
    if (f.size > maxSize * 1024 * 1024) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      update(key, { name: f.name, size: f.size, type: f.type, data: e.target.result });
    };
    reader.readAsDataURL(f);
  }, [key, maxSize, update]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    if (disabled) return;
    const f = e.dataTransfer.files?.[0];
    if (f) processFile(f);
  }, [disabled, processFile]);

  const handleChange = useCallback((e) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
    e.target.value = "";
  }, [processFile]);

  const handleRemove = useCallback((e) => {
    e.stopPropagation();
    update(key, null);
  }, [key, update]);

  return (
    <Box>
      {attrs.label && (
        <Typography sx={{ fontSize: "0.8rem", fontWeight: 500, color: COLORS.text.secondary, mb: 0.5, fontFamily: "inherit" }}>
          {attrs.label}
        </Typography>
      )}

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        onChange={handleChange}
        style={{ display: "none" }}
      />

      {file?.data ? (
        /* Preview */
        <Box sx={{ position: "relative", display: "inline-block", maxWidth: "100%" }}>
          <Box
            component="img"
            src={file.data}
            alt={file.name}
            sx={{
              maxWidth: "100%",
              maxHeight: 220,
              borderRadius: `${BORDER.radiusSmall}px`,
              objectFit: "contain",
              display: "block",
            }}
          />
          {!disabled && (
            <IconButton
              onClick={handleRemove}
              size="small"
              sx={{
                position: "absolute",
                top: 4,
                right: 4,
                backgroundColor: "rgba(0,0,0,0.55)",
                color: "#fff",
                "&:hover": { backgroundColor: "rgba(0,0,0,0.75)" },
                width: 26,
                height: 26,
              }}
            >
              <X size={14} />
            </IconButton>
          )}
          <Typography sx={{ fontSize: "0.7rem", color: COLORS.text.secondary, mt: 0.5, fontFamily: "inherit" }}>
            {file.name}
          </Typography>
        </Box>
      ) : (
        /* Drop zone */
        <Box
          onClick={() => !disabled && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); if (!disabled) setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          sx={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 0.8,
            py: 3,
            px: 2,
            borderRadius: `${BORDER.radiusSmall}px`,
            border: `2px dashed ${dragOver ? COLORS.primary : "rgba(49,45,42,0.2)"}`,
            backgroundColor: dragOver ? "rgba(199,70,52,0.04)" : COLORS.background.input,
            cursor: disabled ? "default" : "pointer",
            opacity: disabled ? 0.5 : 1,
            transition: "all 0.2s ease",
            "&:hover": !disabled ? {
              borderColor: "rgba(49,45,42,0.35)",
              backgroundColor: COLORS.background.hover,
            } : {},
          }}
        >
          {dragOver ? (
            <ImageIcon size={28} color={COLORS.primary} />
          ) : (
            <Upload size={28} color={COLORS.text.secondary} />
          )}
          <Typography sx={{ fontSize: "0.8rem", color: COLORS.text.secondary, fontFamily: "inherit", textAlign: "center" }}>
            {attrs.placeholder || "Arrastra una imagen o haz clic para seleccionar"}
          </Typography>
          <Typography sx={{ fontSize: "0.65rem", color: COLORS.text.secondary, opacity: 0.6, fontFamily: "inherit" }}>
            Max {maxSize}MB
          </Typography>
        </Box>
      )}
    </Box>
  );
}
