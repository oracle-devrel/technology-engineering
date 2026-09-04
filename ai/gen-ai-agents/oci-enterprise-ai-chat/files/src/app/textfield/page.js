"use client";

import { Box, TextField, IconButton, Typography } from "@mui/material";
import { FileText as TextIcon, X } from "lucide-react";
import Image from "next/image";
import { AnimatePresence, motion } from "framer-motion";
import { useState, useCallback, useRef, useEffect } from "react";
import { TEXT_EXTENSIONS } from "../components/chat/ChatInput";
import TypingEffect from "../components/ui/TypingEffect";
import { withBase } from "../../lib/withBase";

const LONG_TEXT_THRESHOLD = 500;

const FILE_STYLES = {
  csv: { border: "#4CAF50", chip: "rgba(76, 175, 80, 0.15)", chipText: "#2e7d32" },
  json: { border: "#FF9800", chip: "rgba(255, 152, 0, 0.15)", chipText: "#e65100" },
  pdf: { border: "#F44336", chip: "rgba(244, 67, 54, 0.15)", chipText: "#c62828" },
  txt: { border: "#42A5F5", chip: "rgba(66, 165, 245, 0.15)", chipText: "#1976d2" },
  md: { border: "#2196F3", chip: "rgba(33, 150, 243, 0.15)", chipText: "#1565c0" },
  sql: { border: "#9C27B0", chip: "rgba(156, 39, 176, 0.15)", chipText: "#7b1fa2" },
  py: { border: "#3776AB", chip: "rgba(55, 118, 171, 0.15)", chipText: "#2c5f8a" },
  js: { border: "#F7DF1E", chip: "rgba(247, 223, 30, 0.2)", chipText: "#8a7800" },
  ts: { border: "#3178C6", chip: "rgba(49, 120, 198, 0.15)", chipText: "#235a9e" },
  default: { border: "#9E9E9E", chip: "rgba(0,0,0,0.1)", chipText: "rgba(0,0,0,0.5)" },
};

