"use client";
import { useState } from "react";
import { Box, Dialog } from "@mui/material";

export default function V2Image({ attrs = {} }) {
  const [open, setOpen] = useState(false);
  const src = attrs.src || "";
  if (!src.startsWith("http")) return null;
  const imageUrl = src;

  return (
    <>
      <Box
        onClick={() => setOpen(true)}
        sx={{
          width: "100%",
          borderRadius: 2,
          overflow: "hidden",
          cursor: "pointer",
          transition: "transform 0.2s ease, box-shadow 0.2s ease",
          "&:hover": {
            transform: "scale(1.01)",
            boxShadow: "0 4px 20px rgba(0,0,0,0.12)",
          },
        }}
      >
        <Box
          component="img"
          src={imageUrl}
          alt={attrs.alt || ""}
          sx={{ width: "100%", height: attrs.height || "auto", objectFit: "cover", display: "block" }}
        />
      </Box>
      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        maxWidth={false}
        PaperProps={{
          sx: {
            backgroundColor: "transparent",
            boxShadow: "none",
            maxWidth: "90vw",
            maxHeight: "90vh",
            overflow: "hidden",
            borderRadius: 2,
          },
        }}
        slotProps={{
          backdrop: {
            sx: { backgroundColor: "rgba(0,0,0,0.85)" },
          },
        }}
      >
        <Box
          component="img"
          src={imageUrl}
          alt={attrs.alt || ""}
          onClick={() => setOpen(false)}
          sx={{
            maxWidth: "90vw",
            maxHeight: "90vh",
            objectFit: "contain",
            display: "block",
            cursor: "pointer",
          }}
        />
      </Dialog>
    </>
  );
}
