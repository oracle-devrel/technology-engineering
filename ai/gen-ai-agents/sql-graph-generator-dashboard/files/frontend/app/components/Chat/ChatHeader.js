"use client";

import { LoupeOutlined } from "@mui/icons-material";
import { Box, IconButton, Stack, Tooltip, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/navigation";

export default function ChatHeader({
  messagesCount,
  onNewChat,
  isConnected = false,
  projectName,
}) {
  const router = useRouter();

  const titleVariants = {
    initial: {
      opacity: 0,
      y: -10,
      scale: 0.95,
    },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 25,
        duration: 0.4,
      },
    },
    exit: {
      opacity: 0,
      y: -10,
      scale: 0.95,
      transition: {
        duration: 0.2,
      },
    },
  };

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
      }}
    >
      <Box sx={{ display: "flex", alignItems: "center", flexGrow: 1, ml: 1.5 }}>
        <Box
          sx={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: isConnected ? "#4CAF50" : "#9e9e9e",
            marginRight: 1,
          }}
        />
        <AnimatePresence mode="wait">
          {messagesCount > 0 && (
            <motion.div
              key="project-title"
              variants={titleVariants}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <Typography variant="body2" component="div">
                {projectName}
              </Typography>
            </motion.div>
          )}
        </AnimatePresence>
      </Box>

      <Stack direction="row" alignItems={"center"} spacing={1}>
        <Tooltip title="New chat" placement="top">
          <IconButton
            onClick={onNewChat}
            disabled={messagesCount === 0}
            sx={{ mr: 1 }}
            size="small"
          >
            <LoupeOutlined />
          </IconButton>
        </Tooltip>
      </Stack>
    </Box>
  );
}
