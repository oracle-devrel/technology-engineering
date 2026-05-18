"use client";

import { Box, Checkbox, CircularProgress, FormControlLabel, InputAdornment, LinearProgress, MenuItem, Radio, RadioGroup, Rating, Select, Skeleton, Slider, Switch, TextField, Typography } from "@mui/material";
import { motion } from "framer-motion";
import {
  Sun, Cloud, CloudRain, CloudSnow, AlertCircle, Check, X, Info,
  Star, Heart, User, Users, Mail, Phone, MapPin, Clock, Calendar,
  Search, Settings, Home, File, Folder, Image as ImageIcon, Video,
  Music, Download, Upload, Link, Share, Edit, Trash, Plus, Minus,
  ArrowUp, ArrowDown, ArrowLeft, ArrowRight, Quote, Code, List, Send,
  Volume2, Presentation, Maximize2, ExternalLink, Play, Copy
} from "lucide-react";
import { useState, useCallback, useEffect, useMemo } from "react";
import { DataGrid } from "@mui/x-data-grid";
import { parseKey, INTERACTIVE_KEYS, CHART_KEYS } from "../../utils/widgetParser";
import { WidgetLineChart, WidgetBarChart, WidgetPieChart, WidgetDonutChart } from "./Charts";
import {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  BORDER,
  BUTTON,
  INPUT,
  ANIMATION,
  getColor,
  getSize,
} from "../../config/widgetTheme";

const ICONS = {
  sun: Sun, cloud: Cloud, rain: CloudRain, snow: CloudSnow,
  alert: AlertCircle, check: Check, x: X, info: Info,
  star: Star, heart: Heart, user: User, users: Users,
  mail: Mail, phone: Phone, map: MapPin, clock: Clock,
  calendar: Calendar, search: Search, settings: Settings, home: Home,
  file: File, folder: Folder, image: ImageIcon, video: Video,
  music: Music, download: Download, upload: Upload, link: Link,
  share: Share, edit: Edit, trash: Trash, plus: Plus, minus: Minus,
  "arrow-up": ArrowUp, "arrow-down": ArrowDown,
  "arrow-left": ArrowLeft, "arrow-right": ArrowRight,
  quote: Quote, code: Code, list: List, send: Send
};

function WidgetSkeleton({ type }) {
  const skeletonMap = {
    t: { width: "60%", height: 24 },
    s: { width: "40%", height: 18 },
    d: { width: "100%", height: 16, lines: 2 },
    i: { width: "100%", height: 120, variant: "rectangular" },
    ic: { width: 24, height: 24, variant: "circular" },
    n: { width: 80, height: 32 },
    p: { width: "100%", height: 8 },
    bt: { width: 100, height: 36, variant: "rectangular" },
    in: { width: "100%", height: 40, variant: "rectangular" },
    sl: { width: "100%", height: 40, variant: "rectangular" },
  };

  const config = skeletonMap[type] || { width: "50%", height: 20 };

  if (config.lines) {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: 0.5, width: "100%" }}>
        {Array.from({ length: config.lines }).map((_, i) => (
          <Skeleton key={i} variant="text" width={i === config.lines - 1 ? "60%" : config.width} height={config.height} sx={{ bgcolor: "rgba(0,0,0,0.06)" }} />
        ))}
      </Box>
    );
  }

  return <Skeleton variant={config.variant || "text"} width={config.width} height={config.height} sx={{ bgcolor: "rgba(0,0,0,0.06)", borderRadius: config.variant === "rectangular" ? 1 : undefined }} />;
}

function WidgetIcon({ name, size = 24, color }) {
  const IconComponent = ICONS[name];
  if (!IconComponent) return null;
  return (
    <motion.div
      initial={{ scale: 0.5, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3, delay: 0.05, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <IconComponent size={size} color={color} />
    </motion.div>
  );
}

function WidgetImage({ src, position }) {
  const isUrl = src.startsWith('http://') || src.startsWith('https://') || src.startsWith('/');
  if (!isUrl) return null;

  if (position === "bg") {
    return (
      <Box sx={{ position: "absolute", inset: 0, backgroundImage: `url(${src})`, backgroundSize: "cover", backgroundPosition: "center", borderRadius: "inherit", zIndex: 0, "&::after": { content: '""', position: "absolute", inset: 0, background: "linear-gradient(to bottom, rgba(0,0,0,0.1), rgba(0,0,0,0.5))", borderRadius: "inherit" } }} />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{ width: "100%" }}
    >
      <Box component="img" src={src} sx={{ width: "100%", maxHeight: 200, objectFit: "cover", borderRadius: 1 }} onError={(e) => { e.target.style.display = "none"; }} />
    </motion.div>
  );
}

function WidgetProgress({ value, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, scaleX: 0.8 }}
      animate={{ opacity: 1, scaleX: 1 }}
      transition={{ duration: 0.4, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{ width: "100%", transformOrigin: "left" }}
    >
      <Box sx={{ width: "100%", mt: 1 }}>
        <LinearProgress variant="determinate" value={parseInt(value) || 0} sx={{ height: 8, borderRadius: 4, backgroundColor: "rgba(0,0,0,0.08)", "& .MuiLinearProgress-bar": { backgroundColor: color || COLORS.primary, borderRadius: 4, transition: "transform 0.6s ease-out" } }} />
      </Box>
    </motion.div>
  );
}

function WidgetList({ items }) {
  const listItems = items.split(";").filter(Boolean);
  return (
    <Box component="ul" sx={{ m: 0, pl: 2.5, fontFamily: TYPOGRAPHY.fontFamily, "& li": { mb: 0.5 } }}>
      {listItems.map((item, i) => (
        <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.1 }} style={{ fontSize: "0.9rem", fontFamily: TYPOGRAPHY.fontFamily }}>{item.trim()}</motion.li>
      ))}
    </Box>
  );
}

function WidgetLinks({ links, color }) {
  // Format: "Label>url;Label2>url2" or just "url1;url2"
  const linkItems = links.split(";").filter(Boolean).map(item => {
    const trimmed = item.trim();
    if (trimmed.includes(">")) {
      const [label, url] = trimmed.split(">");
      return { label: label.trim(), url: url.trim() };
    }
    // If no label, use the URL as label (simplified)
    const url = trimmed;
    const label = url.replace(/^https?:\/\//, "").split("/")[0];
    return { label, url };
  });

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 0.75, mt: 0.5 }}>
      {linkItems.map((item, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: i * 0.08, duration: 0.3 }}
        >
          <Box
            component="a"
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              display: "inline-flex",
              alignItems: "center",
              gap: 0.75,
              color: COLORS.primary,
              textDecoration: "none",
              fontSize: "0.9rem",
              fontWeight: 500,
              transition: "opacity 0.2s",
              "&:hover": { opacity: 0.7 },
            }}
          >
            <Link size={14} />
            {item.label}
          </Box>
        </motion.div>
      ))}
    </Box>
  );
}

function WidgetCode({ code }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box component="pre" sx={{ backgroundColor: "#1e1e1e", color: "#d4d4d4", p: 1.5, borderRadius: 1, fontSize: "0.8rem", fontFamily: "monospace", overflow: "auto", m: 0, mt: 1 }}>
        <code>{code}</code>
      </Box>
    </motion.div>
  );
}

function WidgetQuote({ text, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, delay: 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box sx={{ borderLeft: `3px solid ${color || COLORS.palette.p}`, pl: 2, py: 0.5, fontStyle: "italic", color: COLORS.text.secondary }}>
        &ldquo;{text}&rdquo;
      </Box>
    </motion.div>
  );
}

function WidgetAudio({ src, color }) {
  // src can be: base64 data URL, raw base64 string, or regular URL
  const [audioSrc, setAudioSrc] = useState(null);

  useEffect(() => {
    if (!src) return;

    // If it's already a data URL or regular URL, use it directly
    if (src.startsWith('data:') || src.startsWith('http://') || src.startsWith('https://') || src.startsWith('/')) {
      setAudioSrc(src);
    } else {
      // Assume it's raw base64 - try to detect format or default to mp3
      setAudioSrc(`data:audio/mp3;base64,${src}`);
    }
  }, [src]);

  if (!audioSrc) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay: 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
      style={{ width: "100%", minWidth: 320 }}
    >
      <audio
        controls
        src={audioSrc}
        style={{
          width: "100%",
          height: 36,
          borderRadius: 8,
        }}
      />
    </motion.div>
  );
}

// Status card configuration - using theme colors
const STATUS_CONFIG = {
  success: { icon: "check", color: COLORS.success, bgColor: "rgba(76, 130, 92, 0.12)" },  // Pine 100
  error: { icon: "x", color: COLORS.error, bgColor: "rgba(199, 70, 52, 0.1)" },  // Oracle Red
  warning: { icon: "alert", color: COLORS.warning, bgColor: "rgba(241, 177, 63, 0.12)" },  // Brand Yellow
  info: { icon: "info", color: COLORS.info, bgColor: "rgba(53, 83, 92, 0.1)" },  // Pine 140
};

// Convert URLs in text to clickable <a> links
function linkifyText(text) {
  if (!text || typeof text !== 'string') return text;
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  if (parts.length === 1) return text;
  return parts.map((part, i) =>
    urlRegex.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noopener noreferrer" style={{ color: COLORS.info, wordBreak: "break-all" }}>{part}</a>
    ) : part
  );
}

