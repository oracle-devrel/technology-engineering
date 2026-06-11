"use client";

import { Box, Chip, Typography } from "@mui/material";
import { motion } from "framer-motion";
import Image from "next/image";
import { useState, useEffect } from "react";
import TypingEffect from "../components/ui/TypingEffect";

export default function IntroPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <Box
      sx={{
        height: "100vh",
        width: "100vw",
        backgroundColor: "white",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        fontFamily: "var(--font-oracle-sans), sans-serif",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Flask icon - appears first, alone, centered */}
      <motion.div
        initial={{ opacity: 0, scale: 0, rotate: -20 }}
        animate={{ opacity: 1, scale: 1, rotate: 0 }}
        transition={{
          duration: 0.8,
          delay: 0.5,
          ease: [0.34, 1.56, 0.64, 1],
        }}
        style={{ display: "flex", alignItems: "center", marginBottom: 10 }}
      >
        <Image
          src="/entypo--lab-flask.svg"
          alt="Lab Flask"
          width={48}
          height={48}
          style={{ opacity: 0.85 }}
        />
      </motion.div>

      {/* Title - appears after flask with typing animation */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1.8, ease: "easeOut" }}
      >
        <Typography
          variant="h1"
          sx={{
            fontSize: { xs: "1.6rem", sm: "2rem", md: "2.4rem" },
            fontWeight: 300,
            color: "#1a1a1a",
            letterSpacing: "0.02em",
            fontFamily: "var(--font-oracle-sans), sans-serif",
            userSelect: "none",
            lineHeight: 1.3,
            textAlign: "center",
            minHeight: "3rem",
          }}
        >
          <TypingEffect text="OCI" speed={80} delay={2200}>
            {(typed) => (
              <Box component="span" sx={{ fontWeight: 600 }}>
                {typed}
              </Box>
            )}
          </TypingEffect>
          <TypingEffect text={" Enterprise AI Agents"} speed={45} delay={2600} />
        </Typography>
      </motion.div>

      {/* BLACK BELTS LAB chip */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 4.6, ease: "easeOut" }}
        style={{ marginTop: 16 }}
      >
        <Chip
          label="BLACK BELTS LAB"
          size="small"
          variant="outlined"
          sx={{
            fontSize: "0.75rem",
            height: 26,
            borderRadius: "5px",
            borderColor: "rgba(0, 0, 0, 0.2)",
            color: "rgba(0, 0, 0, 0.45)",
            fontWeight: 500,
            letterSpacing: "0.14em",
            px: 1,
          }}
        />
      </motion.div>

      {/* Subtle background pattern */}
      <Box
        sx={{
          position: "absolute",
          inset: 0,
          opacity: 0.02,
          background: `
            radial-gradient(circle at 30% 40%, rgba(0,0,0,0.1) 0%, transparent 50%),
            radial-gradient(circle at 70% 60%, rgba(0,0,0,0.1) 0%, transparent 50%)
          `,
          pointerEvents: "none",
          zIndex: -1,
        }}
      />
    </Box>
  );
}
