"use client";

import { KeyboardReturn } from "@mui/icons-material";
import { Badge, Box, Chip, IconButton, ListSubheader, Menu, MenuItem, TextField, Tooltip, Typography, Divider, Dialog, DialogContent } from "@mui/material";
import { ChevronDown, ChevronUp, ChevronRight, Paperclip, ImagePlus, FileText, Wrench, Settings, X, FileText as TextIcon, Search, FileSearch, Database, Plug, Puzzle, Presentation, FolderOpen, Terminal, Brain, Copy, Check, CircleStop } from "lucide-react";


const BrainFreezeIcon = ({ size = 16, color = "currentColor", style }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" style={style}>
    <path fill={color} d="M13 3c3.88 0 7 3.14 7 7c0 2.8-1.63 5.19-4 6.31V21H9v-3H8c-1.11 0-2-.89-2-2v-3H4.5c-.42 0-.66-.5-.42-.81L6 9.66A7.003 7.003 0 0 1 13 3m0-2C8.41 1 4.61 4.42 4.06 8.9L2.5 11h-.03l-.02.03c-.55.76-.62 1.76-.19 2.59c.36.69 1 1.17 1.74 1.32V16c0 1.85 1.28 3.42 3 3.87V23h11v-5.5c2.5-1.67 4-4.44 4-7.5c0-4.97-4.04-9-9-9m4.33 8.3l-1.96.51l1.44 1.46c.35.34.35.92 0 1.27s-.93.35-1.27 0l-1.45-1.44l-.52 1.96c-.12.49-.61.76-1.07.64a.91.91 0 0 1-.66-1.11l.53-1.96l-1.96.53a.91.91 0 0 1-1.11-.66c-.12-.45.16-.95.64-1.07l1.96-.52l-1.44-1.45a.9.9 0 0 1 1.27-1.27l1.46 1.44l.51-1.96c.12-.49.62-.77 1.09-.64c.49.13.77.62.64 1.1L14.9 8.1l1.97-.53c.48-.13.97.15 1.1.64c.13.47-.15.97-.64 1.09"/>
  </svg>
);
import { AnimatePresence, motion } from "framer-motion";
import { useState, useEffect, memo, useCallback, useImperativeHandle, forwardRef, useRef } from "react";
import { MCPService } from "../../services/mcpService";
import IOSSwitch from "../ui/IOSSwitch";
import { withBase } from "../../../lib/withBase";

export const TEXT_EXTENSIONS = ['.txt', '.md', '.json', '.js', '.ts', '.jsx', '.tsx', '.css', '.html', '.xml', '.csv', '.log', '.py', '.java', '.c', '.cpp', '.h', '.sql', '.yaml', '.yml', '.sh', '.env'];
const LONG_TEXT_THRESHOLD = 500;

function CopyButton({ content }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <IconButton size="small" onClick={handleCopy} title="Copy to clipboard">
      {copied ? <Check size={16} style={{ color: "#10B981" }} /> : <Copy size={16} />}
    </IconButton>
  );
}

const NATIVE_TOOLS_META = {
  native_web_search: { name: "Web Search", icon: Search, color: "#4285F4" },
  native_code_interpreter: { name: "Code Interpreter", icon: Terminal, color: "#10B981" },
  native_rag: { name: "File Search", icon: FileSearch, color: "#8B5CF6" },
  native_text_to_sql: { name: "Text to SQL", icon: Database, color: "#F59E0B" },
};

