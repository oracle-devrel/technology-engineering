"use client";

import { Box } from "@mui/material";
import { motion } from "framer-motion";

export default function TypingIndicator() {
  const dotVariants = {
    animate: {
      scale: [1, 1.2, 1],
      opacity: [0.4, 1, 0.4],
      transition: {
        duration: 1.4,
        repeat: Infinity,
        ease: "easeInOut",
      },
    },
  };

  const containerVariants = {
    animate: {
      transition: {
        staggerChildren: 0.2,
        repeat: Infinity,
      },
    },
  };

  return (
    <Box
      component="li"
      sx={{
        display: "flex",
        justifyContent: "flex-start",
        width: "100%",
        padding: "4px 16px",
        listStyle: "none",
      }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          maxWidth: "80%",
          width: "auto",
          padding: "8px 12px",
          borderRadius: "20px",
          backgroundColor: "rgba(0, 0, 0, 0.05)",
          alignItems: "flex-start",
        }}
      >
        <motion.div
          variants={containerVariants}
          animate="animate"
          style={{
            display: "flex",
            alignItems: "center",
            gap: "3px",
            padding: 4,
            color: "rgba(0, 0, 0, 0.6)",
          }}
        >
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              variants={dotVariants}
              style={{
                width: "6px",
                height: "6px",
                borderRadius: "50%",
                backgroundColor: "currentColor",
                opacity: 0.4,
              }}
            />
          ))}
        </motion.div>
      </Box>
    </Box>
  );
}