function WidgetStatusCard({ status, title, description, buttons, onButtonClick, clickedButton, loadingButton, disabled }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.info;
  const IconComponent = ICONS[config.icon];

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 2,
          p: 3,
          backgroundColor: COLORS.background.widget,
          borderRadius: 3,
          minWidth: 280,
          maxWidth: 400,
        }}
      >
        {/* Circular icon badge */}
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.1, duration: 0.4, type: "spring", stiffness: 200 }}
        >
          <Box
            sx={{
              width: 64,
              height: 64,
              borderRadius: "50%",
              backgroundColor: config.bgColor,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {IconComponent && <IconComponent size={32} color={config.color} />}
          </Box>
        </motion.div>

        {/* Title and description */}
        <Box sx={{ textAlign: "center" }}>
          {title && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.3 }}
            >
              <Typography sx={{ fontSize: "1.1rem", fontWeight: 600, color: COLORS.text.primary, mb: 0.5 }}>
                {title}
              </Typography>
            </motion.div>
          )}
          {description && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.3 }}
            >
              <Typography sx={{ fontSize: "0.9rem", color: COLORS.text.secondary, lineHeight: 1.5, wordBreak: "break-word", overflowWrap: "break-word" }}>
                {linkifyText(description)}
              </Typography>
            </motion.div>
          )}
        </Box>

        {/* Buttons row */}
        {buttons && buttons.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35, duration: 0.3 }}
            style={{ width: "100%" }}
          >
            <Box sx={{ display: "flex", gap: 1.5, width: "100%", mt: 1 }}>
              {buttons.map((btn, i) => {
                const isPrimary = i === 0;
                const isThisClicked = clickedButton === btn;
                const isAnyClicked = clickedButton !== null || disabled;

                return (
                  <button
                    key={i}
                    onClick={() => !isAnyClicked && onButtonClick(btn)}
                    disabled={isAnyClicked}
                    style={{
                      flex: 1,
                      padding: "10px 16px",
                      backgroundColor: isPrimary ? config.color : "transparent",
                      color: isPrimary ? "#fff" : config.color,
                      border: isPrimary ? "none" : `1.5px solid ${config.color}`,
                      borderRadius: 8,
                      fontSize: "0.9rem",
                      fontWeight: 500,
                      cursor: isAnyClicked ? "default" : "pointer",
                      opacity: isAnyClicked && !isThisClicked ? 0.5 : 1,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 6,
                      transition: "all 0.2s ease",
                    }}
                  >
                    {loadingButton === btn ? (
                      <CircularProgress size={16} sx={{ color: isPrimary ? "#fff" : config.color }} />
                    ) : (
                      <>
                        {isThisClicked && "✓ "}
                        {btn}
                      </>
                    )}
                  </button>
                );
              })}
            </Box>
          </motion.div>
        )}
      </Box>
    </motion.div>
  );
}

// Interactive Components
function WidgetInput({ placeholder, value, onChange, onEnter, disabled }) {
  return (
    <TextField
      size="small"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter" && onEnter && !disabled) {
          e.preventDefault();
          onEnter();
        }
      }}
      disabled={disabled}
      fullWidth
      sx={{
        "& .MuiOutlinedInput-root": {
          backgroundColor: INPUT.backgroundColor,
          "& fieldset": { border: INPUT.border },
          "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
          "&.Mui-focused": { backgroundColor: INPUT.hoverBackground }
        }
      }}
    />
  );
}

function WidgetSelect({ options, value, onChange, disabled }) {
  let label = null;
  let opts = options;

  // Check for label with ? separator
  if (options.includes("?")) {
    const parts = options.split("?");
    label = parts[0].trim();
    opts = parts.slice(1).join("?"); // In case there are ? in options
  }

  const optList = opts.split(";").filter(Boolean);

  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <Select
        size="small"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        displayEmpty
        fullWidth
        disabled={disabled}
        sx={{
          backgroundColor: INPUT.backgroundColor,
          "& .MuiOutlinedInput-notchedOutline": { border: INPUT.border },
          "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
          "&.Mui-focused": { backgroundColor: INPUT.hoverBackground }
        }}
      >
        <MenuItem value="" disabled><em>Select...</em></MenuItem>
        {optList.map((opt, i) => <MenuItem key={i} value={opt.trim()}>{opt.trim()}</MenuItem>)}
      </Select>
    </Box>
  );
}

function WidgetCheckbox({ label, checked, onChange, disabled }) {
  return (
    <FormControlLabel
      control={<Checkbox checked={checked} onChange={(e) => onChange(e.target.checked)} disabled={disabled} sx={{ color: COLORS.text.muted, "&.Mui-checked": { color: COLORS.secondary } }} />}
      label={label}
      disabled={disabled}
      sx={{ "& .MuiFormControlLabel-label": { fontSize: BUTTON.fontSize } }}
    />
  );
}

function WidgetRange({ range, value, onChange, disabled }) {
  const [min, max] = range.split("-").map(n => parseInt(n) || 0);
  return (
    <Box sx={{ width: "100%", px: 1 }}>
      <Slider
        value={value ?? min}
        min={min}
        max={max}
        onChange={(_, v) => onChange(v)}
        disabled={disabled}
        sx={{
          color: COLORS.secondary,
          "& .MuiSlider-thumb": {
            "&:hover, &.Mui-focusVisible": { boxShadow: `0 0 0 8px ${COLORS.background.hover}` }
          },
          "& .MuiSlider-track": { backgroundColor: COLORS.secondary },
          "& .MuiSlider-rail": { backgroundColor: COLORS.background.hover }
        }}
      />
      <Typography variant="caption" sx={{ color: COLORS.text.muted }}>{value ?? min}</Typography>
    </Box>
  );
}

// Radio buttons for single selection
function WidgetRadio({ options, value, onChange, disabled }) {
  let label = null;
  let opts = options;

  if (options.includes("?")) {
    const parts = options.split("?");
    label = parts[0].trim();
    opts = parts.slice(1).join("?");
  }

  const optList = opts.split(";").filter(Boolean);

  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <RadioGroup value={value || ""} onChange={(e) => onChange(e.target.value)}>
        {optList.map((opt, i) => (
          <FormControlLabel
            key={i}
            value={opt.trim()}
            control={<Radio disabled={disabled} size="small" sx={{ color: COLORS.text.muted, "&.Mui-checked": { color: COLORS.secondary } }} />}
            label={opt.trim()}
            disabled={disabled}
            sx={{ "& .MuiFormControlLabel-label": { fontSize: "0.9rem" } }}
          />
        ))}
      </RadioGroup>
    </Box>
  );
}

// Multi-select dropdown
function WidgetMultiSelect({ options, value, onChange, disabled }) {
  let label = null;
  let opts = options;

  if (options.includes("?")) {
    const parts = options.split("?");
    label = parts[0].trim();
    opts = parts.slice(1).join("?");
  }

  const optList = opts.split(";").filter(Boolean);
  const selectedValues = value || [];

  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <Select
        size="small"
        multiple
        value={selectedValues}
        onChange={(e) => onChange(e.target.value)}
        displayEmpty
        fullWidth
        disabled={disabled}
        renderValue={(selected) => selected.length === 0 ? <em>Select...</em> : selected.join(", ")}
        sx={{
          backgroundColor: INPUT.backgroundColor,
          "& .MuiOutlinedInput-notchedOutline": { border: INPUT.border },
          "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
        }}
      >
        {optList.map((opt, i) => (
          <MenuItem key={i} value={opt.trim()}>
            <Checkbox checked={selectedValues.includes(opt.trim())} size="small" />
            {opt.trim()}
          </MenuItem>
        ))}
      </Select>
    </Box>
  );
}

// Date picker
function WidgetDate({ label, value, onChange, disabled }) {
  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <TextField
        type="date"
        size="small"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        fullWidth
        sx={{
          "& .MuiOutlinedInput-root": {
            backgroundColor: INPUT.backgroundColor,
            "& fieldset": { border: INPUT.border },
            "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
          }
        }}
      />
    </Box>
  );
}

// Time picker
function WidgetTime({ label, value, onChange, disabled }) {
  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <TextField
        type="time"
        size="small"
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        fullWidth
        sx={{
          "& .MuiOutlinedInput-root": {
            backgroundColor: INPUT.backgroundColor,
            "& fieldset": { border: INPUT.border },
            "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
          }
        }}
      />
    </Box>
  );
}

// Star rating
function WidgetRating({ label, max, value, onChange, disabled }) {
  const maxStars = parseInt(max) || 5;
  return (
    <Box sx={{ width: "100%" }}>
      {label && (
        <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mb: 0.5 }}>
          {label}
        </Typography>
      )}
      <Rating
        value={value || 0}
        max={maxStars}
        onChange={(_, v) => onChange(v)}
        disabled={disabled}
        sx={{ color: COLORS.warning }}
      />
    </Box>
  );
}

// Toggle switch
function WidgetToggle({ label, checked, onChange, disabled }) {
  return (
    <FormControlLabel
      control={
        <Switch
          checked={checked || false}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          sx={{
            "& .MuiSwitch-switchBase.Mui-checked": { color: COLORS.secondary },
            "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": { backgroundColor: COLORS.secondary },
          }}
        />
      }
      label={label}
      disabled={disabled}
      sx={{ "& .MuiFormControlLabel-label": { fontSize: "0.9rem" } }}
    />
  );
}

// Textarea (multiline input)
function WidgetTextarea({ placeholder, value, onChange, disabled, rows = 3 }) {
  return (
    <TextField
      size="small"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      multiline
      rows={rows}
      fullWidth
      sx={{
        "& .MuiOutlinedInput-root": {
          backgroundColor: INPUT.backgroundColor,
          "& fieldset": { border: INPUT.border },
          "&:hover": { backgroundColor: disabled ? INPUT.backgroundColor : INPUT.hoverBackground },
          "&.Mui-focused": { backgroundColor: INPUT.hoverBackground }
        }
      }}
    />
  );
}

