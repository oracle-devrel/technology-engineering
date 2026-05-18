"use client";

import { Box, CircularProgress, List } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef } from "react";
import MessageItem from "./MessageItem";
import TypingIndicator from "./TypingIndicator";
import WelcomeScreen from "./WelcomeScreen";

export default function MessageList({
  messages,
  loading,
  projectName,
  logoUrl,
  onSendMessage,
  isWaitingForResponse = false,
}) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isWaitingForResponse]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const welcomeVariants = {
    initial: {
      opacity: 1,
      scale: 1,
    },
    exit: {
      opacity: 0,
      scale: 0.95,
      transition: {
        duration: 0.3,
        ease: "easeInOut",
      },
    },
  };

  if (loading && messages.length === 0) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", m: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const hasMessages = messages.length > 0 || isWaitingForResponse;

  return (
    <Box sx={{ position: "relative", width: "100%", height: "100%", px: 1.5 }}>
      <AnimatePresence mode="wait">
        {!hasMessages && (
          <motion.div
            key="welcome-screen"
            variants={welcomeVariants}
            initial="initial"
            exit="exit"
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center",
              paddingLeft: "24px",
              paddingRight: "24px",
            }}
          >
            <WelcomeScreen
              projectName={projectName}
              logoUrl={logoUrl}
              onSendMessage={onSendMessage}
            />
          </motion.div>
        )}
      </AnimatePresence>

      <List sx={{ width: "100%", p: 0, pb: 8 }}>
        {messages.map((msg, idx) => (
          <MessageItem key={idx} message={msg} />
        ))}
        {isWaitingForResponse && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </List>
    </Box>
  );
}