const DrawioLogoSmall = ({ size = 14, color = "#F08705" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
    <rect x="3" y="3" width="7" height="7" rx="1.5" fill={color} opacity="0.9" />
    <rect x="14" y="14" width="7" height="7" rx="1.5" fill={color} opacity="0.9" />
    <rect x="14" y="3" width="7" height="7" rx="1.5" fill={color} opacity="0.5" />
    <line x1="10" y1="6.5" x2="14" y2="6.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="6.5" y1="10" x2="6.5" y2="17.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    <line x1="6.5" y1="17.5" x2="14" y2="17.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

const ADDON_TOOLS_META = {
  addon_drawio: { name: "OCI Draw.io", color: "#F08705", LogoComponent: DrawioLogoSmall },
  addon_sdd: { name: "OCI SDD Generator", color: "#0EA5E9", icon: FileText },
  addon_ppt: { name: "OCI PPT Generator", color: "#EF4444", icon: Presentation },
};

const ChatInput = memo(forwardRef(function ChatInput({
  onSubmit,
  onStop,
  placeholder,
  fontSize,
  disabled = false,
  isLoading = false,
  compact = false,
  models,
  selectedModel,
  onModelChange,
  accentColor,
  isDarkBg = false,
  onAttachmentsChange,
}, ref) {
  const iconColor = accentColor || (isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0, 0, 0, 0.4)");
  const iconOpacity = 1;
  const [value, setValue] = useState("");
  const [attachMenuAnchor, setAttachMenuAnchor] = useState(null);
  const [toolsMenuAnchor, setToolsMenuAnchor] = useState(null);
  const [servers, setServers] = useState([]);
  const [sessionDisabledServers, setSessionDisabledServers] = useState(new Set());
  const [attachedImages, setAttachedImages] = useState([]);
  const [attachedTexts, setAttachedTexts] = useState([]);

  useEffect(() => {
    onAttachmentsChange?.(attachedImages.length + attachedTexts.length);
  }, [attachedImages.length, attachedTexts.length, onAttachmentsChange]);
  const [textDialogOpen, setTextDialogOpen] = useState(null);
  const [imageDialogOpen, setImageDialogOpen] = useState(null);
  const [modelMenuAnchor, setModelMenuAnchor] = useState(null);
  const localInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const fileInputRef = useRef(null);

  const [nativeTools, setNativeTools] = useState([]);
  const [selectedVsNames, setSelectedVsNames] = useState([]); // [{id, name}]
  const [thinkingMenuAnchor, setThinkingMenuAnchor] = useState(null);
  const [reasoningEffort, setReasoningEffort] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('reasoningEffort') || 'off';
    }
    return 'off';
  });

  // Reasoning-capable model detection
  const REASONING_PATTERNS = ['o4-mini', 'gpt-5.4', 'grok-4-reasoning', 'o3', 'o4'];
  const isReasoningModel = selectedModel && REASONING_PATTERNS.some(p => selectedModel.includes(p));

  // Persist reasoning effort
  const handleReasoningEffortChange = useCallback((effort) => {
    setReasoningEffort(effort);
    localStorage.setItem('reasoningEffort', effort);
    setThinkingMenuAnchor(null);
  }, []);

  // Load enabled servers and native tools
  useEffect(() => {
    const updateServers = () => {
      const allServers = MCPService.getServers().filter(s => s.enabled);
      setServers(allServers);
    };
    const updateNativeTools = () => {
      try {
        const stored = localStorage.getItem('nativeToolsEnabled');
        const state = stored ? JSON.parse(stored) : {};
        // Filter out coming-soon tools (native_text_to_sql)
        const comingSoon = new Set(['native_text_to_sql']);
        setNativeTools(Object.entries(state).filter(([id, v]) => v && !comingSoon.has(id)).map(([id]) => id));
      } catch { setNativeTools([]); }
    };
    const updateKnowledge = async () => {
      try {
        const ids = JSON.parse(localStorage.getItem('ragVectorStoreIds') || '[]');
        if (ids.length === 0) { setSelectedVsNames([]); return; }
        const res = await fetch('/api/vector-stores');
        if (res.ok) {
          const data = await res.json();
          const vsMap = Object.fromEntries((data.data || []).map(vs => [vs.id, vs.name]));
          setSelectedVsNames(ids.map(id => ({ id, name: vsMap[id] || id })));
        } else {
          setSelectedVsNames(ids.map(id => ({ id, name: id })));
        }
      } catch { setSelectedVsNames([]); }
    };
    updateServers();
    updateNativeTools();
    updateKnowledge();

    const handleStorage = (e) => {
      if (e.key === MCPService.STORAGE_KEYS.SERVERS) updateServers();
      if (e.key === 'nativeToolsEnabled') updateNativeTools();
      if (e.key === 'ragVectorStoreIds') updateKnowledge();
    };
    const handleToolsChanged = () => { updateServers(); updateNativeTools(); updateKnowledge(); };
    window.addEventListener('storage', handleStorage);
    window.addEventListener('mcp-tools-changed', handleToolsChanged);
    return () => {
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('mcp-tools-changed', handleToolsChanged);
    };
  }, []);

  // Dispatch event when session disabled servers change
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("mcp-session-changed", {
      detail: { disabledServers: Array.from(sessionDisabledServers) }
    }));
  }, [sessionDisabledServers]);

  // Get file extension from name
  const getFileExtension = (name) => {
    if (!name) return null;
    const match = name.match(/\.([^.]+)$/);
    return match ? match[1].toLowerCase() : null;
  };

  // Add text attachment helper
  const addTextAttachment = useCallback((content, name = null) => {
    setAttachedTexts(prev => {
      if (prev.length >= 4) return prev;
      return [...prev, {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
        name,
        ext: getFileExtension(name),
        content,
        preview: content.slice(0, 200).replace(/\n/g, ' ') + (content.length > 200 ? '...' : ''),
      }];
    });
  }, []);

  // Process image files
  const processImageFile = useCallback((file) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      setAttachedImages(prev => [...prev, {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
        name: file.name,
        type: file.type,
        base64: event.target.result,
        preview: event.target.result,
      }]);
    };
    reader.readAsDataURL(file);
  }, []);

  // Process text files
  const processTextFile = useCallback((file) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      addTextAttachment(event.target.result, file.name);
    };
    reader.readAsText(file);
  }, [addTextAttachment]);

  // Process PDF files - extract text content
  const processPdfFile = useCallback(async (file) => {
    try {
      const pdfjsLib = await import('pdfjs-dist');
      pdfjsLib.GlobalWorkerOptions.workerSrc = withBase('/pdf.worker.min.mjs');

      const arrayBuffer = await file.arrayBuffer();
      const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
      const textParts = [];

      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const content = await page.getTextContent();
        const pageText = content.items.map(item => item.str).join(' ');
        if (pageText.trim()) textParts.push(pageText);
      }

      const fullText = textParts.join('\n\n');
      if (fullText.trim()) {
        addTextAttachment(fullText, file.name);
      } else {
        // Fallback: no extractable text (scanned PDF)
        const sizeKB = (file.size / 1024).toFixed(1);
        addTextAttachment(`[PDF sin texto extraíble - ${sizeKB} KB, ${pdf.numPages} páginas]`, file.name);
      }
    } catch (err) {
      console.error('PDF extraction error:', err);
      const sizeKB = (file.size / 1024).toFixed(1);
      addTextAttachment(`[Error al leer PDF - ${sizeKB} KB]`, file.name);
    }
  }, [addTextAttachment]);

  // Process XLSX files - extract text content
  const processXlsxFile = useCallback(async (file) => {
    try {
      const XLSX = await import('xlsx');
      const arrayBuffer = await file.arrayBuffer();
      const workbook = XLSX.read(arrayBuffer, { type: 'array' });
      const textParts = [];

      for (const sheetName of workbook.SheetNames) {
        const sheet = workbook.Sheets[sheetName];
        const rows = XLSX.utils.sheet_to_json(sheet, { header: 1, defval: '' });
        if (rows.length === 0) continue;

        const lines = rows.map(row => row.join('\t'));
        textParts.push(`[${sheetName}]\n${lines.join('\n')}`);
      }

      const fullText = textParts.join('\n\n');
      if (fullText.trim()) {
        addTextAttachment(fullText, file.name);
      } else {
        const sizeKB = (file.size / 1024).toFixed(1);
        addTextAttachment(`[XLSX sin datos - ${sizeKB} KB, ${workbook.SheetNames.length} hojas]`, file.name);
      }
    } catch (err) {
      console.error('XLSX extraction error:', err);
      const sizeKB = (file.size / 1024).toFixed(1);
      addTextAttachment(`[Error al leer XLSX - ${sizeKB} KB]`, file.name);
    }
  }, [addTextAttachment]);

  // Check if file is a text file
  const isTextFile = useCallback((file) => {
    return file.type.startsWith('text/') ||
      TEXT_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));
  }, []);

  // Check if file is a PDF
  const isPdfFile = useCallback((file) => {
    return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
  }, []);

  // Check if file is an Excel file
  const isXlsxFile = useCallback((file) => {
    const xlsxTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ];
    return xlsxTypes.includes(file.type) ||
      /\.(xlsx|xls)$/i.test(file.name);
  }, []);

  // Process files (images, text, PDFs, and XLSX)
  const processFiles = useCallback((files) => {
    Array.from(files).forEach(file => {
      if (file.type.startsWith('image/')) {
        processImageFile(file);
      } else if (isPdfFile(file)) {
        processPdfFile(file);
      } else if (isXlsxFile(file)) {
        processXlsxFile(file);
      } else if (isTextFile(file)) {
        processTextFile(file);
      }
    });
  }, [processImageFile, processPdfFile, processXlsxFile, processTextFile, isPdfFile, isXlsxFile, isTextFile]);

  // Expose methods to parent
  useImperativeHandle(ref, () => ({
    focus: () => localInputRef.current?.focus(),
    clear: () => {
      setValue("");
      setAttachedImages([]);
      setAttachedTexts([]);
    },
    getValue: () => value,
    getSessionActiveServers: () => servers.filter(s => !sessionDisabledServers.has(s.id)).map(s => s.id),
    getAttachedImages: () => attachedImages,
    getAttachedTexts: () => attachedTexts,
    addFiles: (files) => processFiles(files),
  }));

  const handleServerToggle = useCallback((serverId) => {
    setSessionDisabledServers(prev => {
      const next = new Set(prev);
      if (next.has(serverId)) {
        next.delete(serverId);
      } else {
        next.add(serverId);
      }
      return next;
    });
  }, []);

  const handleChange = useCallback((e) => setValue(e.target.value), []);

  const handleImageSelect = useCallback((e) => {
    processFiles(e.target.files);
    e.target.value = '';
  }, [processFiles]);

  const handleRemoveImage = useCallback((imageId) => {
    setAttachedImages(prev => prev.filter(img => img.id !== imageId));
  }, []);

  const handleRemoveText = useCallback((textId) => {
    setAttachedTexts(prev => prev.filter(t => t.id !== textId));
  }, []);

  // Paste handler - images, files, and long text
  const handlePaste = useCallback((e) => {
    const items = e.clipboardData?.items;
    const files = e.clipboardData?.files;

    // If there are actual files (from drag or file paste), process them with filenames
    if (files?.length > 0) {
      e.preventDefault();
      processFiles(files);
      return;
    }

    // Check for image or text file items
    if (items) {
      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        if (item.type.startsWith('image/')) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) processImageFile(file);
          return;
        }
        // Check for text files (e.g., .csv, .txt pasted from file manager)
        if (item.kind === 'file' && isTextFile({ type: item.type, name: '' })) {
          e.preventDefault();
          const file = item.getAsFile();
          if (file) processTextFile(file);
          return;
        }
      }
    }

    // Only treat as plain text paste if no files involved
    const pastedText = e.clipboardData.getData('text');
    if (pastedText && pastedText.length >= LONG_TEXT_THRESHOLD) {
      e.preventDefault();
      addTextAttachment(pastedText);
    }
  }, [processImageFile, processFiles, processTextFile, isTextFile, addTextAttachment]);

  const canSubmit = !disabled && (value.length > 0 || attachedImages.length > 0 || attachedTexts.length > 0);

  const handleKeyDown = useCallback((e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (canSubmit) {
        onSubmit(value.trim(), attachedImages, attachedTexts);
        setValue("");
        setAttachedImages([]);
        setAttachedTexts([]);
      }
    }
  }, [value, attachedImages, attachedTexts, canSubmit, onSubmit]);

  const handleSubmitClick = useCallback(() => {
    if (canSubmit) {
      onSubmit(value.trim(), attachedImages, attachedTexts);
      setValue("");
      setAttachedImages([]);
      setAttachedTexts([]);
    }
  }, [value, attachedImages, attachedTexts, canSubmit, onSubmit]);

  const handleAddPhotos = useCallback(() => {
    setAttachMenuAnchor(null);
    imageInputRef.current?.click();
  }, []);

  return (
    <Box
      sx={{
        mt: compact ? 0 : 1,
        mb: compact ? 0 : 4,
        display: "flex",
        flexDirection: "column",
        gap: 1,
        ...(compact ? {} : { minHeight: "16rem" }),
      }}
    >
      {/* Attachments preview */}
      <AnimatePresence>
        {(attachedImages.length > 0 || attachedTexts.length > 0) && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            style={{ overflowY: "clip", overflowX: "visible" }}
          >
            <Box sx={{
              display: "flex",
              gap: 1.5,
              mb: 1,
              pt: 1,
              pb: 0.5,
              overflowX: "auto",
              overflowY: "hidden",
              flexWrap: "nowrap",
              ml: -4,
              pl: 4,
              marginRight: "-36.5px",
              paddingRight: "36.5px",
              "&::-webkit-scrollbar": { display: "none" },
              scrollbarWidth: "none",
            }}>
              {/* Images */}
              {attachedImages.length > 0 && (
                <Box sx={{ display: "contents" }}>
                  {attachedImages.map(img => (
                    <Box
                      key={img.id}
                      onClick={() => setImageDialogOpen(img)}
                      sx={{
                        position: "relative",
                        width: 80,
                        height: 80,
                        flexShrink: 0,
                        cursor: "pointer",
                        "&:hover .remove-btn": { opacity: 1 },
                      }}
                    >
                      <Box sx={{
                        width: "100%",
                        height: "100%",
                        borderRadius: 1,
                        overflow: "hidden",
                        border: "1px solid rgba(0,0,0,0.1)",
                        "&:hover": { border: "1px solid rgba(0,0,0,0.25)" },
                      }}>
                        <img
                          src={img.preview}
                          alt={img.name}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      </Box>
                      <IconButton
                        className="remove-btn"
                        size="small"
                        onClick={(e) => { e.stopPropagation(); handleRemoveImage(img.id); }}
                        sx={{
                          position: "absolute",
                          top: -6,
                          right: -6,
                          backgroundColor: "rgba(0,0,0,0.6)",
                          color: "white",
                          padding: "2px",
                          opacity: 0,
                          transition: "opacity 0.15s",
                          "&:hover": { backgroundColor: "rgba(0,0,0,0.8)" },
                        }}
                      >
                        <X size={12} />
                      </IconButton>
                    </Box>
                  ))}
                </Box>
              )}

              {/* Text files */}
              {attachedTexts.length > 0 && (
                <Box sx={{ display: "contents" }}>
                  {attachedTexts.map(txt => {
                    // File type styles
                    const fileStyles = {
                      csv: { border: "#4CAF50", chip: "rgba(76, 175, 80, 0.15)", chipText: "#2e7d32" },
                      json: { border: "#FF9800", chip: "rgba(255, 152, 0, 0.15)", chipText: "#e65100" },
                      pdf: { border: "#F44336", chip: "rgba(244, 67, 54, 0.15)", chipText: "#c62828" },
                      txt: { border: "#42A5F5", chip: "rgba(66, 165, 245, 0.15)", chipText: "#1976d2" },
                      md: { border: "#2196F3", chip: "rgba(33, 150, 243, 0.15)", chipText: "#1565c0" },
                      xlsx: { border: "#217346", chip: "rgba(33, 115, 70, 0.15)", chipText: "#145a32" },
                      xls: { border: "#217346", chip: "rgba(33, 115, 70, 0.15)", chipText: "#145a32" },
                      sql: { border: "#9C27B0", chip: "rgba(156, 39, 176, 0.15)", chipText: "#7b1fa2" },
                      py: { border: "#3776AB", chip: "rgba(55, 118, 171, 0.15)", chipText: "#2c5f8a" },
                      js: { border: "#F7DF1E", chip: "rgba(247, 223, 30, 0.2)", chipText: "#8a7800" },
                      ts: { border: "#3178C6", chip: "rgba(49, 120, 198, 0.15)", chipText: "#235a9e" },
                      default: { border: "#9E9E9E", chip: "rgba(0,0,0,0.1)", chipText: "rgba(0,0,0,0.5)" },
                    };
                    const style = fileStyles[txt.ext] || fileStyles.default;
                    const extLabel = txt.ext || "txt";

                    return (
                    <Box
                      key={txt.id}
                      onClick={() => setTextDialogOpen(txt)}
                      sx={{
                        position: "relative",
                        cursor: "pointer",
                        width: 120,
                        flexShrink: 0,
                        mb: "4px",
                        "&:hover .remove-btn": { opacity: 1 },
                      }}
                    >
                      {/* Stacked back layer */}
                      <Box sx={{ position: "absolute", bottom: -4, left: 3, right: -3, top: 0, borderRadius: 0.75, backgroundColor: `${style.border}12`, border: `1px solid ${style.border}20` }} />
                      {/* Main card */}
                      <Box sx={{
                        position: "relative",
                        display: "flex",
                        flexDirection: "column",
                        p: 1.25,
                        height: 120,
                        borderRadius: 0.75,
                        backgroundColor: "var(--dm-surface, white)",
                        border: `1px solid ${style.border}30`,
                        boxShadow: `0 2px 8px ${style.border}12`,
                        overflow: "hidden",
                        transition: "all 0.2s",
                        "&:hover": { transform: "translateY(-2px)", boxShadow: `0 8px 20px ${style.border}20` },
                      }}>
                        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.75 }}>
                          <TextIcon size={12} style={{ color: style.border, flexShrink: 0 }} />
                          <Typography sx={{ fontSize: "0.7rem", fontWeight: 600, color: style.chipText, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", flex: 1 }}>
                            {txt.name || "Pasted"}
                          </Typography>
                        </Box>
                        <Box sx={{ flex: 1, overflow: "hidden" }}>
                          <Typography sx={{
                            fontSize: "0.6rem",
                            color: "rgba(0,0,0,0.45)",
                            lineHeight: 1.4,
                            overflow: "hidden",
                            display: "-webkit-box",
                            WebkitLineClamp: 3,
                            WebkitBoxOrient: "vertical",
                            wordBreak: "break-all",
                          }}>
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
                        onClick={(e) => { e.stopPropagation(); handleRemoveText(txt.id); }}
                        sx={{
                          position: "absolute",
                          top: -6,
                          right: -6,
                          zIndex: 2,
                          backgroundColor: style.border,
                          color: "white",
                          padding: "2px",
                          opacity: 0,
                          transition: "opacity 0.15s",
                          "&:hover": { backgroundColor: style.chipText },
                        }}
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

      {/* Input row */}
      <Box sx={{ display: "flex", alignItems: "flex-start", gap: 2, flex: 1 }}>
        <TextField
          inputRef={localInputRef}
          autoFocus
          variant="standard"
          placeholder={placeholder}
          multiline
          maxRows={8}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onPaste={handlePaste}
          fullWidth
          sx={{
            "& input, & textarea, & .MuiInput-input": {
              fontSize,
              fontWeight: "100 !important",
              color: isDarkBg ? "rgba(255,255,255,0.7)" : "rgba(0, 0, 0, 0.6)",
              paddingTop: "4px",
              lineHeight: 1.3,
            },
            "& .MuiInput-underline:before, & .MuiInput-underline:hover:not(.Mui-disabled):before, & .MuiInput-underline:after": {
              borderBottom: "none",
            },
          }}
        />
        <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}>
          <Tooltip title="Attach" placement="left">
            <IconButton
              onClick={(e) => setAttachMenuAnchor(e.currentTarget)}
              sx={{
                color: iconColor,
                opacity: 1,
                marginTop: "4px",
                "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
              }}
              size="medium"
            >
              <Paperclip style={{ fontSize: "1.5rem" }} />
            </IconButton>
          </Tooltip>
          {/* Model selector (mobile compact mode) */}
          {models && onModelChange && (
            <>
              <Tooltip title={selectedModel?.replace(/^[a-z]+\./, "") || "Select model"} placement="left">
                <IconButton
                  onClick={(e) => setModelMenuAnchor(e.currentTarget)}
                  sx={{
                    color: iconColor,
                    opacity: iconOpacity,
                    "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
                  }}
                  size="medium"
                >
                  <BrainFreezeIcon size={24} color={iconColor} />
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={modelMenuAnchor}
                open={Boolean(modelMenuAnchor)}
                onClose={() => setModelMenuAnchor(null)}
                PaperProps={{ sx: { maxHeight: 400 } }}
              >
                {(() => {
                  const groups = {};
                  models.forEach((m) => {
                    const provider = m.split(".")[0];
                    if (!groups[provider]) groups[provider] = [];
                    groups[provider].push(m);
                  });
                  const providerLabels = { openai: "OpenAI", xai: "xAI", google: "Google", cohere: "Cohere", meta: "Meta" };
                  return Object.entries(groups).flatMap(([provider, items]) => [
                    <ListSubheader
                      key={`ci-${provider}`}
                      sx={{
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        color: "rgba(0,0,0,0.4)",
                        letterSpacing: "0.08em",
                        textTransform: "uppercase",
                        lineHeight: "28px",
                        backgroundColor: "white",
                      }}
                    >
                      {providerLabels[provider] || provider}
                    </ListSubheader>,
                    ...items.map((m) => (
                      <MenuItem
                        key={m}
                        selected={selectedModel === m}
                        onClick={() => {
                          onModelChange(m);
                          setModelMenuAnchor(null);
                        }}
                        sx={{ fontSize: "0.95rem", pl: 3, display: "flex", alignItems: "center", gap: 1, fontWeight: selectedModel === m ? 600 : 400 }}
                      >
                        {m.replace(/^[a-z]+\./, "")}
                        {m === "xai.grok-4-1-fast-reasoning" && (
                          <Chip
                            label="Recommended"
                            size="small"
                            sx={{
                              fontSize: "0.6rem",
                              height: 18,
                              borderRadius: "4px",
                              bgcolor: "rgba(25, 118, 210, 0.1)",
                              color: "#1976d2",
                              fontWeight: 600,
                              letterSpacing: "0.03em",
                            }}
                          />
                        )}
                      </MenuItem>
                    )),
                  ]);
                })()}
              </Menu>
            </>
          )}
          {(() => {
            const badgeAppMode = typeof window !== 'undefined' ? (localStorage.getItem('appMode') || 'internal') : 'internal';
            const visibleServers = badgeAppMode === 'client' ? servers.filter(s => !s.isAddon) : servers;
            const totalTools = nativeTools.length + visibleServers.length;
            return (
              <Tooltip title="Tools" placement="left">
                <IconButton
                  onClick={(e) => setToolsMenuAnchor(e.currentTarget)}
                  sx={{
                    color: iconColor,
                    opacity: iconOpacity,
                    "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
                  }}
                  size="medium"
                >
                  <Wrench style={{ fontSize: "1.5rem" }} />
                </IconButton>
              </Tooltip>
            );
          })()}
          {/* Thinking effort selector — only for reasoning models */}
          {isReasoningModel && (
            <>
              <Tooltip title={`Thinking: ${reasoningEffort}`} placement="left">
                <IconButton
                  onClick={(e) => setThinkingMenuAnchor(e.currentTarget)}
                  sx={{
                    color: iconColor,
                    opacity: iconOpacity,
                    "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
                  }}
                  size="medium"
                >
                  <Badge
                    badgeContent={reasoningEffort === "off" ? "—" : reasoningEffort === "low" ? "L" : reasoningEffort === "high" ? "H" : "M"}
                    sx={{
                      "& .MuiBadge-badge": {
                        fontSize: "0.6rem",
                        fontWeight: 700,
                        height: 14,
                        minWidth: 14,
                        backgroundColor: "#999",
                        color: "white",
                      },
                    }}
                  >
                    <Brain size={20} />
                  </Badge>
                </IconButton>
              </Tooltip>
              <Menu
                anchorEl={thinkingMenuAnchor}
                open={Boolean(thinkingMenuAnchor)}
                onClose={() => setThinkingMenuAnchor(null)}
                slotProps={{
                  paper: {
                    sx: {
                      width: 160,
                      p: 0.5,
                      backgroundColor: isDarkBg ? "#242424" : "#fff",
                      color: isDarkBg ? "#e5e5e5" : "#1a1a1a",
                      border: isDarkBg ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.08)",
                    },
                  },
                }}
              >
                <Typography sx={{ fontSize: "0.6rem", fontWeight: 700, color: isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.35)", textTransform: "uppercase", letterSpacing: "0.08em", px: 1.5, py: 0.5 }}>
                  Thinking effort
                </Typography>
                {[
                  { value: "off", label: "Off", desc: "No thinking, fastest" },
                  { value: "low", label: "Low", desc: "Quick, simple tasks" },
                  { value: "medium", label: "Medium", desc: "Balanced (default)" },
                  { value: "high", label: "High", desc: "Complex reasoning" },
                ].map(opt => (
                  <MenuItem
                    key={opt.value}
                    selected={reasoningEffort === opt.value}
                    onClick={() => handleReasoningEffortChange(opt.value)}
                    sx={{
                      fontSize: "0.85rem",
                      borderRadius: 1,
                      mx: 0.5,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "flex-start",
                      py: 0.75,
                      color: isDarkBg ? "#e5e5e5" : "#1a1a1a",
                      "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)" },
                      "&.Mui-selected": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.06)" },
                      "&.Mui-selected:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.12)" : "rgba(0,0,0,0.08)" },
                    }}
                  >
                    <Typography sx={{ fontSize: "0.85rem", fontWeight: reasoningEffort === opt.value ? 600 : 400 }}>
                      {opt.label}
                    </Typography>
                    <Typography sx={{ fontSize: "0.68rem", color: isDarkBg ? "rgba(255,255,255,0.45)" : "rgba(0,0,0,0.4)" }}>
                      {opt.desc}
                    </Typography>
                  </MenuItem>
                ))}
              </Menu>
            </>
          )}
          <Tooltip title={isLoading ? "Stop generating" : "Send message"} placement="left" disableHoverListener={!isLoading && !canSubmit}>
            <IconButton
              sx={isLoading ? {
                color: iconColor,
                opacity: 1,
                pointerEvents: "auto",
                "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
              } : {
                color: iconColor,
                opacity: canSubmit ? 1 : 0,
                pointerEvents: canSubmit ? "auto" : "none",
                transition: "opacity 0.3s ease-in-out",
                "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)" },
              }}
              size="medium"
              onClick={isLoading ? onStop : handleSubmitClick}
            >
              {isLoading ? (
                <CircleStop size={20} />
              ) : (
                <KeyboardReturn sx={{ fontSize }} />
              )}
            </IconButton>
          </Tooltip>

          {/* Hidden file inputs */}
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={handleImageSelect}
            style={{ display: "none" }}
          />
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,.md,.json,.csv,.xml,.html,.css,.js,.ts,.jsx,.tsx,.py,.java,.c,.cpp,.h,.yml,.yaml,.toml,.ini,.log,.sql,.sh,.bat,.xlsx,.xls"
            multiple
            onChange={(e) => { processFiles(e.target.files); e.target.value = ''; }}
            style={{ display: "none" }}
          />

          {/* Attach menu */}
          <Menu
            anchorEl={attachMenuAnchor}
            open={Boolean(attachMenuAnchor)}
            onClose={() => setAttachMenuAnchor(null)}
          >
            <MenuItem onClick={handleAddPhotos} sx={{ fontSize: "0.9rem", gap: 1 }}>
              <ImagePlus size={16} />
              Add photos
            </MenuItem>
            <MenuItem onClick={() => { setAttachMenuAnchor(null); fileInputRef.current?.click(); }} sx={{ fontSize: "0.9rem", gap: 1 }}>
              <FileText size={16} />
              Add files
            </MenuItem>
          </Menu>

          {/* Tools menu */}
          <Menu
            anchorEl={toolsMenuAnchor}
            open={Boolean(toolsMenuAnchor)}
            onClose={() => setToolsMenuAnchor(null)}
            slotProps={{
              paper: {
                sx: {
                  width: 200,
                  p: 1,
                  pb: 0.5,
                  backgroundColor: isDarkBg ? "#242424" : "#fff",
                  color: isDarkBg ? "#e5e5e5" : "#1a1a1a",
                  border: isDarkBg ? "1px solid rgba(255,255,255,0.08)" : "1px solid rgba(0,0,0,0.08)",
                },
              },
            }}
          >
            {(() => {
              const isBrowser = typeof window !== 'undefined';
              const currentAppMode = isBrowser ? (localStorage.getItem('appMode') || 'internal') : 'internal';
              const isClientMode = currentAppMode === 'client';
              const addonEnabled = (() => { if (!isBrowser) return {}; try { return JSON.parse(localStorage.getItem('addonToolsEnabled') || '{}'); } catch { return {}; } })();
              const addonServers = isClientMode ? [] : servers.filter(s => s.isAddon && addonEnabled[s.id] !== false);
              const customServers = servers.filter(s => !s.isNative && !s.isAddon);
              const ragEnabled = nativeTools.includes('native_rag') && selectedVsNames.length > 0;
              const hasAny = nativeTools.length > 0 || addonServers.length > 0 || customServers.length > 0;

              if (!hasAny) {
                return (
                  <Box sx={{ px: 1, py: 1.5, textAlign: "center" }}>
                    <Typography sx={{ fontSize: "0.8rem", color: isDarkBg ? "rgba(255,255,255,0.45)" : "rgba(0,0,0,0.4)" }}>No tools active</Typography>
                  </Box>
                );
              }

              const ToolChip = ({ icon, label, color, bg, textColor }) => {
                const resolvedBg = bg || (isDarkBg ? `${color}22` : `${color}12`);
                const resolvedText = textColor || (isDarkBg ? "#e5e5e5" : color);
                return (
                  <Box sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 0.75,
                    px: 1.25,
                    py: 0.6,
                    borderRadius: 1,
                    backgroundColor: resolvedBg,
                    border: `1px solid ${color}${isDarkBg ? "40" : "25"}`,
                  }}>
                    <Box sx={{ flexShrink: 0, display: "flex" }}>{icon}</Box>
                    <Typography sx={{ fontSize: "0.78rem", fontWeight: 550, color: resolvedText, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 180 }}>{label}</Typography>
                  </Box>
                );
              };

              const SectionLabel = ({ label }) => (
                <Typography sx={{ fontSize: "0.6rem", fontWeight: 700, color: isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0,0,0,0.35)", textTransform: "uppercase", letterSpacing: "0.08em", px: 0.25, mb: 0.25 }}>
                  {label}
                </Typography>
              );

              const sections = [];

              if (nativeTools.length > 0) {
                sections.push(
                  <Box key="native" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                    <SectionLabel label="Native" />
                    {nativeTools.map(id => {
                      const meta = NATIVE_TOOLS_META[id];
                      if (!meta) return null;
                      const Icon = meta.icon;
                      return <ToolChip key={id} icon={<Icon size={14} color={meta.color} />} label={meta.name} color={meta.color} />;
                    })}
                  </Box>
                );
              }

              if (addonServers.length > 0) {
                sections.push(
                  <Box key="addons" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                    <SectionLabel label="Internal" />
                    {addonServers.map(server => {
                      const meta = ADDON_TOOLS_META[server.id];
                      const color = meta?.color || "#6B7280";
                      const iconColor = meta?.textColor || color;
                      const icon = meta?.LogoComponent
                        ? <meta.LogoComponent size={14} color={iconColor} />
                        : meta?.icon
                          ? <meta.icon size={14} color={iconColor} />
                          : <Puzzle size={14} color={iconColor} />;
                      return <ToolChip key={server.id} icon={icon} label={meta?.name || server.name} color={color} bg={meta?.bg} textColor={meta?.textColor} />;
                    })}
                  </Box>
                );
              }

              if (ragEnabled) {
                sections.push(
                  <Box key="knowledge" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                    <SectionLabel label="Knowledge" />
                    {selectedVsNames.map(vs => (
                      <ToolChip key={vs.id} icon={<FolderOpen size={14} color="#8B5CF6" />} label={vs.name} color="#8B5CF6" />
                    ))}
                  </Box>
                );
              }

              if (customServers.length > 0) {
                sections.push(
                  <Box key="custom" sx={{ display: "flex", flexDirection: "column", gap: 0.5 }}>
                    <SectionLabel label="Custom" />
                    {customServers.map(server => (
                      <ToolChip key={server.id} icon={<Plug size={14} color="#6B7280" />} label={server.name} color="#6B7280" />
                    ))}
                  </Box>
                );
              }

              return sections.map((section, i) => (
                <Box key={section.key}>
                  {i > 0 && <Divider sx={{ mx: -1, my: 0.75, borderColor: isDarkBg ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)" }} />}
                  {section}
                </Box>
              ));
            })()}
            <Divider sx={{ mx: -1, mt: 0.75, mb: 0.5, borderColor: isDarkBg ? "rgba(255,255,255,0.08)" : "rgba(0,0,0,0.08)" }} />
            <MenuItem
              onClick={() => {
                setToolsMenuAnchor(null);
                window.location.href = '/settings/tools';
              }}
              sx={{
                fontSize: "0.8rem",
                gap: 1,
                py: 0.5,
                minHeight: "auto",
                borderRadius: 1,
                color: isDarkBg ? "#e5e5e5" : "#1a1a1a",
                "&:hover": { backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)" },
              }}
            >
              <Settings size={13} />
              Manage tools
            </MenuItem>
          </Menu>
        </Box>
      </Box>

      {/* Text preview dialog */}
      <Dialog
        open={Boolean(textDialogOpen)}
        onClose={() => setTextDialogOpen(null)}
        maxWidth="md"
        fullWidth
        slotProps={{
          paper: { sx: { borderRadius: 2, maxHeight: "80vh" } }
        }}
      >
        <DialogContent sx={{ p: 0 }}>
          <Box sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            p: 2,
            pb: 1,
            borderBottom: "1px solid rgba(0,0,0,0.08)",
          }}>
            <Box>
              <Typography sx={{ fontWeight: 500, fontSize: "0.95rem", color: "rgba(0,0,0,0.8)" }}>
                {textDialogOpen?.name || "Pasted content"}
              </Typography>
              <Typography sx={{ fontSize: "0.75rem", color: "rgba(0,0,0,0.5)", mt: 0.25 }}>
                {textDialogOpen?.content && (
                  <>
                    {(new Blob([textDialogOpen.content]).size / 1024).toFixed(2)} KB • {textDialogOpen.content.split('\n').length.toLocaleString()} lines
                  </>
                )}
              </Typography>
            </Box>
            <Box sx={{ display: "flex", gap: 0.5, mt: -0.5, mr: -0.5 }}>
              <CopyButton content={textDialogOpen?.content} />
              <IconButton size="small" onClick={() => setTextDialogOpen(null)}>
                <X size={18} />
              </IconButton>
            </Box>
          </Box>
          <Box sx={{ p: 2, maxHeight: "60vh", overflow: "auto" }}>
            <Box sx={{ backgroundColor: "rgba(0,0,0,0.04)", borderRadius: 1.5, p: 2 }}>
              <Typography
                component="pre"
                sx={{
                  fontFamily: "monospace",
                  fontSize: "0.8rem",
                  color: "rgba(0,0,0,0.7)",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  m: 0,
                  lineHeight: 1.5,
                }}
              >
                {textDialogOpen?.content}
              </Typography>
            </Box>
          </Box>
        </DialogContent>
      </Dialog>

      {/* Image preview dialog */}
      <Dialog
        open={Boolean(imageDialogOpen)}
        onClose={() => setImageDialogOpen(null)}
        maxWidth="lg"
        slotProps={{
          paper: { sx: { borderRadius: 2, backgroundColor: "rgba(0,0,0,0.9)" } }
        }}
      >
        <DialogContent sx={{ p: 0, position: "relative" }}>
          <IconButton
            size="small"
            onClick={() => setImageDialogOpen(null)}
            sx={{
              position: "absolute",
              top: 8,
              right: 8,
              backgroundColor: "rgba(255,255,255,0.1)",
              color: "white",
              zIndex: 1,
              "&:hover": { backgroundColor: "rgba(255,255,255,0.2)" },
            }}
          >
            <X size={18} />
          </IconButton>
          {imageDialogOpen && (
            <img
              src={imageDialogOpen.preview}
              alt={imageDialogOpen.name}
              style={{
                maxWidth: "90vw",
                maxHeight: "85vh",
                objectFit: "contain",
                display: "block",
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
}));

export default ChatInput;