// Row form layout - renders interactive elements in key-value rows
function WidgetRowForm({
  props,
  formState,
  updateFormState,
  handleButtonClick,
  clickedButton,
  loadingButton,
  disabled,
  themeColor,
}) {
  // Get all keys in order, filtering out style keys
  const allKeys = Object.keys(props).filter(k => !k.startsWith("_"));

  // Separate into fields (non-buttons) and buttons
  const fieldKeys = allKeys.filter(k => {
    const base = k.replace(/\d+$/, "");
    return base !== "bt" && base !== "t" && base !== "d" && base !== "s";
  });
  const buttonKeys = allKeys.filter(k => k.startsWith("bt"));
  const hasTitle = props.t || props.s;

  // Helper to extract label, options, and default value from value string
  // Formats: "Label", "Label=default", "Label?opts", "Label?opts=default"
  const parseFieldValue = (value) => {
    let label = value;
    let options = value;
    let defaultValue = null;

    // First, extract default value (after =)
    if (value.includes("=")) {
      const eqIndex = value.lastIndexOf("=");
      defaultValue = value.substring(eqIndex + 1).trim();
      value = value.substring(0, eqIndex);
    }

    // Then extract label and options (before/after ?)
    if (value.includes("?")) {
      label = value.split("?")[0].trim();
      options = value.split("?").slice(1).join("?");
    } else {
      label = value;
      options = value;
    }

    return { label, options, defaultValue };
  };

  // Legacy helpers for backwards compatibility
  const extractLabel = (value) => parseFieldValue(value).label;
  const extractOptions = (value) => parseFieldValue(value).options;

  // Render a single row with label and component
  const renderRow = (key, index) => {
    const base = key.replace(/\d+$/, "");
    const value = props[key];
    const { label, options, defaultValue } = parseFieldValue(value);
    const isFormDisabled = disabled || clickedButton !== null || loadingButton !== null;
    const isLastField = index === fieldKeys.length - 1;

    let component = null;

    switch (base) {
      case "in":
        const inputVal = formState[label] !== undefined ? formState[label] : (defaultValue || "");
        component = (
          <WidgetInput
            placeholder=""
            value={inputVal}
            onChange={(v) => updateFormState(label, v)}
            disabled={isFormDisabled}
          />
        );
        break;

      case "ta":
        // Convert literal \n to actual newlines for textarea defaults
        const taDefault = defaultValue ? defaultValue.replace(/\\n/g, '\n') : "";
        const taVal = formState[label] !== undefined ? formState[label] : taDefault;
        component = (
          <WidgetTextarea
            placeholder=""
            value={taVal}
            onChange={(v) => updateFormState(label, v)}
            disabled={isFormDisabled}
          />
        );
        break;

      case "sl":
        const selectKey = `select_${key}`;
        const selectVal = formState[selectKey] !== undefined ? formState[selectKey] : (defaultValue || "");
        component = (
          <Select
            size="small"
            value={selectVal}
            onChange={(e) => updateFormState(selectKey, e.target.value)}
            displayEmpty
            fullWidth
            disabled={isFormDisabled}
            sx={{
              backgroundColor: INPUT.backgroundColor,
              "& .MuiOutlinedInput-notchedOutline": { border: INPUT.border },
              "&:hover": { backgroundColor: isFormDisabled ? INPUT.backgroundColor : INPUT.hoverBackground },
            }}
          >
            {!defaultValue && <MenuItem value="" disabled><em>Select...</em></MenuItem>}
            {options.split(";").filter(Boolean).map((opt, i) => (
              <MenuItem key={i} value={opt.trim()}>{opt.trim()}</MenuItem>
            ))}
          </Select>
        );
        break;

      case "dt":
        const dateKey = `date_${key}`;
        const dateVal = formState[dateKey] !== undefined ? formState[dateKey] : (defaultValue || "");
        component = (
          <TextField
            type="date"
            size="small"
            value={dateVal}
            onChange={(e) => updateFormState(dateKey, e.target.value)}
            disabled={isFormDisabled}
            fullWidth
            sx={{
              "& .MuiOutlinedInput-root": {
                backgroundColor: INPUT.backgroundColor,
                "& fieldset": { border: INPUT.border },
              }
            }}
          />
        );
        break;

      case "tm":
        const timeKey = `time_${key}`;
        const timeVal = formState[timeKey] !== undefined ? formState[timeKey] : (defaultValue || "");
        component = (
          <TextField
            type="time"
            size="small"
            value={timeVal}
            onChange={(e) => updateFormState(timeKey, e.target.value)}
            disabled={isFormDisabled}
            fullWidth
            sx={{
              "& .MuiOutlinedInput-root": {
                backgroundColor: INPUT.backgroundColor,
                "& fieldset": { border: INPUT.border },
              }
            }}
          />
        );
        break;

      case "tg":
        const toggleKey = `toggle_${key}`;
        const toggleRaw = formState[toggleKey] !== undefined ? formState[toggleKey] : (defaultValue === "true" || defaultValue === "1");
        const toggleVal = toggleRaw === true || toggleRaw === "true" || toggleRaw === "1";
        component = (
          <Switch
            checked={toggleVal}
            onChange={(e) => updateFormState(toggleKey, e.target.checked)}
            disabled={isFormDisabled}
            sx={{
              "& .MuiSwitch-switchBase.Mui-checked": { color: COLORS.secondary },
              "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": { backgroundColor: COLORS.secondary },
            }}
          />
        );
        break;

      case "cb":
        const cbRaw = formState[label] !== undefined ? formState[label] : (defaultValue === "true" || defaultValue === "1");
        const cbVal = cbRaw === true || cbRaw === "true" || cbRaw === "1";
        component = (
          <Checkbox
            checked={cbVal}
            onChange={(e) => updateFormState(label, e.target.checked)}
            disabled={isFormDisabled}
            sx={{ color: COLORS.text.muted, "&.Mui-checked": { color: COLORS.secondary } }}
          />
        );
        break;

      case "rg":
        const rangeKey = `range_${key}`;
        const [min, max] = options.split("-").map(n => parseInt(n) || 0);
        const rangeDefault = defaultValue ? parseInt(defaultValue) : min;
        const rangeVal = formState[rangeKey] !== undefined ? formState[rangeKey] : rangeDefault;
        component = (
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, width: "100%" }}>
            <Slider
              value={rangeVal}
              min={min}
              max={max}
              onChange={(_, v) => updateFormState(rangeKey, v)}
              disabled={isFormDisabled}
              sx={{ color: COLORS.secondary, flex: 1 }}
            />
            <Typography variant="caption" sx={{ color: COLORS.text.muted, minWidth: 30 }}>
              {rangeVal}
            </Typography>
          </Box>
        );
        break;

      default:
        return null;
    }

    if (!component) return null;

    return (
      <motion.div
        key={key}
        initial={{ opacity: 0, x: -10 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.3, delay: index * 0.05 }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: base === "ta" ? "flex-start" : "center",
            gap: 2,
            py: 1.5,
            borderBottom: isLastField ? "none" : `1px solid ${COLORS.background.hover}`,
          }}
        >
          <Typography
            sx={{
              fontSize: "0.9rem",
              fontWeight: 500,
              color: COLORS.text.secondary,
              minWidth: 100,
              flexShrink: 0,
              pt: base === "ta" ? 1 : 0,
            }}
          >
            {label}
          </Typography>
          <Box sx={{ flex: 1 }}>
            {component}
          </Box>
        </Box>
      </motion.div>
    );
  };

  return (
    <Box
      sx={{
        backgroundColor: COLORS.background.widget,
        borderRadius: 3,
        p: 2.5,
        minWidth: 320,
      }}
    >
      {/* Title/subtitle header */}
      {hasTitle && (
        <Box sx={{ mb: 2, pb: 1.5, borderBottom: `1px solid ${COLORS.background.hover}` }}>
          {props.t && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <Typography sx={{ fontSize: "1.1rem", fontWeight: 600, color: COLORS.text.primary }}>
                {props.t}
              </Typography>
            </motion.div>
          )}
          {props.s && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.05 }}
            >
              <Typography sx={{ fontSize: "0.85rem", color: COLORS.text.secondary, mt: 0.5 }}>
                {props.s}
              </Typography>
            </motion.div>
          )}
        </Box>
      )}

      {/* Field rows */}
      <Box>
        {fieldKeys.map((key, index) => renderRow(key, index))}
      </Box>

      {/* Buttons row */}
      {buttonKeys.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: fieldKeys.length * 0.05 }}
        >
          <Box sx={{ display: "flex", gap: 1.5, mt: 2, pt: 1.5, borderTop: `1px solid ${COLORS.background.hover}` }}>
            {buttonKeys.map((key, i) => {
              const label = props[key];
              const isPrimary = i === 0;
              const isThisClicked = clickedButton === label;
              const isAnyClicked = clickedButton !== null || disabled;

              return (
                <button
                  key={key}
                  onClick={() => !isAnyClicked && handleButtonClick(label, buttonKeys.length === 1)}
                  disabled={isAnyClicked}
                  style={{
                    flex: isPrimary ? 1 : "none",
                    padding: "10px 20px",
                    backgroundColor: isPrimary ? themeColor : "transparent",
                    color: isPrimary ? "#fff" : themeColor,
                    border: isPrimary ? "none" : `1.5px solid ${themeColor}`,
                    borderRadius: 8,
                    fontSize: "0.9rem",
                    fontWeight: 500,
                    cursor: isAnyClicked ? "default" : "pointer",
                    opacity: isAnyClicked && !isThisClicked ? 0.5 : 1,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    gap: 6,
                  }}
                >
                  {loadingButton === label ? (
                    <CircularProgress size={16} sx={{ color: isPrimary ? "#fff" : themeColor }} />
                  ) : (
                    <>
                      {isThisClicked && "✓ "}
                      {label}
                    </>
                  )}
                </button>
              );
            })}
          </Box>
        </motion.div>
      )}
    </Box>
  );
}

