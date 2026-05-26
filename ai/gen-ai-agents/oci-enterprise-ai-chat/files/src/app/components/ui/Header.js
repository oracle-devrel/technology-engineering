"use client";

import { Avatar, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, Divider, IconButton, ListItemIcon, ListSubheader, Menu, MenuItem, Skeleton, Tooltip, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import Image from "next/image";
import { Building2, Check, ChevronDown, ClipboardCopy, Download, LogOut, Menu as MenuIcon, Share2, SquarePen, Users, X } from "lucide-react";
import { useEffect, useState } from "react";
import BubbleModelSelector from "./BubbleModelSelector";

const BrainFreezeIcon = ({ size = 16, color = "currentColor" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24">
    <path fill={color} d="M13 3c3.88 0 7 3.14 7 7c0 2.8-1.63 5.19-4 6.31V21H9v-3H8c-1.11 0-2-.89-2-2v-3H4.5c-.42 0-.66-.5-.42-.81L6 9.66A7.003 7.003 0 0 1 13 3m0-2C8.41 1 4.61 4.42 4.06 8.9L2.5 11h-.03l-.02.03c-.55.76-.62 1.76-.19 2.59c.36.69 1 1.17 1.74 1.32V16c0 1.85 1.28 3.42 3 3.87V23h11v-5.5c2.5-1.67 4-4.44 4-7.5c0-4.97-4.04-9-9-9m4.33 8.3l-1.96.51l1.44 1.46c.35.34.35.92 0 1.27s-.93.35-1.27 0l-1.45-1.44l-.52 1.96c-.12.49-.61.76-1.07.64a.91.91 0 0 1-.66-1.11l.53-1.96l-1.96.53a.91.91 0 0 1-1.11-.66c-.12-.45.16-.95.64-1.07l1.96-.52l-1.44-1.45a.9.9 0 0 1 1.27-1.27l1.46 1.44l.51-1.96c.12-.49.62-.77 1.09-.64c.49.13.77.62.64 1.1L14.9 8.1l1.97-.53c.48-.13.97.15 1.1.64c.13.47-.15.97-.64 1.09"/>
  </svg>
);

export default function Header({
  models = [],
  selectedModel,
  onModelChange,
  loadingModels,
  onNewConversation,
  isMobile = false,
  onMenuToggle,
  chatHistory = [],
  showLabChip = true,
  showLabIcon = true,
  appTitle = "",


  accentColor = "#C74634",
  minimal = false,
  isDarkBg = false,
  appMode,
  onToggleAppMode,
}) {
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [user, setUser] = useState(null);
  const [loadingUser, setLoadingUser] = useState(true);
  const [authEnabled, setAuthEnabled] = useState(null); // null until we know
  const [userMenuAnchor, setUserMenuAnchor] = useState(null);
  const [shareOpen, setShareOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const [hasAnimated, setHasAnimated] = useState(false);
  useEffect(() => {
    const key = "header-animated";
    if (sessionStorage.getItem(key)) setHasAnimated(true);
    else sessionStorage.setItem(key, "1");
  }, []);

  const buildExportData = () => ({
    exported_at: new Date().toISOString(),
    model: selectedModel,
    exchange_count: chatHistory.length,
    exchanges: chatHistory.map(exchange => ({
      user: exchange.userMessage || null,
      assistant: exchange.rawAssistantText || null,
      assistant_parsed: exchange.responses || [],
    })),
  });

  const handleDownloadConversation = () => {
    const exportData = buildExportData();
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setShareOpen(false);
  };

  const handleCopyConversation = () => {
    const text = JSON.stringify(buildExportData(), null, 2);
    const doCopy = () => {
      if (navigator.clipboard?.writeText) {
        return navigator.clipboard.writeText(text);
      }
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.cssText = "position:fixed;opacity:0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
      return Promise.resolve();
    };
    doCopy().then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => {
    fetch('/api/auth/session')
      .then(res => res.json())
      .then(data => {
        setAuthEnabled(data.authEnabled !== false);
        if (data.authenticated) setUser(data.user);
      })
      .catch(() => setAuthEnabled(false))
      .finally(() => setLoadingUser(false));
  }, []);

  return (
    <Box
      sx={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        px: { xs: 1.5, md: 3 },
        py: 1.5,
        zIndex: 100,
        backgroundColor: isDarkBg ? "rgba(26, 26, 26, 0.85)" : "rgba(255, 255, 255, 0.8)",
        backdropFilter: "blur(10px)",
      }}
    >
      {/* Left side: hamburger (mobile) + Title */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
        {isMobile && onMenuToggle && (
          <IconButton
            onClick={onMenuToggle}
            sx={{
              color: isDarkBg ? "rgba(255,255,255,0.6)" : "rgba(0, 0, 0, 0.5)",
              p: 1,
              "&:hover": {
                backgroundColor: "rgba(0, 0, 0, 0.04)",
              },
            }}
          >
            <MenuIcon size={22} />
          </IconButton>
        )}
        <motion.div
          initial={hasAnimated ? false : { opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.6,
            delay: 0,
            ease: [0.25, 0.46, 0.45, 0.94],
          }}
        >
          <Box
            onClick={onNewConversation}
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              cursor: "pointer",
              "&:hover": {
                opacity: 0.7,
              },
            }}
          >
            {showLabIcon && <Image src="/entypo--lab-flask.svg" alt="Lab Flask" width={20} height={20} style={isDarkBg ? { filter: "invert(1)" } : undefined} />}
            <Typography
              variant="h1"
              sx={{
                fontSize: { xs: "0.9rem", sm: "1rem", md: "1.1rem" },
                fontWeight: 300,
                color: isDarkBg ? "#e5e5e5" : "#1a1a1a",
                letterSpacing: "0.02em",
                fontFamily: "var(--font-oracle-sans), sans-serif",
                userSelect: "none",
                lineHeight: 1.3,
              }}
            >
              {appTitle || (<><Box component="span" sx={{ fontWeight: 600 }}>OCI</Box>{" "}Enterprise AI</>)}
            </Typography>
            {showLabChip && (
              <Chip
                label="BLACK BELTS LAB"
                size="small"
                variant="outlined"
                sx={{
                  display: { xs: "none", md: "flex" },
                  fontSize: "0.55rem",
                  height: 18,
                  borderRadius: "4px",
                  borderColor: "rgba(0, 0, 0, 0.2)",
                  color: isDarkBg ? "rgba(255,255,255,0.6)" : "rgba(0, 0, 0, 0.5)",
                  fontWeight: 500,
                  letterSpacing: "0.1em",
                }}
              />
            )}
          </Box>
        </motion.div>
      </Box>

      {/* Right controls */}
      {!minimal && <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {/* Model selector - desktop only */}
        {!isMobile && (
          <>
            <Tooltip title={selectedModel?.replace(/^[a-z]+\./, "") || "Select model"} placement="bottom">
              <Box
                onClick={(e) => !loadingModels && setMenuAnchor(e.currentTarget)}
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1,
                  cursor: loadingModels ? "default" : "pointer",
                  backgroundColor: "transparent",
                  borderRadius: 1,
                  px: 1.5,
                  py: 0.75,
                  "&:hover": {
                    backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                  },
                }}
              >
                <AnimatePresence mode="wait">
                  {loadingModels ? (
                    <motion.div
                      key="skeleton"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Skeleton
                        variant="text"
                        width={120}
                        sx={{
                          bgcolor: "rgba(0, 0, 0, 0.08)",
                          fontSize: "1rem",
                        }}
                      />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="text"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      style={{ display: "flex", alignItems: "center", gap: 8 }}
                    >
                      <BrainFreezeIcon size={20} color={isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0, 0, 0, 0.4)"} />
                      {/* Model name label hidden temporarily — tooltip still shows it on hover */}
                    </motion.div>
                  )}
                </AnimatePresence>
                <ChevronDown size={14} color={isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0, 0, 0, 0.3)"} />
              </Box>
            </Tooltip>

            <BubbleModelSelector
              models={models}
              selectedModel={selectedModel}
              onModelChange={onModelChange}
              anchorEl={menuAnchor}
              open={Boolean(menuAnchor)}
              onClose={() => setMenuAnchor(null)}
              accentColor={accentColor}
            />
          </>
        )}

        {/* App Mode toggle — mobile only */}
        {isMobile && appMode && onToggleAppMode && (
          <Tooltip title={appMode === "internal" ? "Internal mode" : "Client mode"} placement="bottom">
            <IconButton
              onClick={onToggleAppMode}
              sx={{
                color: isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0, 0, 0, 0.4)",
                backgroundColor: "transparent",
                "&:hover": {
                  backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                  color: isDarkBg ? "rgba(255,255,255,0.7)" : "rgba(0, 0, 0, 0.6)",
                },
              }}
            >
              {appMode === "internal" ? <Building2 size={20} strokeWidth={2} /> : <Users size={20} strokeWidth={2} />}
            </IconButton>
          </Tooltip>
        )}

        <Tooltip title="Share conversation" placement="bottom">
          <span>
            <IconButton
              onClick={() => setShareOpen(true)}
              disabled={chatHistory.length === 0}
              sx={{
                color: isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0, 0, 0, 0.4)",
                backgroundColor: "transparent",
                "&:hover": {
                  backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                  color: isDarkBg ? "rgba(255,255,255,0.7)" : "rgba(0, 0, 0, 0.6)",
                },
                "&.Mui-disabled": {
                  color: isDarkBg ? "rgba(255,255,255,0.15)" : "rgba(0, 0, 0, 0.15)",
                },
              }}
            >
              <Share2 size={20} />
            </IconButton>
          </span>
        </Tooltip>

        <Tooltip title="New conversation" placement="bottom">
          <IconButton
            onClick={onNewConversation}
            sx={{
              color: isDarkBg ? "rgba(255,255,255,0.5)" : "rgba(0, 0, 0, 0.4)",
              backgroundColor: "transparent",
              "&:hover": {
                backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0,0,0,0.04)",
                color: isDarkBg ? "rgba(255,255,255,0.7)" : "rgba(0, 0, 0, 0.6)",
              },
            }}
          >
            <SquarePen size={20} />
          </IconButton>
        </Tooltip>

        {/* User avatar - desktop only. Skeleton only when auth is on. */}
        {!isMobile && loadingUser && authEnabled !== false && (
          <IconButton disabled sx={{ ml: 0.5 }}>
            <Skeleton variant="circular" width={36} height={36} />
          </IconButton>
        )}
        {!isMobile && !loadingUser && user && (
          <>
            <Tooltip title={user.name || user.email} placement="bottom">
              <IconButton
                onClick={(e) => setUserMenuAnchor(e.currentTarget)}
                sx={{ ml: 0.5 }}
              >
                <Avatar
                  sx={{
                    width: 36,
                    height: 36,
                    fontSize: "0.95rem",
                    bgcolor: "#1a1a1a",
                  }}
                >
                  {(user.name || user.email || "U").charAt(0).toUpperCase()}
                </Avatar>
              </IconButton>
            </Tooltip>
            <Menu
              anchorEl={userMenuAnchor}
              open={Boolean(userMenuAnchor)}
              onClose={() => setUserMenuAnchor(null)}
              PaperProps={{ sx: { minWidth: 180 } }}
            >
              <MenuItem disabled sx={{ opacity: "1 !important" }}>
                <Box>
                  <Typography sx={{ fontSize: "0.85rem", fontWeight: 500 }}>
                    {user.name}
                  </Typography>
                  <Typography sx={{ fontSize: "0.7rem", color: "text.secondary" }}>
                    {user.email}
                  </Typography>
                  <Chip
                    label="Oracle IDCS"
                    size="small"
                    sx={{
                      mt: 0.75,
                      fontSize: "0.6rem",
                      height: 18,
                      borderRadius: "4px",
                      bgcolor: "rgba(200, 50, 50, 0.08)",
                      color: "#c83232",
                      fontWeight: 600,
                      letterSpacing: "0.03em",
                    }}
                  />
                </Box>
              </MenuItem>
              <Divider />
              <MenuItem
                onClick={() => { window.location.href = '/api/auth/logout'; }}
                sx={{ fontSize: "0.85rem", color: "error.main" }}
              >
                <ListItemIcon sx={{ minWidth: 28 }}>
                  <LogOut size={16} color="#d32f2f" />
                </ListItemIcon>
                Sign out
              </MenuItem>
            </Menu>
          </>
        )}
      </Box>}

      {/* Share Dialog */}
      <Dialog open={shareOpen} onClose={() => setShareOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle sx={{ pb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Share2 size={18} />
              <Typography sx={{ fontWeight: 600, fontSize: '1rem' }}>Share conversation</Typography>
            </Box>
            <IconButton onClick={() => setShareOpen(false)} size="small" sx={{ color: 'text.secondary' }}>
              <X size={18} />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography sx={{ fontSize: '0.85rem', color: 'text.secondary', mb: 2 }}>
            Download a JSON file with the full conversation.
          </Typography>
          <Box sx={{ backgroundColor: 'rgba(0,0,0,0.03)', borderRadius: 1, p: 2, border: '1px solid rgba(0,0,0,0.07)' }}>
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', mb: 0.5, fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Summary
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography sx={{ fontSize: '0.82rem', color: 'text.secondary' }}>Exchanges</Typography>
                <Typography sx={{ fontSize: '0.82rem', fontWeight: 500 }}>{chatHistory.length}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography sx={{ fontSize: '0.82rem', color: 'text.secondary' }}>Model</Typography>
                <Typography sx={{ fontSize: '0.82rem', fontWeight: 500 }}>{selectedModel?.replace(/^[a-z]+\./, '') || '—'}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography sx={{ fontSize: '0.82rem', color: 'text.secondary' }}>Exported at</Typography>
                <Typography sx={{ fontSize: '0.82rem', fontWeight: 500 }}>{new Date().toLocaleString()}</Typography>
              </Box>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button
            onClick={handleCopyConversation}
            variant="outlined"
            startIcon={copied ? <Check size={16} /> : <ClipboardCopy size={16} />}
            sx={{ fontSize: '0.85rem', textTransform: 'none', borderRadius: 1.5, color: copied ? 'success.main' : undefined, borderColor: copied ? 'success.main' : undefined }}
          >
            {copied ? 'Copied!' : 'Copy JSON'}
          </Button>
          <Button
            onClick={handleDownloadConversation}
            variant="contained"
            startIcon={<Download size={16} />}
            sx={{ fontSize: '0.85rem', textTransform: 'none', borderRadius: 1.5 }}
          >
            Download JSON
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
