"use client";

import DynamicThemeProvider from "@/app/contexts/DynamicThemeProvider";
import {
  Alert,
  alpha,
  Box,
  Container,
  lighten,
  Paper,
  Snackbar,
  Typography,
} from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import { useChat } from "../../contexts/ChatContext";
import { useProject } from "../../contexts/ProjectsContext";
import NavMenu from "../NavMenu";
import ChatHeader from "./ChatHeader";
import ChatInputBar from "./ChatInputBar";
import MessageList from "./MessageList";

const containerVariants = {
  initial: {
    scale: 0.8,
    opacity: 0,
  },
  animate: {
    scale: 1,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 260,
      damping: 20,
    },
  },
};

const dynamicIslandVariants = {
  initial: {
    y: 100,
    opacity: 0,
  },
  animate: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 350,
      damping: 25,
      delay: 0.3,
    },
  },
};

const logoVariants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      duration: 0.3,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.2,
    },
  },
};

export default function Chat({ onAddProject, onEditProject, onDeleteProject }) {
  const {
    messages,
    connected,
    loading,
    error,
    isListening,
    isWaitingForResponse,
    sendMessage,
    sendAttachment,
    clearChat,
    toggleSpeechRecognition,
    setError,
    currentSpeechProvider,
  } = useChat();

  const { getCurrentProject } = useProject();
  const currentProject = getCurrentProject();

  const [isDragOver, setIsDragOver] = useState(false);

  const isOracleRecording = currentSpeechProvider === "oracle" && isListening;

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!e.currentTarget.contains(e.relatedTarget)) {
      setIsDragOver(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      const isValidType =
        file.type.startsWith("image/") || file.type === "application/pdf";

      if (isValidType) {
        window.dispatchEvent(new CustomEvent("fileDropped", { detail: file }));
      }
    }
  };

  const getBackgroundStyle = () => {
    if (currentProject.backgroundImage) {
      return {
        backgroundImage: `url(${currentProject.backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      };
    }
    return {
      backgroundColor: lighten(
        currentProject.backgroundColor || "#F5F5F5",
        0.5
      ),
    };
  };

  const hasMessages = messages.length > 0 || isWaitingForResponse;

  return (
    <DynamicThemeProvider projectConfig={currentProject}>
      <Box
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        sx={{
          minHeight: "100vh",
          transition: "all 0.5s ease",
          position: "relative",
          ...getBackgroundStyle(),
        }}
      >
        {isDragOver && (
          <Box
            sx={{
              position: "fixed",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: alpha(
                currentProject.mainColor || "#007AFF",
                0.1
              ),
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 9999,
              pointerEvents: "none",
              backdropFilter: "blur(1px)",
            }}
          >
            <Typography
              variant="h4"
              sx={{
                color: currentProject.mainColor || "#007AFF",
                fontWeight: 600,
                textAlign: "center",
              }}
            >
              📎 Drop images or PDFs here
            </Typography>
          </Box>
        )}

        <Container
          maxWidth="lg"
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100vh",
            padding: { xs: 2, sm: 10 },
            gap: { xs: 1, sm: 2 },
          }}
        >
          <Box
            sx={{
              position: "absolute",
              top: "50%",
              left: 20,
              transform: "translateY(-50%)",
              zIndex: 10,
            }}
          >
            <NavMenu
              onAddProject={onAddProject}
              onEditProject={onEditProject}
              onDeleteProject={onDeleteProject}
            />
          </Box>

          <Paper
            component={motion.div}
            elevation={0}
            maxWidth="md"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            sx={{
              height: "100%",
              px: 1,
              pt: 1,
              display: "flex",
              flexDirection: "column",
              position: "relative",
              overflow: "hidden",
              width: "100%",
              borderRadius: 2,
            }}
          >
            <ChatHeader
              messagesCount={messages.length}
              onNewChat={clearChat}
              isConnected={connected}
              projectName={currentProject.name}
            />

            <Box
              sx={{
                flexGrow: 1,
                overflow: "auto",
                display: "flex",
                flexDirection: "column",
                mt: 2,
              }}
            >
              <MessageList
                messages={messages}
                loading={loading}
                projectName={currentProject.name}
                logoUrl={currentProject.logoUrl}
                onSendMessage={sendMessage}
                isWaitingForResponse={isWaitingForResponse}
              />
            </Box>

            <AnimatePresence>
              {hasMessages && (
                <motion.div
                  key="floating-logo"
                  variants={logoVariants}
                  initial="initial"
                  animate="animate"
                  exit="exit"
                  style={{
                    position: "absolute",
                    bottom: 0,
                    left: 0,
                    right: 0,
                    zIndex: 10,
                  }}
                >
                  <Box
                    sx={{
                      position: "relative",
                      display: "flex",
                      alignItems: "flex-end",
                      justifyContent: "flex-start",
                      background:
                        "linear-gradient(to top, rgba(255,255,255,1) 40%, rgba(255,255,255,0.8) 80%, rgba(255,255,255,0) 100%)",
                      height: "80px",
                      width: "100%",
                    }}
                  >
                    <Box
                      component="img"
                      src={currentProject.logoUrl || "/oda-logo.png"}
                      alt={`${currentProject.name} logo`}
                      sx={{
                        maxHeight: 32,
                        maxWidth: 120,
                        mb: 2,
                        ml: 2,
                        objectFit: "contain",
                      }}
                    />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>

            <Snackbar
              open={!!error}
              autoHideDuration={6000}
              onClose={() => setError("")}
              anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
            >
              <Alert onClose={() => setError("")} severity="error">
                {error}
              </Alert>
            </Snackbar>
          </Paper>

          <motion.div
            variants={dynamicIslandVariants}
            initial="initial"
            animate="animate"
            style={{
              display: "flex",
              justifyContent: "center",
              width: "100%",
            }}
          >
            <ChatInputBar
              onSendMessage={sendMessage}
              onToggleSpeechRecognition={toggleSpeechRecognition}
              onSendAttachment={sendAttachment}
              isConnected={connected}
              isListening={isListening}
              currentSpeechProvider={currentSpeechProvider}
            />
          </motion.div>
        </Container>
      </Box>
    </DynamicThemeProvider>
  );
}