// Calendar/Agenda Widget
function WidgetCalendar({ props }) {
  // Parse days and events from props
  // Format: dy:Mon,3 for day, ev:Title,Time,Color for events
  const days = [];
  let currentDay = null;

  // Get all keys in order
  const allKeys = Object.keys(props);

  for (const key of allKeys) {
    const baseKey = key.replace(/\d+$/, '');
    const value = props[key];

    if (baseKey === 'dy') {
      // Parse day: DayName,DayNumber
      const parts = value.split(',');
      currentDay = {
        name: parts[0]?.trim() || '',
        number: parts[1]?.trim() || '',
        events: []
      };
      days.push(currentDay);
    } else if (baseKey === 'ev' && currentDay) {
      // Parse event: Title,Time,Color
      const parts = value.split(',');
      currentDay.events.push({
        title: parts[0]?.trim() || '',
        time: parts[1]?.trim() || '',
        color: getColor(parts[2]?.trim()) || COLORS.primary
      });
    }
  }

  if (days.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 3,
          overflow: 'hidden',
          minWidth: 280,
        }}
      >
        {/* Optional title */}
        {props.t && (
          <Box sx={{ px: 2.5, pt: 2, pb: 1 }}>
            <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary }}>
              {props.t}
            </Typography>
          </Box>
        )}

        {/* Days */}
        <Box sx={{ display: 'flex', flexDirection: 'column' }}>
          {days.map((day, dayIndex) => (
            <motion.div
              key={dayIndex}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: dayIndex * 0.1, duration: 0.3 }}
            >
              <Box
                sx={{
                  display: 'flex',
                  borderTop: dayIndex > 0 ? `1px solid ${COLORS.background.hover}` : 'none',
                }}
              >
                {/* Day column */}
                <Box
                  sx={{
                    width: 70,
                    py: 2,
                    px: 2,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'flex-start',
                    backgroundColor: 'rgba(0,0,0,0.02)',
                    borderRight: `1px solid ${COLORS.background.hover}`,
                  }}
                >
                  <Typography
                    sx={{
                      fontSize: '0.75rem',
                      fontWeight: 500,
                      color: COLORS.text.secondary,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {day.name}
                  </Typography>
                  <Typography
                    sx={{
                      fontSize: '1.5rem',
                      fontWeight: 700,
                      color: COLORS.text.primary,
                      lineHeight: 1.2,
                    }}
                  >
                    {day.number}
                  </Typography>
                </Box>

                {/* Events column */}
                <Box sx={{ flex: 1, py: 1.5, px: 2 }}>
                  {day.events.length > 0 ? (
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {day.events.map((event, eventIndex) => (
                        <motion.div
                          key={eventIndex}
                          initial={{ opacity: 0, x: -5 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: dayIndex * 0.1 + eventIndex * 0.05, duration: 0.2 }}
                        >
                          <Box
                            sx={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: 1.5,
                            }}
                          >
                            {/* Color indicator */}
                            <Box
                              sx={{
                                width: 4,
                                height: 32,
                                borderRadius: 2,
                                backgroundColor: event.color,
                                flexShrink: 0,
                              }}
                            />
                            {/* Event details */}
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography
                                sx={{
                                  fontSize: '0.9rem',
                                  fontWeight: 500,
                                  color: COLORS.text.primary,
                                  lineHeight: 1.3,
                                }}
                              >
                                {event.title}
                              </Typography>
                              <Typography
                                sx={{
                                  fontSize: '0.8rem',
                                  color: COLORS.text.secondary,
                                }}
                              >
                                {event.time}
                              </Typography>
                            </Box>
                          </Box>
                        </motion.div>
                      ))}
                    </Box>
                  ) : (
                    <Typography sx={{ fontSize: '0.85rem', color: COLORS.text.muted, py: 1 }}>
                      No events
                    </Typography>
                  )}
                </Box>
              </Box>
            </motion.div>
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}

// Timeline Widget - Shows phases with dates
function WidgetTimeline({ props }) {
  const phases = [];
  const allKeys = Object.keys(props);
  const isHorizontal = props._dir === 'h' || props._dir === 'horizontal';

  for (const key of allKeys) {
    const baseKey = key.replace(/\d+$/, '');
    const value = props[key];

    if (baseKey === 'ph') {
      // Parse phase: Name,DateRange
      const parts = value.split(',');
      phases.push({
        name: parts[0]?.trim() || '',
        date: parts.slice(1).join(',').trim() || '',
      });
    }
  }

  if (phases.length === 0) return null;

  // Horizontal Timeline Layout
  if (isHorizontal) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      >
        <Box
          sx={{
            backgroundColor: COLORS.background.widget,
            borderRadius: 3,
            p: 2.5,
            minWidth: 280,
          }}
        >
          {props.t && (
            <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary, mb: 2 }}>
              {props.t}
            </Typography>
          )}

          <Box sx={{ position: 'relative', pt: 2 }}>
            {/* Horizontal line */}
            <Box
              sx={{
                position: 'absolute',
                left: 20,
                right: 20,
                top: 24,
                height: 2,
                backgroundColor: COLORS.background.hover,
                borderRadius: 1,
              }}
            />

            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              {phases.map((phase, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1, duration: 0.3 }}
                  style={{ flex: 1, textAlign: 'center', position: 'relative' }}
                >
                  {/* Dot */}
                  <Box
                    sx={{
                      width: 12,
                      height: 12,
                      borderRadius: '50%',
                      backgroundColor: index === 0 ? COLORS.primary : COLORS.background.hover,
                      border: `2px solid ${index === 0 ? COLORS.primary : COLORS.text.muted}`,
                      margin: '0 auto',
                      mb: 1.5,
                      position: 'relative',
                      zIndex: 1,
                    }}
                  />

                  <Typography
                    sx={{
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color: COLORS.text.primary,
                      lineHeight: 1.3,
                    }}
                  >
                    {phase.name}
                  </Typography>
                  {phase.date && (
                    <Typography
                      sx={{
                        fontSize: '0.75rem',
                        color: COLORS.text.secondary,
                        mt: 0.25,
                      }}
                    >
                      {phase.date}
                    </Typography>
                  )}
                </motion.div>
              ))}
            </Box>
          </Box>
        </Box>
      </motion.div>
    );
  }

  // Vertical Timeline Layout (default)
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 3,
          p: 2.5,
          minWidth: 280,
        }}
      >
        {props.t && (
          <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary, mb: 2 }}>
            {props.t}
          </Typography>
        )}

        <Box sx={{ position: 'relative', pl: 3 }}>
          {/* Vertical line */}
          <Box
            sx={{
              position: 'absolute',
              left: 2,
              top: 8,
              bottom: 8,
              width: 2,
              backgroundColor: COLORS.background.hover,
              borderRadius: 1,
            }}
          />

          {phases.map((phase, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1, duration: 0.3 }}
            >
              <Box
                sx={{
                  position: 'relative',
                  pb: index < phases.length - 1 ? 2.5 : 0,
                }}
              >
                {/* Dot */}
                <Box
                  sx={{
                    position: 'absolute',
                    left: -27,
                    top: 6,
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: index === 0 ? COLORS.primary : COLORS.background.hover,
                    border: `2px solid ${index === 0 ? COLORS.primary : COLORS.text.muted}`,
                  }}
                />

                <Typography
                  sx={{
                    fontSize: '0.95rem',
                    fontWeight: 600,
                    color: COLORS.text.primary,
                    lineHeight: 1.3,
                  }}
                >
                  {phase.name}
                </Typography>
                {phase.date && (
                  <Typography
                    sx={{
                      fontSize: '0.8rem',
                      color: COLORS.text.secondary,
                      mt: 0.25,
                    }}
                  >
                    {phase.date}
                  </Typography>
                )}
              </Box>
            </motion.div>
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}

// Table Widget - Shows structured data in rows and columns

function WidgetTable({ props }) {
  const [copied, setCopied] = useState(false);
  const headers = [];
  const rowsRaw = [];

  for (const key of Object.keys(props)) {
    const baseKey = key.replace(/\d+$/, '');
    const value = props[key];
    if (baseKey === 'h') headers.push(...value.split(';').map(h => h.trim()));
    else if (baseKey === 'r') rowsRaw.push(value.split(';').map(v => v.trim()));
  }

  const columns = useMemo(() => headers.map((h, i) => ({
    field: `col${i}`,
    headerName: h,
    flex: 1,
    minWidth: 120,
    sortable: true,
  })), [headers.join(';')]);

  const rows = useMemo(() => rowsRaw.map((row, rowIndex) => {
    const obj = { id: rowIndex };
    row.forEach((cell, i) => { obj[`col${i}`] = cell; });
    return obj;
  }), [rowsRaw.length, headers.length]);

  const toTSV = useCallback(() => {
    const headerLine = headers.join('\t');
    const dataLines = rowsRaw.map(r => r.join('\t'));
    return [headerLine, ...dataLines].join('\n');
  }, [headers, rowsRaw]);

  const handleCopy = useCallback(() => {
    const text = toTSV();
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [toTSV]);

  const handleDownloadCSV = useCallback(() => {
    const headerLine = headers.join(',');
    const dataLines = rowsRaw.map(r => r.map(cell => cell.includes(',') ? `"${cell}"` : cell).join(','));
    const csv = [headerLine, ...dataLines].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${props.t || 'table'}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [headers, rowsRaw, props.t]);

  if (columns.length === 0 && rows.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          minWidth: 280,
          width: '100%',
        }}
      >
        <Box sx={{ px: 2.5, pt: 2, pb: 1.5, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {props.t ? (
            <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary, fontFamily: TYPOGRAPHY.fontFamily }}>
              {props.t}
            </Typography>
          ) : <Box />}
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Box
              component="button"
              onClick={handleCopy}
              sx={{
                display: 'flex', alignItems: 'center', gap: 0.5, px: 1, py: 0.5,
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                backgroundColor: copied ? 'rgba(76,130,92,0.1)' : 'transparent',
                color: copied ? COLORS.success : COLORS.text.muted,
                fontSize: '0.72rem', fontFamily: TYPOGRAPHY.fontFamily,
                transition: 'all 0.2s',
                '&:hover': { backgroundColor: 'rgba(0,0,0,0.05)', color: COLORS.text.primary },
              }}
            >
              {copied ? <Check size={13} /> : <Copy size={13} />}
              {copied ? 'Copied' : 'Copy'}
            </Box>
            <Box
              component="button"
              onClick={handleDownloadCSV}
              sx={{
                display: 'flex', alignItems: 'center', gap: 0.5, px: 1, py: 0.5,
                border: 'none', borderRadius: '6px', cursor: 'pointer',
                backgroundColor: 'transparent',
                color: COLORS.text.muted,
                fontSize: '0.72rem', fontFamily: TYPOGRAPHY.fontFamily,
                transition: 'all 0.2s',
                '&:hover': { backgroundColor: 'rgba(0,0,0,0.05)', color: COLORS.text.primary },
              }}
            >
              <Download size={13} />
              CSV
            </Box>
          </Box>
        </Box>

        <Box sx={{ width: '100%' }}>
          <DataGrid
            rows={rows}
            columns={columns}
            disableRowSelectionOnClick
            hideFooter={rows.length <= 100}
            density="compact"
            autoHeight
            disableColumnMenu={false}
            sx={{
              border: 'none',
              borderRadius: '4px',
              fontFamily: TYPOGRAPHY.fontFamily,
              fontSize: '0.85rem',
              '& .MuiDataGrid-columnHeaders': {
                backgroundColor: 'rgba(0,0,0,0.03)',
                borderBottom: `1px solid ${COLORS.background.hover}`,
              },
              '& .MuiDataGrid-columnHeaderTitle': {
                fontWeight: 600,
                fontSize: '0.8rem',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                color: COLORS.text.secondary,
              },
              '& .MuiDataGrid-cell': {
                color: COLORS.text.primary,
                borderBottom: `1px solid ${COLORS.background.hover}`,
              },
              '& .MuiDataGrid-row:hover': {
                backgroundColor: 'rgba(0,0,0,0.03)',
              },
              '& .MuiDataGrid-row:last-of-type .MuiDataGrid-cell': {
                borderBottom: 'none',
              },
              '& .MuiDataGrid-columnSeparator': {
                color: 'rgba(0,0,0,0.1)',
              },
            }}
          />
        </Box>
      </Box>
    </motion.div>
  );
}

