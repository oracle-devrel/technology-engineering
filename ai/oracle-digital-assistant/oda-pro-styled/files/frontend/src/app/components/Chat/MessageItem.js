"use client";

import { alpha, Box, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import { useChat } from "../../contexts/ChatContext";
import MessageContent from "./MessageContent";

export default function MessageItem({ message }) {
  const theme = useTheme();
  const { speakMessage, cancelAudio, playingMessageId, setPlayingMessageId } =
    useChat();

  const isFromBot = message.from;

  const primaryColor = theme.palette.primary.main;
  const primaryLight = theme.palette.primary.light;
  const primaryDark = theme.palette.primary.dark;

  const messageId = `${message.userId}-${message.date}`;
  const isPlaying = playingMessageId === messageId;

  const handlePlayAudio = (message) => {
    if (isPlaying) {
      cancelAudio();
    } else {
      if (playingMessageId) {
        cancelAudio();
      }
      if (speakMessage(message)) {
        setPlayingMessageId(messageId);
      }
    }
  };

  const botMessageVariants = {
    initial: {
      opacity: 0,
      x: -30,
      scale: 0.96,
    },
    animate: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 30,
        duration: 0.5,
      },
    },
  };

  const userMessageVariants = {
    initial: {
      opacity: 0,
      x: 30,
      scale: 0.96,
    },
    animate: {
      opacity: 1,
      x: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 320,
        damping: 25,
        duration: 0.4,
      },
    },
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: isFromBot ? "flex-start" : "flex-end",
        width: "100%",
        padding: "4px 16px",
      }}
    >
      {isFromBot ? (
        <motion.div
          variants={botMessageVariants}
          initial="initial"
          animate="animate"
          style={{
            display: "flex",
            flexDirection: "column",
            maxWidth: "80%",
            width: "auto",
            padding: "12px 0",
          }}
        >
          <Box
            component={motion.div}
            animate={{
              boxShadow: isPlaying
                ? [
                    "inset 0 0 0px 0px transparent",
                    `inset 0 0 15px 2px ${theme.palette.primary.main}25`,
                    `inset 0 0 25px 3px ${theme.palette.primary.main}40`,
                    `inset 0 0 15px 2px ${theme.palette.primary.main}25`,
                  ]
                : "inset 0 0 0px 0px transparent",
            }}
            transition={{
              duration: isPlaying ? 2 : 0.5,
              repeat: isPlaying ? Infinity : 0,
              ease: "easeInOut",
            }}
            sx={{
              backgroundColor: "rgba(246, 246, 246, 0.95)",
              borderRadius: "22px",
              padding: "12px 16px",
              WebkitBackdropFilter: "blur(20px)",
            }}
          >
            <MessageContent message={message} isFromBot />
          </Box>
          {/* <Box
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              mt: 0.5,
              mr: 2,
            }}
          >
            <IconButton
              size="small"
              onClick={() => handlePlayAudio(message)}
              sx={{
                width: 24,
                height: 24,
                backgroundColor: "rgba(0, 0, 0, 0.1)",
                "&:hover": {
                  backgroundColor: "rgba(0, 0, 0, 0.2)",
                },
              }}
            >
              {isPlaying ? (
                <Stop sx={{ fontSize: 14 }} />
              ) : (
                <PlayArrow sx={{ fontSize: 14 }} />
              )}
            </IconButton>
          </Box> */}
        </motion.div>
      ) : (
        <motion.div
          variants={userMessageVariants}
          initial="initial"
          animate="animate"
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "flex-start",
            maxWidth: "80%",
            width: "auto",
            ...(message.messagePayload.type === "attachment"
              ? {
                  background: "transparent",
                  padding: 0,
                  borderRadius: 0,
                }
              : {
                  borderRadius: "22px 22px 5px 22px",
                  background: `linear-gradient(135deg, ${alpha(
                    primaryColor,
                    0.05
                  )} 0%, ${alpha(primaryDark, 0.3)} 100%)`,
                  color: "#000",
                  padding: "6px 16px 6px 16px",
                  backdropFilter: "blur(20px)",
                  WebkitBackdropFilter: "blur(20px)",
                }),
          }}
        >
          <Box sx={{ flexGrow: 1, pt: "2px" }}>
            <MessageContent message={message} />
          </Box>
        </motion.div>
      )}
    </Box>
  );
}