export default function TextFieldPage() {
  const [value, setValue] = useState("");
  const [attachedImages, setAttachedImages] = useState([]);
  const [attachedTexts, setAttachedTexts] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [mounted, setMounted] = useState(false);
  const dragCounterRef = useRef(0);
  const inputRef = useRef(null);

  useEffect(() => { setMounted(true); }, []);

  const getExt = (name) => {
    if (!name) return null;
    const parts = name.split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : null;
  };

  const addTextAttachment = useCallback((content, name) => {
    const ext = getExt(name);
    setAttachedTexts(prev => [...prev, {
      id: `txt-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
      content,
      name: name || "Pasted text",
      ext,
      preview: content.slice(0, 200).replace(/\n/g, " ") + (content.length > 200 ? "..." : ""),
    }]);
  }, []);

  const processImageFile = useCallback((file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setAttachedImages(prev => [...prev, {
        id: `img-${Date.now()}-${Math.random().toString(36).substr(2, 5)}`,
        name: file.name,
        preview: e.target.result,
        file,
      }]);
    };
    reader.readAsDataURL(file);
  }, []);

  const processTextFile = useCallback((file) => {
    const reader = new FileReader();
    reader.onload = (e) => addTextAttachment(e.target.result, file.name);
    reader.readAsText(file);
  }, [addTextAttachment]);

  const processPdfFile = useCallback(async (file) => {
    try {
      const pdfjsLib = await import("pdfjs-dist");
      pdfjsLib.GlobalWorkerOptions.workerSrc = withBase("/pdf.worker.min.mjs");
      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const textParts = [];
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        const pageText = content.items.map(item => item.str).join(" ");
        if (pageText.trim()) textParts.push(pageText);
      }
      const fullText = textParts.join("\n\n");
      addTextAttachment(fullText.trim() || `[PDF - ${pdf.numPages} pages]`, file.name);
    } catch {
      addTextAttachment(`[PDF - ${(file.size / 1024).toFixed(1)} KB]`, file.name);
    }
  }, [addTextAttachment]);

  const isTextFile = useCallback((file) => {
    return file.type?.startsWith("text/") ||
      TEXT_EXTENSIONS.some(ext => file.name?.toLowerCase().endsWith(ext));
  }, []);

  const isPdfFile = useCallback((file) => {
    return file.type === "application/pdf" || file.name?.toLowerCase().endsWith(".pdf");
  }, []);

  const processFiles = useCallback((files) => {
    Array.from(files).forEach(file => {
      if (file.type.startsWith("image/")) processImageFile(file);
      else if (isPdfFile(file)) processPdfFile(file);
      else if (isTextFile(file)) processTextFile(file);
    });
  }, [processImageFile, processPdfFile, processTextFile, isPdfFile, isTextFile]);

  // Drag & drop
  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;
    if (e.dataTransfer?.types?.includes("Files")) setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounterRef.current = 0;
    const files = e.dataTransfer?.files;
    if (files?.length > 0) {
      processFiles(files);
      inputRef.current?.focus();
    }
  }, [processFiles]);

  // Paste
  const handlePaste = useCallback((e) => {
    const files = e.clipboardData?.files;
    if (files?.length > 0) {
      e.preventDefault();
      processFiles(files);
      return;
    }
    const items = e.clipboardData?.items;
    if (items) {
      for (let i = 0; i < items.length; i++) {
        if (items[i].type.startsWith("image/")) {
          e.preventDefault();
          const file = items[i].getAsFile();
          if (file) processImageFile(file);
          return;
        }
      }
    }
    const pastedText = e.clipboardData.getData("text");
    if (pastedText && pastedText.length >= LONG_TEXT_THRESHOLD) {
      e.preventDefault();
      addTextAttachment(pastedText);
    }
  }, [processFiles, processImageFile, addTextAttachment]);

  return (
    <Box
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      sx={{
        minHeight: "100vh",
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundImage: "url('/backgrounds/white-red-background.png')",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
        px: 4,
        pt: 4,
        pb: "15vh",
        position: "relative",
      }}
    >
      {/* Drop overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              position: "fixed",
              inset: 0,
              zIndex: 100,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "rgba(255,255,255,0.85)",
              backdropFilter: "blur(8px)",
            }}
          >
            <Box sx={{
              border: "2px dashed rgba(0,0,0,0.25)",
              borderRadius: 4,
              p: 10,
              width: "50vw",
              height: "35vh",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              textAlign: "center",
            }}>
              <Typography sx={{ fontSize: "1.5rem", color: "rgba(0,0,0,0.4)", fontWeight: 300 }}>
                Drop files here
              </Typography>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      <Box sx={{ width: "100%", maxWidth: 480 }}>
        {/* Logo & Welcome - staggered for recording */}
        <Box sx={{ mb: 4, minHeight: 130 }}>
          <motion.div
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3, ease: "easeOut" }}
          >
            <Image
              src="/oracle-logo-building.png"
              alt="Logo"
              width={600}
              height={400}
              style={{ maxHeight: "100px", width: "auto", objectFit: "contain", marginBottom: 12 }}
            />
          </motion.div>
          <Typography sx={{ fontSize: "2rem", fontWeight: 300, lineHeight: 1.4, color: "rgba(0,0,0,0.7)", minHeight: "2.8rem" }}>
            <TypingEffect text="Hey," speed={60} delay={900} />
          </Typography>
          <Typography sx={{ fontSize: "2rem", fontWeight: 300, lineHeight: 1.4, color: "rgba(0,0,0,0.7)", minHeight: "2.8rem" }}>
            <TypingEffect text="Welcome to Agent Hub!" speed={45} delay={1600} />
          </Typography>
        </Box>

        {/* TextField */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.0, delay: 3.0, ease: "easeOut" }}
        >

        {/* Attachment previews */}
        <AnimatePresence>
          {(attachedImages.length > 0 || attachedTexts.length > 0) && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: "easeOut" }}
              style={{ overflow: "hidden" }}
            >
              <Box sx={{ display: "flex", flexDirection: "column", gap: 1, mb: 2, pt: 1, pr: 1 }}>
                {/* Images */}
                {attachedImages.length > 0 && (
                  <Box sx={{ display: "flex", gap: 1.5, flexWrap: "wrap" }}>
                    {attachedImages.map(img => (
                      <Box key={img.id} sx={{ position: "relative", width: 80, height: 80, "&:hover .remove-btn": { opacity: 1 } }}>
                        <Box sx={{ width: "100%", height: "100%", borderRadius: 1, overflow: "hidden", border: "1px solid rgba(0,0,0,0.1)" }}>
                          <img src={img.preview} alt={img.name} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
                        </Box>
                        <IconButton
                          className="remove-btn"
                          size="small"
                          onClick={() => setAttachedImages(prev => prev.filter(i => i.id !== img.id))}
                          sx={{ position: "absolute", top: -6, right: -6, backgroundColor: "rgba(0,0,0,0.6)", color: "white", padding: "2px", opacity: 0, transition: "opacity 0.15s", "&:hover": { backgroundColor: "rgba(0,0,0,0.8)" } }}
                        >
                          <X size={12} />
                        </IconButton>
                      </Box>
                    ))}
                  </Box>
                )}

                {/* Text files */}
                {attachedTexts.length > 0 && (
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5 }}>
                    {attachedTexts.map(txt => {
                      const style = FILE_STYLES[txt.ext] || FILE_STYLES.default;
                      const extLabel = txt.ext || "txt";
                      return (
                        <Box key={txt.id} sx={{ position: "relative", width: 120, mb: "4px", mr: "4px", "&:hover .remove-btn": { opacity: 1 } }}>
                          <Box sx={{ position: "absolute", bottom: -4, left: 3, right: -3, top: 0, borderRadius: 0.75, backgroundColor: `${style.border}12`, border: `1px solid ${style.border}20` }} />
                          <Box sx={{
                            position: "relative", display: "flex", flexDirection: "column", p: 1.25, height: 120,
                            borderRadius: 0.75, backgroundColor: "white", border: `1px solid ${style.border}30`,
                            boxShadow: `0 2px 8px ${style.border}12`, overflow: "hidden",
                            transition: "all 0.2s", "&:hover": { transform: "translateY(-2px)", boxShadow: `0 8px 20px ${style.border}20` },
                          }}>
                            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.75 }}>
                              <TextIcon size={12} style={{ color: style.border, flexShrink: 0 }} />
                              <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, color: style.chipText, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
                                {txt.name || "Pasted"}
                              </Typography>
                            </Box>
                            <Box sx={{ flex: 1, overflow: "hidden" }}>
                              <Typography sx={{ fontSize: "0.6rem", color: "rgba(0,0,0,0.45)", lineHeight: 1.4, overflow: "hidden", display: "-webkit-box", WebkitLineClamp: 3, WebkitBoxOrient: "vertical", wordBreak: "break-all" }}>
                                {txt.preview}
                              </Typography>
                            </Box>
                            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mt: 0.75 }}>
                              <Box sx={{ display: "flex", gap: 0.25 }}>
                                {[0.3, 0.5, 0.8].map((o, i) => <Box key={i} sx={{ width: 3, height: 3, borderRadius: "50%", backgroundColor: style.border, opacity: o }} />)}
                              </Box>
                              <Box sx={{ px: 0.5, py: 0.15, borderRadius: 0.5, backgroundColor: style.chip }}>
                                <Typography sx={{ fontSize: "0.55rem", fontWeight: 700, color: style.chipText }}>.{extLabel}</Typography>
                              </Box>
                            </Box>
                          </Box>
                          <IconButton
                            className="remove-btn"
                            size="small"
                            onClick={() => setAttachedTexts(prev => prev.filter(t => t.id !== txt.id))}
                            sx={{ position: "absolute", top: -6, right: -6, zIndex: 2, backgroundColor: style.border, color: "white", padding: "2px", opacity: 0, transition: "opacity 0.15s", "&:hover": { backgroundColor: style.chipText } }}
                          >
                            <X size={12} />
                          </IconButton>
                        </Box>
                      );
                    })}
                  </Box>
                )}
              </Box>
            </motion.div>
          )}
        </AnimatePresence>

        {/* TextField only - no buttons */}
        <TextField
          inputRef={inputRef}
          autoFocus
          variant="standard"
          placeholder="Ask me anything..."
          multiline
          maxRows={12}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onPaste={handlePaste}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              setValue("");
              setAttachedImages([]);
              setAttachedTexts([]);
            }
          }}
          fullWidth
          sx={{
            "& input, & textarea, & .MuiInput-input": {
              fontSize: "1.35rem",
              fontWeight: "100 !important",
              color: "rgba(0, 0, 0, 0.6)",
              paddingTop: "4px",
              lineHeight: 1.4,
            },
            "& .MuiInput-underline:before, & .MuiInput-underline:hover:not(.Mui-disabled):before, & .MuiInput-underline:after": {
              borderBottom: "none",
            },
            "& .MuiInput-root": {
              "&::before, &::after": { display: "none" },
            },
            "& ul, & li": { listStyle: "none", margin: 0, padding: 0 },
          }}
        />
        </motion.div>
      </Box>
    </Box>
  );
}