// Checklist Widget - Shows tasks with status (done/todo/blocked)
function WidgetChecklist({ props }) {
  const items = [];

  for (const key of Object.keys(props)) {
    const baseKey = key.replace(/\d+$/, '');
    const value = props[key];

    if (baseKey === 'done' || baseKey === 'todo' || baseKey === 'blocked') {
      items.push({ status: baseKey, text: value });
    }
  }

  if (items.length === 0) return null;

  const statusStyles = {
    done: { color: COLORS.success, icon: Check, bgColor: 'rgba(76, 130, 92, 0.12)' },  // Pine 100
    todo: { color: COLORS.text.muted, icon: null, bgColor: 'transparent' },
    blocked: { color: COLORS.error, icon: X, bgColor: 'rgba(199, 70, 52, 0.1)' },  // Oracle Red
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 3,
          p: 2.5,
          minWidth: 280,
        }}
      >
        {props.t && (
          <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary, mb: 2 }}>
            {props.t}
          </Typography>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {items.map((item, index) => {
            const style = statusStyles[item.status];
            const IconComponent = style.icon;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05, duration: 0.25 }}
              >
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    py: 0.75,
                  }}
                >
                  <Box
                    sx={{
                      width: 20,
                      height: 20,
                      borderRadius: 1,
                      border: `2px solid ${style.color}`,
                      backgroundColor: style.bgColor,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                    }}
                  >
                    {IconComponent && <IconComponent size={12} color={style.color} />}
                  </Box>
                  <Typography
                    sx={{
                      fontSize: '0.9rem',
                      color: item.status === 'done' ? COLORS.text.secondary : COLORS.text.primary,
                      textDecoration: 'none',
                    }}
                  >
                    {item.text}
                  </Typography>
                </Box>
              </motion.div>
            );
          })}
        </Box>
      </Box>
    </motion.div>
  );
}

// Section Widget - Collapsible content section
function WidgetSection({ props }) {
  const [expanded, setExpanded] = useState(true);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 3,
          overflow: 'hidden',
          minWidth: 280,
        }}
      >
        {/* Header - clickable to toggle */}
        <Box
          onClick={() => setExpanded(!expanded)}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            p: 2,
            cursor: 'pointer',
            '&:hover': { backgroundColor: 'rgba(0,0,0,0.02)' },
          }}
        >
          <motion.div
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ArrowRight size={18} color={COLORS.text.secondary} />
          </motion.div>
          <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: COLORS.text.primary, fontFamily: TYPOGRAPHY.fontFamily }}>
            {props.t || 'Section'}
          </Typography>
        </Box>

        {/* Content */}
        <motion.div
          initial={false}
          animate={{
            height: expanded ? 'auto' : 0,
            opacity: expanded ? 1 : 0,
          }}
          transition={{ duration: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
          style={{ overflow: 'hidden' }}
        >
          <Box sx={{ px: 2, pb: 2, pl: 4.5 }}>
            {props.d && (
              <Typography sx={{ fontSize: '0.9rem', color: COLORS.text.secondary, lineHeight: 1.6, fontFamily: TYPOGRAPHY.fontFamily }}>
                {props.d}
              </Typography>
            )}
            {props.ls && <WidgetList items={props.ls} />}
          </Box>
        </motion.div>
      </Box>
    </motion.div>
  );
}

// Risk Widget - Risk card with severity level (using theme colors)
function WidgetRisk({ props, level }) {
  const severityConfig = {
    high: { color: COLORS.error, textColor: 'white', bgColor: '#d4594a', label: 'High Risk' },  // Oracle Red lighter
    medium: { color: '#b87a2e', textColor: 'white', bgColor: COLORS.warning, label: 'Medium Risk' },  // Brand Yellow
    low: { color: COLORS.success, textColor: 'white', bgColor: '#6a9b74', label: 'Low Risk' },  // Pine 100 lighter
  };

  const severity = severityConfig[level] || severityConfig.medium;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: severity.bgColor,
          borderRadius: 2,
          overflow: 'hidden',
          minWidth: 280,
        }}
      >
        <Box sx={{ p: 2.5 }}>
          {/* Severity badge */}
          <Box
            sx={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 0.75,
              px: 1.5,
              py: 0.5,
              borderRadius: 2,
              backgroundColor: 'rgba(255,255,255,0.25)',
              mb: 1.5,
            }}
          >
            <AlertCircle size={14} color={severity.textColor} />
            <Typography
              sx={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: severity.textColor,
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              {severity.label}
            </Typography>
          </Box>

          {props.t && (
            <Typography sx={{ fontSize: '1rem', fontWeight: 600, color: severity.textColor, mb: 0.5 }}>
              {props.t}
            </Typography>
          )}

          {props.d && (
            <Typography sx={{ fontSize: '0.85rem', color: 'rgba(255,255,255,0.9)', lineHeight: 1.5 }}>
              {props.d}
            </Typography>
          )}
        </Box>
      </Box>
    </motion.div>
  );
}

// Poll Widget - Choice selector with options + custom input
function WidgetPoll({ props, onSubmit, disabled, selectedData }) {
  const [selected, setSelected] = useState(null);
  const [customText, setCustomText] = useState('');
  const [isSubmitted, setIsSubmitted] = useState(false);

  useEffect(() => {
    if (disabled && selectedData) {
      setIsSubmitted(true);
      if (selectedData._action === 'custom') {
        setCustomText(selectedData.custom || '');
      } else {
        setSelected(selectedData._action);
      }
    }
  }, [disabled, selectedData]);

  const question = props.poll || props.t || 'Make a selection';
  const description = props.d;
  const widgetId = props._id || null;

  const options = Object.keys(props)
    .filter(k => k.match(/^op\d*$/))
    .map(k => props[k]);

  const handleOptionClick = (optionText) => {
    if (isSubmitted || disabled) return;
    setSelected(optionText);
    setIsSubmitted(true);
    if (onSubmit) onSubmit({ _action: optionText }, widgetId);
  };

  const handleCustomSubmit = () => {
    if (isSubmitted || disabled || !customText.trim()) return;
    setIsSubmitted(true);
    if (onSubmit) onSubmit({ custom: customText.trim(), _action: 'custom' }, widgetId);
  };

  const isDisabled = isSubmitted || disabled;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box sx={{
        backgroundColor: COLORS.background.widget,
        borderRadius: 3,
        p: 3,
        minWidth: 280,
        maxWidth: 420,
      }}>
        {/* Question */}
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.3 }}
        >
          <Typography sx={{
            fontSize: '1.1rem',
            fontWeight: 600,
            color: COLORS.text.primary,
            mb: description ? 0.5 : 2,
            fontFamily: TYPOGRAPHY.fontFamily,
          }}>
            {question}
          </Typography>
        </motion.div>

        {description && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15, duration: 0.3 }}
          >
            <Typography sx={{
              fontSize: '0.9rem',
              color: COLORS.text.secondary,
              mb: 2,
              lineHeight: 1.5,
              fontFamily: TYPOGRAPHY.fontFamily,
            }}>
              {description}
            </Typography>
          </motion.div>
        )}

        {/* Option cards */}
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          {options.map((option, index) => {
            const isThisSelected = selected === option;
            const isOtherSelected = selected !== null && !isThisSelected;

            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -15 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 + index * 0.05, duration: 0.3 }}
              >
                <Box
                  onClick={() => handleOptionClick(option)}
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 1.5,
                    px: 2,
                    py: 1.5,
                    borderRadius: 2,
                    border: `1.5px solid ${isThisSelected ? COLORS.primary : 'var(--dm-border, rgba(49, 45, 42, 0.12))'}`,
                    backgroundColor: isThisSelected ? 'rgba(199, 70, 52, 0.06)' : 'var(--dm-subtle, rgba(49, 45, 42, 0.02))',
                    cursor: isDisabled ? 'default' : 'pointer',
                    opacity: isOtherSelected ? 0.5 : 1,
                    transition: 'all 0.2s ease',
                    ...(!isDisabled && {
                      '&:hover': {
                        borderColor: COLORS.primary,
                        backgroundColor: 'rgba(199, 70, 52, 0.04)',
                        transform: 'translateX(4px)',
                      },
                    }),
                  }}
                >
                  {/* Number badge */}
                  <Box sx={{
                    width: 28,
                    height: 28,
                    borderRadius: '50%',
                    backgroundColor: isThisSelected ? COLORS.primary : 'var(--dm-subtle, rgba(49, 45, 42, 0.08))',
                    color: isThisSelected ? '#fff' : COLORS.text.secondary,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    flexShrink: 0,
                    transition: 'all 0.2s ease',
                  }}>
                    {isThisSelected ? <Check size={14} /> : index + 1}
                  </Box>

                  <Typography sx={{
                    fontSize: '0.95rem',
                    color: COLORS.text.primary,
                    fontWeight: isThisSelected ? 600 : 400,
                    fontFamily: TYPOGRAPHY.fontFamily,
                  }}>
                    {option}
                  </Typography>
                </Box>
              </motion.div>
            );
          })}
        </Box>

        {/* Custom input area */}
        <Box sx={{ borderTop: '1px solid var(--dm-border, rgba(49, 45, 42, 0.08))', mt: 2, pt: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <TextField
              size="small"
              placeholder="Or type your own answer..."
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !isDisabled && customText.trim()) {
                  e.preventDefault();
                  handleCustomSubmit();
                }
              }}
              disabled={isDisabled}
              fullWidth
              sx={{
                '& .MuiOutlinedInput-root': {
                  backgroundColor: INPUT.backgroundColor,
                  '& fieldset': { border: INPUT.border },
                  '&:hover': { backgroundColor: isDisabled ? INPUT.backgroundColor : INPUT.hoverBackground },
                  '&.Mui-focused': { backgroundColor: INPUT.hoverBackground },
                },
              }}
            />
            <button
              onClick={handleCustomSubmit}
              disabled={isDisabled || !customText.trim()}
              style={{
                padding: '8px 16px',
                backgroundColor: COLORS.primary,
                color: '#fff',
                border: 'none',
                borderRadius: BUTTON.borderRadius,
                fontSize: '0.85rem',
                fontWeight: 500,
                cursor: (isDisabled || !customText.trim()) ? 'default' : 'pointer',
                opacity: (isDisabled || !customText.trim()) ? 0.5 : 1,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                flexShrink: 0,
                transition: 'all 0.2s ease',
              }}
            >
              <Send size={14} />
            </button>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}

