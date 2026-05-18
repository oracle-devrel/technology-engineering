"use client";

import { Box, IconButton, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { Settings, Upload } from "lucide-react";
import { useRouter } from "next/navigation";
import BlinkingEye from "../ui/BlinkingEye";
import { memo, useState, useCallback, useRef, useEffect } from "react";
import TypingEffect from "../ui/TypingEffect";
import ScrollableList from "../ui/ScrollableList";
import OracleLogo from "../ui/OracleLogo";
import ChatInput, { TEXT_EXTENSIONS } from "./ChatInput";

const fontSizes = { xs: "1.5rem", sm: "1.8rem", md: "2rem" };
const textFieldFontSizes = { xs: "1.1rem", sm: "1.3rem", md: "1.5rem" };

const commonTextStyles = {
  fontSize: fontSizes,
  fontWeight: 300,
  textAlign: "left",
  lineHeight: 1.4,
  margin: 0,
};

const ChatSidebar = memo(function ChatSidebar({
  uiSettings,
  showTextField,
  chatHistoryLength,
  inputRef,
  onSubmit,
  onStop,
  recentConversations,
  loadingConversations = false,
  hasMoreConversations = false,
  isLoadingMoreConversations = false,
  onLoadMoreConversations,
  activeConversationId,
  onConversationClick,
  onConversationDelete,
  onRefreshConversations,
  isLoading = false,
  width = 30,
  selectedModel,

  accentColor = "#C74634",
  iconTint,
  isDarkBg = false,
}) {
  const router = useRouter();
  const [isDragging, setIsDragging] = useState(false);
  const [attachmentCount, setAttachmentCount] = useState(0);
  const inputWrapperRef = useRef(null);
  const dragCounterRef = useRef(0);

  const isValidFile = useCallback((file) => {
    return file.type.startsWith('image/') ||
      file.type.startsWith('text/') ||
      file.type === 'application/pdf' ||
      file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      file.type === 'application/vnd.ms-excel' ||
      file.name.toLowerCase().endsWith('.pdf') ||
      /\.(xlsx|xls)$/i.test(file.name) ||
      TEXT_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));
  }, []);

  const handleDragEnter = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current++;

    // Check if dragging files
    if (e.dataTransfer?.types?.includes('Files')) {
      setIsDragging(true);
    }
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounterRef.current--;
    if (dragCounterRef.current === 0) {
      setIsDragging(false);
    }
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
    if (files?.length > 0 && inputRef?.current?.addFiles) {
      // Filter valid files
      const validFiles = Array.from(files).filter(isValidFile);
      if (validFiles.length > 0) {
        inputRef.current.addFiles(validFiles);
        inputRef.current.focus();
      }
    }
  }, [inputRef, isValidFile]);

  return (
    <Box
      id="chat-sidebar-root"
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDragOver={handleDragOver}
      onDrop={handleDrop}
      sx={{
        flex: `0 0 ${width}%`,
        minWidth: 0,
        paddingTop: "10vh",
        paddingLeft: 4,
        paddingRight: 4,
        display: "flex",
        flexDirection: "column",
        height: "100%",
        position: "relative",
        overflow: "visible",
        clipPath: "inset(0px -4.5px 0px 0px)",
      }}
    >
      {/* Drop overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            id="chat-sidebar-drop-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            style={{
              position: "absolute",
              top: 16,
              left: 16,
              right: 16,
              bottom: 16,
              backgroundColor: "rgba(255, 255, 255, 0.85)",
              border: "2px dashed rgba(0, 0, 0, 0.2)",
              borderRadius: 12,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              zIndex: 100,
              pointerEvents: "none",
            }}
          >
            <Upload size={32} style={{ color: "rgba(0, 0, 0, 0.3)" }} />
            <Typography sx={{ color: "rgba(0, 0, 0, 0.5)", fontWeight: 500 }}>
              Drop files here
            </Typography>
            <Typography sx={{ color: "rgba(0, 0, 0, 0.35)", fontSize: "0.8rem" }}>
              Images and text files
            </Typography>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Logo */}
      <Box id="chat-sidebar-logo" sx={{ mb: 1 }}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: 0.5,
            delay: 0.1,
            ease: [0.25, 0.46, 0.45, 0.94],
          }}
        >
          {uiSettings.appLogo ? (
            <img
              src={uiSettings.appLogo}
              alt="App Logo"
              style={{
                maxHeight: "50px",
                width: "auto",
                objectFit: "contain",
                userSelect: "none",
                ...(isDarkBg && { filter: "brightness(0) invert(1)", opacity: 0.85 }),
              }}
            />
          ) : (
            <OracleLogo accentColor={accentColor} isDarkBg={isDarkBg} maxHeight={100} />
          )}
        </motion.div>
      </Box>

      {/* Welcome message - only shows when no chat history and no attachments */}
      <AnimatePresence>
        {chatHistoryLength === 0 && attachmentCount === 0 && (
          <motion.div
            initial={{ opacity: 1, height: "auto" }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0, marginTop: 0, marginBottom: 0 }}
            transition={{ duration: 0.35, ease: [0.4, 0, 0.2, 1] }}
            style={{ overflow: "hidden" }}
          >
            <Box id="chat-sidebar-message" sx={{ minHeight: "100px" }}>
              <TypingEffect text="Hey," speed={50}>
                {(displayedText) => (
                  <Typography
                    variant="h3"
                    sx={{
                      ...commonTextStyles,
                      minHeight: "40px",
                      color: isDarkBg ? "#e5e5e5" : "#000000",
                    }}
                  >
                    {displayedText}
                  </Typography>
                )}
              </TypingEffect>
              <TypingEffect
                text={uiSettings.welcomeMessage}
                speed={50}
                delay={200}
              >
                {(displayedText) => (
                  <Typography
                    variant="h3"
                    sx={{
                      ...commonTextStyles,
                      minHeight: "40px",
                      color: isDarkBg ? "#e5e5e5" : "#000000",
                    }}
                  >
                    {displayedText}
                  </Typography>
                )}
              </TypingEffect>
            </Box>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Input */}
      <AnimatePresence>
        {showTextField && (
          <motion.div
            ref={inputWrapperRef}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.6,
              ease: [0.25, 0.46, 0.45, 0.94],
            }}
          >
            <ChatInput
              ref={inputRef}
              onSubmit={onSubmit}
              onStop={onStop}
              placeholder={uiSettings.inputPlaceholder}
              fontSize={textFieldFontSizes}
              disabled={isLoading}
              isLoading={isLoading}
              selectedModel={selectedModel}
              accentColor={iconTint}
              isDarkBg={isDarkBg}
              onAttachmentsChange={setAttachmentCount}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom section - Recent conversations + Settings */}
      <Box
        id="chat-sidebar-bottom"
        sx={{
          marginTop: "auto",
          flexShrink: 0,
          maxHeight: "320px",
          maxWidth: "200px",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Recent conversations */}
        <Box sx={{ flex: 1, overflow: "hidden" }}>
          <ScrollableList
            title="Recent conversations"
            titleDelay={0}
            bgColor={isDarkBg ? "#1a1a1a" : "white"}
            isDarkBg={isDarkBg}

            accentColor={accentColor}
            items={recentConversations}
            initialLoading={loadingConversations}
            activeId={activeConversationId}
            onItemClick={(item) => {
              if (item && item.id) {
                onConversationClick(item);
              }
            }}
            onItemDelete={onConversationDelete}
            onRefresh={onRefreshConversations}
            hasMore={hasMoreConversations}
            isLoadingMore={isLoadingMoreConversations}
            onLoadMore={onLoadMoreConversations}
          />
        </Box>

        {/* Settings icon */}
        <Box sx={{ flexShrink: 0, paddingBottom: "2rem" }}>
          <IconButton
            onClick={() => router.push("/settings")}
            sx={{
              color: isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0, 0, 0, 0.3)",
              p: 1,
              "&:hover": {
                backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)",
                color: isDarkBg ? "rgba(255,255,255,0.6)" : "rgba(0, 0, 0, 0.5)",
              },
            }}
          >
            <Settings sx={{ fontSize: "1.2rem" }} />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
});

export default ChatSidebar;
