"use client";

import DynamicThemeProvider from "@/app/contexts/DynamicThemeProvider";
import { Alert, Box, lighten, Paper, Snackbar } from "@mui/material";
import { motion } from "framer-motion";
import { useState } from "react";
import ChatHeader from "../Chat/ChatHeader";
import ChatInputBar from "../Chat/ChatInputBar";
import MessageList from "../Chat/MessageList";

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

export default function ChatPreview({ projectData }) {
  const [error, setError] = useState("");

  const messages = [];
  const connected = true;
  const loading = false;
  const isListening = false;

  const sendMessage = () => {};
  const clearChat = () => {};
  const toggleSpeechRecognition = () => {};

  const getBackgroundStyle = () => {
    if (projectData.backgroundImage) {
      return {
        backgroundImage: `url(${projectData.backgroundImage})`,
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundRepeat: "no-repeat",
      };
    }
    return {
      backgroundColor: lighten(projectData.backgroundColor || "#F5F5F5", 0.5),
    };
  };

  return (
    <DynamicThemeProvider projectConfig={projectData}>
      <Box
        sx={{
          height: "100%",
          width: "100%",
          borderRadius: 2,
          overflow: "hidden",
          transition: "all 0.1s ease",
          justifyContent: "center",
          alignItems: "center",
          display: "flex",
          ...getBackgroundStyle(),
        }}
      >
        <Box
          maxWidth="md"
          sx={{
            display: "flex",
            flexDirection: "column",
            justifyContent: "center",
            alignItems: "center",
            height: "100%",
            width: "100%",
            minWidth: 500,
            padding: 8,
            gap: { xs: 1, sm: 2 },
          }}
        >
          <Paper
            component={motion.div}
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
              boxShadow: "0px 0px 15px rgba(0, 0, 0, 0.1)",
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
              projectName={projectData.name}
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
                projectName={projectData.name}
                logoUrl={projectData.logoUrl}
              />
            </Box>

            <Snackbar
              open={!!error}
              autoHideDuration={6000}
              onClose={() => setError("")}
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
            <Paper
              sx={{
                maxWidth: "md",
                width: "100%",
                borderRadius: 6,
                backgroundColor: "white",
                boxShadow: "0 8px 24px -8px rgba(0, 0, 0, 0.15)",
                border: "1px solid rgba(255, 255, 255, 0.2)",
              }}
            >
              <ChatInputBar
                onSendMessage={sendMessage}
                onToggleSpeechRecognition={toggleSpeechRecognition}
                isConnected={true}
                isListening={isListening}
                isPreview={true}
              />
            </Paper>
          </motion.div>
        </Box>
      </Box>
    </DynamicThemeProvider>
  );
}