// Mail Widget - Email preview card
// PPT Widget - Embeds PowerPoint presentation from URL
function WidgetPPT({ props }) {
  const [isLoading, setIsLoading] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const pptUrl = props.ppt;
  const encodedUrl = encodeURIComponent(pptUrl);
  const viewerUrl = `https://view.officeapps.live.com/op/embed.aspx?src=${encodedUrl}`;

  // Extract filename from URL for display
  const filename = pptUrl.split('/').pop()?.split('?')[0]?.replace(/_/g, ' ')?.replace('.pptx', '') || 'Presentation';

  const handleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const handleOpenExternal = () => {
    window.open(viewerUrl, '_blank');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          width: isFullscreen ? '100vw' : 800,
          maxWidth: isFullscreen ? '100vw' : '100%',
          position: isFullscreen ? 'fixed' : 'relative',
          top: isFullscreen ? 0 : 'auto',
          left: isFullscreen ? 0 : 'auto',
          zIndex: isFullscreen ? 9999 : 1,
          height: isFullscreen ? '100vh' : 'auto',
          backgroundColor: isFullscreen ? '#000' : 'transparent',
        }}
      >
        {/* Header */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.4 }}
        >
          <Box
            sx={{
              background: 'linear-gradient(135deg, #D35230 0%, #B7472A 100%)',
              borderRadius: isFullscreen ? 0 : '12px 12px 0 0',
              px: 2.5,
              py: 2,
              display: 'flex',
              alignItems: 'center',
              gap: 2,
            }}
          >
            <Box
              sx={{
                width: 44,
                height: 44,
                borderRadius: '10px',
                backgroundColor: 'rgba(255,255,255,0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Presentation size={24} color="white" />
            </Box>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography
                sx={{
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '1rem',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {props.t || filename}
              </Typography>
              <Typography
                sx={{
                  color: 'rgba(255,255,255,0.7)',
                  fontSize: '0.75rem',
                  mt: 0.25,
                }}
              >
                PowerPoint Presentation
              </Typography>
            </Box>

            {/* Action buttons */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleOpenExternal}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '8px',
                  backgroundColor: 'rgba(255,255,255,0.15)',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.25)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.15)'}
              >
                <ExternalLink size={18} color="white" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleFullscreen}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: '8px',
                  backgroundColor: 'rgba(255,255,255,0.15)',
                  border: 'none',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  transition: 'background-color 0.2s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.25)'}
                onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'rgba(255,255,255,0.15)'}
              >
                <Maximize2 size={18} color="white" />
              </motion.button>
              {isFullscreen && (
                <motion.button
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleFullscreen}
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: '8px',
                    backgroundColor: 'rgba(255,255,255,0.25)',
                    border: 'none',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <X size={18} color="white" />
                </motion.button>
              )}
            </Box>
          </Box>
        </motion.div>

        {/* Slide viewer */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          <Box
            sx={{
              backgroundColor: '#1a1a1a',
              borderRadius: isFullscreen ? 0 : '0 0 12px 12px',
              overflow: 'hidden',
              boxShadow: isFullscreen ? 'none' : '0 8px 32px rgba(0,0,0,0.12)',
              position: 'relative',
            }}
          >
            {/* Loading overlay */}
            {isLoading && (
              <Box
                sx={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  right: 0,
                  bottom: 0,
                  backgroundColor: '#1a1a1a',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 2,
                  zIndex: 10,
                }}
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                >
                  <Box
                    sx={{
                      width: 48,
                      height: 48,
                      borderRadius: '50%',
                      border: '3px solid rgba(211,82,48,0.2)',
                      borderTopColor: '#D35230',
                    }}
                  />
                </motion.div>
                <Typography sx={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.875rem' }}>
                  Loading presentation...
                </Typography>
              </Box>
            )}

            <Box
              sx={{
                width: '100%',
                aspectRatio: isFullscreen ? 'auto' : '4/3',
                height: isFullscreen ? 'calc(100vh - 76px)' : 'auto',
              }}
            >
              <iframe
                src={viewerUrl}
                onLoad={() => setIsLoading(false)}
                style={{
                  width: '100%',
                  height: '100%',
                  border: 'none',
                }}
                allowFullScreen
              />
            </Box>
          </Box>
        </motion.div>
      </Box>

      {/* Fullscreen backdrop */}
      {isFullscreen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          onClick={handleFullscreen}
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.8)',
            zIndex: 9998,
          }}
        />
      )}
    </motion.div>
  );
}

function WidgetMail({ props }) {
  const parseBody = (raw) => (raw || '')
    .replace(/&#10;/g, '\n').replace(/&#13;/g, '\r')
    .replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/<br\s*\/?>/gi, '\n').replace(/<[^>]+>/g, '');

  // Only store what the user has explicitly edited — props are the source of truth
  const [userEdits, setUserEdits] = useState({});
  const [copied, setCopied] = useState(null);

  const fields = {
    to: userEdits.to ?? (props.to || ''),
    from: userEdits.from ?? (props.from || ''),
    cc: userEdits.cc ?? (props.cc || ''),
    subj: userEdits.subj ?? (props.subj || ''),
    body: userEdits.body ?? parseBody(props.body),
  };

  const update = (key, val) => setUserEdits(e => ({ ...e, [key]: val }));

  const copyField = (key) => {
    const text = fields[key];
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(key);
    setTimeout(() => setCopied(null), 2000);
  };

  const CopyAdornment = ({ fieldKey }) => (
    <InputAdornment position="end">
      <Box
        onClick={() => copyField(fieldKey)}
        sx={{
          cursor: 'pointer',
          color: copied === fieldKey ? COLORS.success : 'rgba(0,0,0,0.3)',
          display: 'flex', alignItems: 'center',
          p: 0.5,
          borderRadius: 1,
          '&:hover': { color: copied === fieldKey ? COLORS.success : COLORS.text.primary, backgroundColor: 'rgba(0,0,0,0.05)' },
          transition: 'color 0.2s',
        }}
      >
        {copied === fieldKey ? <Check size={13} /> : <Copy size={13} />}
      </Box>
    </InputAdornment>
  );

  const MailField = ({ label, fieldKey }) => (
    props[fieldKey] !== undefined ? (
      <Box>
        <Typography sx={{ fontSize: '0.72rem', fontWeight: 500, color: COLORS.text.secondary, textTransform: 'uppercase', letterSpacing: '0.4px', mb: 0.5 }}>
          {label}
        </Typography>
        <TextField
          value={fields[fieldKey]}
          onChange={e => update(fieldKey, e.target.value)}
          size="small"
          fullWidth
          InputProps={{ endAdornment: <CopyAdornment fieldKey={fieldKey} /> }}
          sx={{ '& .MuiOutlinedInput-root': { fontSize: '0.85rem', fontFamily: 'inherit', backgroundColor: 'rgba(0,0,0,0.02)' } }}
        />
      </Box>
    ) : null
  );

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 2,
          overflow: 'hidden',
          minWidth: 340,
          border: '1px solid rgba(0,0,0,0.08)',
        }}
      >
        {/* Header */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 1.5,
            px: 2.5,
            py: 1.75,
            borderBottom: '1px solid rgba(0,0,0,0.06)',
            backgroundColor: 'rgba(0,0,0,0.02)',
          }}
        >
          <Box sx={{ width: 34, height: 34, borderRadius: '50%', backgroundColor: '#1976d2', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
            <Mail size={16} color="white" />
          </Box>
          <Typography sx={{ fontSize: '0.8rem', fontWeight: 600, color: COLORS.text.primary, letterSpacing: '0.2px' }}>
            Email Draft
          </Typography>
        </Box>

        {/* Editable fields */}
        <Box sx={{ p: 2.5, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
          <MailField label="Subject" fieldKey="subj" />
          <MailField label="To" fieldKey="to" />
          <MailField label="From" fieldKey="from" />
          <MailField label="Cc" fieldKey="cc" />

          {/* Body */}
          {props.body !== undefined && (
            <Box sx={{ pt: 1, borderTop: '1px solid rgba(0,0,0,0.06)' }}>
              <Typography sx={{ fontSize: '0.72rem', fontWeight: 500, color: COLORS.text.secondary, textTransform: 'uppercase', letterSpacing: '0.4px', mb: 0.5 }}>
                Body
              </Typography>
              <TextField
                value={fields.body}
                onChange={e => update('body', e.target.value)}
                multiline
                minRows={4}
                maxRows={14}
                fullWidth
                size="small"
                InputProps={{ endAdornment: <InputAdornment position="end" sx={{ alignSelf: 'flex-start', mt: 0.5 }}><Box onClick={() => copyField('body')} sx={{ cursor: 'pointer', color: copied === 'body' ? COLORS.success : 'rgba(0,0,0,0.3)', display: 'flex', alignItems: 'center', p: 0.5, borderRadius: 1, '&:hover': { color: copied === 'body' ? COLORS.success : COLORS.text.primary, backgroundColor: 'rgba(0,0,0,0.05)' }, transition: 'color 0.2s' }}>{copied === 'body' ? <Check size={13} /> : <Copy size={13} />}</Box></InputAdornment> }}
                sx={{ '& .MuiOutlinedInput-root': { fontSize: '0.875rem', fontFamily: 'inherit', lineHeight: 1.6, backgroundColor: 'rgba(0,0,0,0.02)', alignItems: 'flex-start' } }}
              />
            </Box>
          )}
        </Box>
      </Box>
    </motion.div>
  );
}

// KPI Card - Single metric display
function WidgetKPICard({ value, label, color }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{ flex: 1, minWidth: 100 }}
    >
      <Box
        sx={{
          backgroundColor: COLORS.background.widget,
          borderRadius: 2,
          p: 2,
          textAlign: 'center',
        }}
      >
        <Typography
          sx={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: color || COLORS.primary,
            lineHeight: 1.2,
          }}
        >
          {value}
        </Typography>
        <Typography
          sx={{
            fontSize: '0.75rem',
            color: COLORS.text.secondary,
            mt: 0.5,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {label}
        </Typography>
      </Box>
    </motion.div>
  );
}

// Grid Widget - KPI cards in grid layout
function WidgetGrid({ props, columns = 3 }) {
  const kpis = [];

  for (const key of Object.keys(props)) {
    const baseKey = key.replace(/\d+$/, '');
    const value = props[key];

    if (baseKey === 'kpi') {
      // Format: Value;Label or Value;Label;Color
      const parts = value.split(';');
      kpis.push({
        value: parts[0]?.trim() || '',
        label: parts[1]?.trim() || '',
        color: getColor(parts[2]?.trim()) || COLORS.primary,
      });
    }
  }

  if (kpis.length === 0) return null;

  const cols = parseInt(props.grid) || parseInt(props.cols) || columns;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    >
      <Box sx={{ minWidth: 280 }}>
        {props.t && (
          <Typography sx={{ fontSize: '1.1rem', fontWeight: 600, color: COLORS.text.primary, mb: 2 }}>
            {props.t}
          </Typography>
        )}

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: `repeat(${cols}, 1fr)`,
            gap: 1.5,
          }}
        >
          {kpis.map((kpi, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05, duration: 0.25 }}
            >
              <WidgetKPICard
                value={kpi.value}
                label={kpi.label}
                color={kpi.color}
              />
            </motion.div>
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}

function WidgetButton({ label, color, onClick, isSubmit, isLoading, isClicked, disabled }) {
  const bgColor = isSubmit ? color : COLORS.secondary;

  return (
    <button
      onClick={disabled ? undefined : onClick}
      disabled={disabled}
      style={{
        padding: BUTTON.padding,
        backgroundColor: bgColor,
        color: COLORS.text.inverse,
        border: "none",
        borderRadius: BUTTON.borderRadius,
        fontSize: BUTTON.fontSize,
        fontWeight: BUTTON.fontWeight,
        cursor: disabled ? "default" : "pointer",
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: 8,
        opacity: disabled ? BUTTON.disabledOpacity : 1
      }}
    >
      {isLoading ? (
        <CircularProgress size={16} sx={{ color: COLORS.text.inverse }} />
      ) : (
        <>
          {isClicked && "✓ "}
          {label}
          {isSubmit && !isClicked && <Send size={14} />}
        </>
      )}
    </button>
  );
}

export default function Widget({ props = {}, streamingKey = null, streamingValue = "", onSubmit, selectedData = null, disabled = false, embedded = false }) {
  const [formState, setFormState] = useState({});
  const [clickedButton, setClickedButton] = useState(null);
  const [loadingButton, setLoadingButton] = useState(null);

  // Pre-populate form state with selectedData when loading a used widget
  useEffect(() => {
    if (disabled && selectedData) {
      setFormState(selectedData);
      // Find the action button that was clicked
      if (selectedData._action) {
        setClickedButton(selectedData._action);
      }
    }
  }, [disabled, selectedData]);

  const themeColor = getColor(props._c) || COLORS.primary;
  const size = getSize(props._sz);
  const radius = props._rd !== undefined ? parseInt(props._rd) * 4 : BORDER.radius;
  const direction = props._dir === "h" ? "row" : "column";
  const align = { l: "flex-start", c: "center", r: "flex-end" }[props._al] || "flex-start";
  const gap = props._g !== undefined ? parseInt(props._g) : SPACING.gap;
  const widgetId = props._id || null;

  // Dark theme and centered layout
  const isDark = props._dark !== undefined;
  const isCentered = props._center !== undefined;

  // Background color handling
  const getBgColor = () => {
    if (props._bg) {
      if (props._bg.startsWith("http")) return null;
      return getColor(props._bg);
    }
    if (isDark) return COLORS.slate[150]; // Dark slate background
    return null;
  };
  const bgColor = getBgColor();

  // Text colors for dark theme
  const textColors = isDark ? {
    primary: COLORS.text.inverse,
    secondary: "rgba(255,255,255,0.7)",
    muted: "rgba(255,255,255,0.5)",
  } : {
    primary: COLORS.text.primary,
    secondary: COLORS.text.secondary,
    muted: COLORS.text.muted,
  };

  const hasBackgroundImage = Object.keys(props).some(k => k.includes("@bg") && props[k]);
  const backgroundImageKey = Object.keys(props).find(k => k.includes("@bg"));
  const backgroundImage = backgroundImageKey ? props[backgroundImageKey] : null;

  // Check if widget has interactive elements
  const interactiveKeys = Object.keys(props).filter(k => {
    const base = k.split("@")[0];
    return INTERACTIVE_KEYS[base];
  });
  const hasInteractive = interactiveKeys.length > 0;

  // Check if widget is a chart
  const chartType = Object.keys(props).find(k => CHART_KEYS[k]);

  const updateFormState = useCallback((key, value) => {
    setFormState(prev => ({ ...prev, [key]: value }));
  }, []);

  const handleButtonClick = useCallback((label, isOnlyButton) => {
    if (clickedButton || loadingButton) return;

    setLoadingButton(label);

    // Brief loading state, then show clicked
    setTimeout(() => {
      setLoadingButton(null);
      setClickedButton(label);

      if (onSubmit) {
        let dataToSubmit;
        if (isOnlyButton && interactiveKeys.length === 0) {
          dataToSubmit = { _action: label };
        } else {
          dataToSubmit = { ...formState, _action: label };
        }
        onSubmit(dataToSubmit, widgetId);
      }
    }, ANIMATION.loadingDelay);
  }, [formState, onSubmit, widgetId, clickedButton, loadingButton, interactiveKeys.length]);

  const getPositionedContent = (position) => {
    return Object.entries(props).filter(([key]) => {
      const parsed = parseKey(key);
      return parsed.position === position;
    });
  };

  const topContent = getPositionedContent("t");
  const bottomContent = getPositionedContent("b");
  const overlayContent = getPositionedContent("ov");

  const renderContent = (key, value, isStreaming = false) => {
    const parsed = parseKey(key);
    const displayValue = isStreaming ? streamingValue : value;

    if (parsed.isStyle) return null;

    // Count buttons to determine if single button
    const buttonCount = Object.keys(props).filter(k => k.startsWith("bt")).length;
    const isOnlyButton = buttonCount === 1 && interactiveKeys.filter(k => !k.startsWith("bt")).length === 0;

    switch (parsed.base) {
      case "t":
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: isCentered ? 0 : -20, y: isCentered ? -10 : 0 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            transition={{ duration: 0.4, delay: 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Typography sx={{ fontSize: size.title, fontWeight: 600, color: (hasBackgroundImage || isDark) ? textColors.primary : "inherit", lineHeight: 1.3, textAlign: isCentered ? "center" : "left", fontFamily: TYPOGRAPHY.fontFamily, wordBreak: "break-word" }}>
              {displayValue}{isStreaming && <span style={{ opacity: 0.5 }}>|</span>}
            </Typography>
          </motion.div>
        );

      case "s":
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: isCentered ? 0 : -15, y: isCentered ? -5 : 0 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            transition={{ duration: 0.4, delay: 0.15, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Typography sx={{ fontSize: size.text, fontWeight: 500, color: (hasBackgroundImage || isDark) ? textColors.secondary : themeColor, lineHeight: 1.3, textAlign: isCentered ? "center" : "left" }}>
              {displayValue}{isStreaming && <span style={{ opacity: 0.5 }}>|</span>}
            </Typography>
          </motion.div>
        );

      case "d":
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: isCentered ? 0 : -15, y: isCentered ? -5 : 0 }}
            animate={{ opacity: 1, x: 0, y: 0 }}
            transition={{ duration: 0.4, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Typography sx={{ fontSize: size.text, color: (hasBackgroundImage || isDark) ? textColors.secondary : "rgba(0,0,0,0.7)", lineHeight: 1.5, textAlign: isCentered ? "center" : "left" }}>
              {displayValue}{isStreaming && <span style={{ opacity: 0.5 }}>|</span>}
            </Typography>
          </motion.div>
        );

      case "ic":
        return <WidgetIcon key={key} name={displayValue} size={size.icon} color={isDark ? textColors.primary : themeColor} />;

      case "i":
        return <WidgetImage key={key} src={displayValue} position={parsed.position} />;

      case "n":
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: isCentered ? 0 : -20, scale: isCentered ? 0.9 : 1 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.1, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Typography sx={{ fontSize: "clamp(1.2rem, 4vw, 2rem)", fontWeight: 700, color: isDark ? textColors.primary : themeColor, textAlign: isCentered ? "center" : "left", lineHeight: 1.2, wordBreak: "break-word" }}>{displayValue}</Typography>
          </motion.div>
        );

      case "p":
        return <WidgetProgress key={key} value={displayValue} color={themeColor} />;

      case "q":
        return <WidgetQuote key={key} text={displayValue} color={themeColor} />;

      case "cd":
        return <WidgetCode key={key} code={displayValue} />;

      case "ls":
        return <WidgetList key={key} items={displayValue} />;

      case "lk":
        return <WidgetLinks key={key} links={displayValue} color={themeColor} />;

      case "au":
        return <WidgetAudio key={key} src={displayValue} color={themeColor} />;

      // Interactive elements
      case "in":
        // Find submit button for Enter key
        const submitBtnKey = Object.keys(props).find(k => k.startsWith("bt"));
        const submitBtnLabel = submitBtnKey ? props[submitBtnKey] : null;
        const isFormDisabled = disabled || clickedButton !== null || loadingButton !== null;
        // Parse label and default value from displayValue (e.g., "Name=John" -> label: "Name", default: "John")
        const inLabel = displayValue.includes("=") ? displayValue.split("=")[0] : displayValue;
        const inDefault = displayValue.includes("=") ? displayValue.split("=").slice(1).join("=") : "";
        const inValue = formState[inLabel] !== undefined ? formState[inLabel] : inDefault;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetInput
                placeholder={inLabel}
                value={inValue}
                onChange={(v) => updateFormState(inLabel, v)}
                onEnter={submitBtnLabel ? () => handleButtonClick(submitBtnLabel, isOnlyButton) : undefined}
                disabled={isFormDisabled}
              />
            </Box>
          </motion.div>
        );

      case "ta":
        const isTextareaDisabled = disabled || clickedButton !== null || loadingButton !== null;
        // Parse label and default value from displayValue (e.g., "Notes=Draft text" -> label: "Notes", default: "Draft text")
        const taLabel = displayValue.includes("=") ? displayValue.split("=")[0] : displayValue;
        const taDefaultVal = displayValue.includes("=") ? displayValue.split("=").slice(1).join("=").replace(/\\n/g, '\n') : "";
        const taValue = formState[taLabel] !== undefined ? formState[taLabel] : taDefaultVal;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetTextarea
                placeholder={taLabel}
                value={taValue}
                onChange={(v) => updateFormState(taLabel, v)}
                disabled={isTextareaDisabled}
              />
            </Box>
          </motion.div>
        );

      case "bt":
        const isSubmitBtn = displayValue.toLowerCase().includes("submit") || displayValue.toLowerCase().includes("send") || displayValue.toLowerCase().includes("apply") || (!hasInteractive && buttonCount > 0);
        const isThisButtonClicked = clickedButton === displayValue;
        const isAnyButtonClicked = disabled || clickedButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.3, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Box sx={{ mt: 1 }}>
              <WidgetButton
                label={displayValue}
                color={themeColor}
                onClick={() => handleButtonClick(displayValue, isOnlyButton)}
                isSubmit={isSubmitBtn || isOnlyButton}
                isLoading={loadingButton === displayValue}
                isClicked={isThisButtonClicked}
                disabled={isAnyButtonClicked || loadingButton !== null}
              />
            </Box>
          </motion.div>
        );

      case "sl":
        const selectKey = `select_${key}`;
        const isSelectDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetSelect
                options={displayValue}
                value={formState[selectKey] || ""}
                onChange={(v) => updateFormState(selectKey, v)}
                disabled={isSelectDisabled}
              />
            </Box>
          </motion.div>
        );

      case "cb":
        const isCheckboxDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3, delay: 0.2, ease: [0.25, 0.46, 0.45, 0.94] }}
          >
            <Box sx={{ mt: 0.5 }}>
              <WidgetCheckbox
                label={displayValue}
                checked={formState[displayValue] === true || formState[displayValue] === "true" || formState[displayValue] === "1"}
                onChange={(v) => updateFormState(displayValue, v)}
                disabled={isCheckboxDisabled}
              />
            </Box>
          </motion.div>
        );

      case "rg":
        const rangeKey = `range_${key}`;
        const isRangeDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetRange
                range={displayValue}
                value={formState[rangeKey]}
                onChange={(v) => updateFormState(rangeKey, v)}
                disabled={isRangeDisabled}
              />
            </Box>
          </motion.div>
        );

      case "rd":
        const radioKey = `radio_${key}`;
        const isRadioDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetRadio
                options={displayValue}
                value={formState[radioKey]}
                onChange={(v) => updateFormState(radioKey, v)}
                disabled={isRadioDisabled}
              />
            </Box>
          </motion.div>
        );

      case "ms":
        const multiKey = `multi_${key}`;
        const isMultiDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetMultiSelect
                options={displayValue}
                value={formState[multiKey]}
                onChange={(v) => updateFormState(multiKey, v)}
                disabled={isMultiDisabled}
              />
            </Box>
          </motion.div>
        );

      case "dt":
        const dateKey = `date_${key}`;
        const isDateDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetDate
                label={displayValue !== "date" ? displayValue : null}
                value={formState[dateKey]}
                onChange={(v) => updateFormState(dateKey, v)}
                disabled={isDateDisabled}
              />
            </Box>
          </motion.div>
        );

      case "tm":
        const timeKey = `time_${key}`;
        const isTimeDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetTime
                label={displayValue !== "time" ? displayValue : null}
                value={formState[timeKey]}
                onChange={(v) => updateFormState(timeKey, v)}
                disabled={isTimeDisabled}
              />
            </Box>
          </motion.div>
        );

      case "rt":
        const ratingKey = `rating_${key}`;
        const isRatingDisabled = disabled || clickedButton !== null || loadingButton !== null;
        const [ratingLabel, ratingMax] = displayValue.includes("?") ? displayValue.split("?") : [null, displayValue];
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetRating
                label={ratingLabel}
                max={ratingMax}
                value={formState[ratingKey]}
                onChange={(v) => updateFormState(ratingKey, v)}
                disabled={isRatingDisabled}
              />
            </Box>
          </motion.div>
        );

      case "tg":
        const toggleKey = `toggle_${key}`;
        const isToggleDisabled = disabled || clickedButton !== null || loadingButton !== null;
        return (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.25, ease: [0.25, 0.46, 0.45, 0.94] }}
            style={{ width: "100%" }}
          >
            <Box sx={{ width: "100%", mt: 1 }}>
              <WidgetToggle
                label={displayValue}
                checked={formState[toggleKey] === true || formState[toggleKey] === "true" || formState[toggleKey] === "1"}
                onChange={(v) => updateFormState(toggleKey, v)}
                disabled={isToggleDisabled}
              />
            </Box>
          </motion.div>
        );

      default:
        return null;
    }
  };

  const contentKeys = Object.keys(props).filter(k => {
    const parsed = parseKey(k);
    return !parsed.isStyle && !parsed.position;
  });

  // Separate header elements (title + icon) from other content
  const headerKeys = contentKeys.filter(k => k === "t" || k === "ic");
  const bodyKeys = contentKeys.filter(k => k !== "t" && k !== "ic");
  const hasHeader = headerKeys.length > 0;

  const skeletonKeys = streamingKey && !props[streamingKey] ? [streamingKey] : [];

  // Render status card if detected
  if (props.st) {
    const statusType = props.st.toLowerCase();
    const buttons = Object.keys(props)
      .filter(k => k.startsWith("bt"))
      .map(k => props[k]);

    return (
      <WidgetStatusCard
        status={statusType}
        title={props.t}
        description={props.d}
        buttons={buttons}
        onButtonClick={(label) => handleButtonClick(label, buttons.length === 1)}
        clickedButton={clickedButton}
        loadingButton={loadingButton}
        disabled={disabled}
      />
    );
  }

  // Render row form layout if _rows is present
  if (props._rows !== undefined) {
    return (
      <WidgetRowForm
        props={props}
        formState={formState}
        updateFormState={updateFormState}
        handleButtonClick={handleButtonClick}
        clickedButton={clickedButton}
        loadingButton={loadingButton}
        disabled={disabled}
        themeColor={themeColor}
      />
    );
  }

  // Render calendar widget if detected (has cal: and dy: keys)
  if (props.cal !== undefined) {
    return <WidgetCalendar props={props} />;
  }

  /// Render PPT widget if detected (has ppt: key with URL)
  if (props.ppt !== undefined) {
    return <WidgetPPT props={props} />;
  }

  // Render mail widget if detected (has mail: or subj: with to: keys)
  if (props.mail !== undefined || (props.subj !== undefined && (props.to !== undefined || props.from !== undefined))) {
    return <WidgetMail props={props} />;
  }

  // Render timeline widget if detected (has tl: and ph: keys)
  if (props.tl !== undefined || Object.keys(props).some(k => k.startsWith('ph'))) {
    return <WidgetTimeline props={props} />;
  }

  // Render table widget if detected (has tb: and h:/r: keys)
  if (props.tb !== undefined || (Object.keys(props).some(k => k.startsWith('h')) && Object.keys(props).some(k => k.startsWith('r')))) {
    return <WidgetTable props={props} />;
  }

  // Render checklist widget if detected (has ck: or done:/todo:/blocked: keys)
  if (props.ck !== undefined || Object.keys(props).some(k => k.match(/^(done|todo|blocked)\d*$/))) {
    return <WidgetChecklist props={props} />;
  }

  // Render poll widget if detected (has poll: key or op: options)
  if (props.poll !== undefined || Object.keys(props).some(k => k.match(/^op\d*$/))) {
    return <WidgetPoll props={props} onSubmit={onSubmit} disabled={disabled} selectedData={selectedData} />;
  }

  // Render section widget if detected (has sec: key)
  if (props.sec !== undefined) {
    return <WidgetSection props={props} />;
  }

  // Render risk widget if detected (has risk: key)
  if (props.risk !== undefined) {
    return <WidgetRisk props={props} level={props.risk} />;
  }

  // Render grid/KPI widget if detected (has grid: or cols: with kpi: items)
  if ((props.grid !== undefined || props.cols !== undefined) && Object.keys(props).some(k => k.match(/^kpi\d*$/))) {
    return <WidgetGrid props={props} />;
  }

  // Render chart widget if detected
  if (chartType) {
    const chartTitle = props[chartType];
    const ChartComponent = {
      ch_ln: WidgetLineChart,
      ch_br: WidgetBarChart,
      ch_pie: WidgetPieChart,
      ch_don: WidgetDonutChart,
    }[chartType];

    return (
      <Box
        sx={{
          display: embedded ? "block" : "inline-block",
          maxWidth: props._w || "100%",
          width: embedded ? "100%" : (props._w || "auto"),
          minWidth: embedded ? 0 : (props._mw || 280),
          position: "relative",
        }}
      >
        <motion.div
          initial={{ scaleY: 0, opacity: 0.5 }}
          animate={{ scaleY: 1, opacity: 1 }}
          transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
          style={{
            position: "absolute",
            inset: 0,
            backgroundColor: bgColor || COLORS.background.widget,
            borderRadius: `${radius}px`,
            transformOrigin: "top",
            zIndex: 0,
          }}
        />
        <Box
          sx={{
            position: "relative",
            p: size.container,
            borderRadius: `${radius}px`,
            fontFamily: TYPOGRAPHY.fontFamily,
            zIndex: 1,
          }}
        >
          {chartTitle && (
            <Typography sx={{ fontSize: size.title, fontWeight: 600, mb: 1.5 }}>
              {chartTitle}
            </Typography>
          )}
          <ChartComponent props={props} />
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: embedded ? "block" : "inline-block",
        maxWidth: props._w || "100%",
        width: embedded ? "100%" : (props._w || "auto"),
        minWidth: embedded ? 0 : (props._mw || 280),
        position: "relative",
      }}
    >
      {/* Animated background */}
      <motion.div
        initial={{ scaleY: 0, opacity: 0.5 }}
        animate={{ scaleY: 1, opacity: 1 }}
        transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: bgColor || (hasBackgroundImage ? "transparent" : COLORS.background.widget),
          borderRadius: `${radius}px`,
          transformOrigin: "top",
          zIndex: 0,
        }}
      />
      <Box
        sx={{
          position: "relative",
          display: "flex",
          flexDirection: direction,
          alignItems: isCentered ? "center" : align,
          justifyContent: isCentered ? "center" : "flex-start",
          gap: gap,
          p: size.container,
          borderRadius: `${radius}px`,
          overflow: "hidden",
          fontFamily: TYPOGRAPHY.fontFamily,
          zIndex: 1,
        }}
      >
        {backgroundImage && <WidgetImage src={backgroundImage} position="bg" />}

        <Box sx={{ position: "relative", zIndex: 1, display: "flex", flexDirection: "column", alignItems: isCentered ? "center" : "stretch", gap: gap, width: "100%" }}>
          {topContent.map(([key, value]) => renderContent(key, value))}

          {/* Header row: icon + title together */}
          {hasHeader && (
            <Box sx={{ display: "flex", flexDirection: isCentered ? "column" : "row", alignItems: "center", gap: isCentered ? 1.5 : 1 }}>
              {props.ic && renderContent("ic", props.ic)}
              {props.t && renderContent("t", props.t, streamingKey === "t")}
            </Box>
          )}

          {/* Body content */}
          <Box sx={{ display: "flex", flexDirection: direction, alignItems: isCentered ? "center" : (direction === "row" ? "center" : "stretch"), gap: gap, flexWrap: "wrap", width: "100%" }}>
            {bodyKeys.map(key => {
              const isCurrentlyStreaming = streamingKey === key;
              return renderContent(key, props[key], isCurrentlyStreaming);
            })}

            {skeletonKeys.map(key => <WidgetSkeleton key={`skeleton-${key}`} type={key} />)}
          </Box>

          {bottomContent.map(([key, value]) => renderContent(key, value))}

          {overlayContent.length > 0 && (
            <Box sx={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2 }}>
              {overlayContent.map(([key, value]) => renderContent(key, value))}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  );
}
