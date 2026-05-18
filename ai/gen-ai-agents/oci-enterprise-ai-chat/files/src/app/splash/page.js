"use client";

import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

export default function SplashPage() {
  const router = useRouter();
  const [isLoaded, setIsLoaded] = useState(false);
  const [isExiting, setIsExiting] = useState(false);
  const [appTitle, setAppTitle] = useState("OCI Enterprise AI Agents");
  const [appLogo, setAppLogo] = useState("");

  useEffect(() => {
    // Load UI settings from localStorage
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('uiSettings');
      if (stored) {
        try {
          const parsedSettings = JSON.parse(stored);
          setAppTitle(parsedSettings.appTitle || "OCI Enterprise AI Agents");
          setAppLogo(parsedSettings.appLogo || "");
          // Update document title
          document.title = parsedSettings.appTitle || "OCI Enterprise AI Agents";
        } catch (e) {
          console.error('Error parsing UI settings:', e);
        }
      }
    }
    
    // Small delay to ensure smooth animations
    setTimeout(() => setIsLoaded(true), 100);
  }, []);

  const handleClick = () => {
    setIsExiting(true);
    // Wait for exit animation to complete before navigating
    setTimeout(() => {
      router.push("/");
    }, 800);
  };

  return (
    <Box
      onClick={handleClick}
      sx={{
        height: "100vh",
        width: "100vw",
        backgroundColor: "white",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        cursor: "pointer",
        fontFamily: "var(--font-oracle-sans), sans-serif",
        gap: 2,
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Oracle Logo */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={
          isExiting
            ? { opacity: 0, y: -30, scale: 0.9 }
            : isLoaded
            ? { opacity: 1, y: 0, scale: 1 }
            : { opacity: 0, y: -20, scale: 1 }
        }
        transition={{
          duration: isExiting ? 0.6 : 0.8,
          delay: isExiting ? 0 : 0.1,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
        whileHover={{
          scale: 1.05,
          transition: { duration: 0.3, ease: "easeOut" },
        }}
      >
        {appLogo ? (
          <img
            src={appLogo}
            alt="App Logo"
            style={{
              maxHeight: "160px",
              width: "auto",
              objectFit: "contain",
              userSelect: "none",
            }}
          />
        ) : (
          <Image
            src="/oracle-logo-building.png"
            alt="Logo"
            width={600}
            height={400}
            style={{
              maxHeight: "160px",
              width: "auto",
              objectFit: "contain",
              userSelect: "none",
            }}
          />
        )}
      </motion.div>

      {/* Oracle One AI Title */}
      <motion.div
        initial={{ opacity: 0, y: -30 }}
        animate={
          isExiting
            ? { opacity: 0, y: -40, scale: 0.8 }
            : isLoaded
            ? { opacity: 1, y: 0, scale: 1 }
            : { opacity: 0, y: -30, scale: 1 }
        }
        transition={{
          duration: isExiting ? 0.6 : 0.8,
          delay: isExiting ? 0.1 : 0.2,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
        whileHover={{
          scale: 1.02,
          transition: { duration: 0.3, ease: "easeOut" },
        }}
      >
        <Typography
          variant="h1"
          sx={{
            fontSize: { xs: "1.8rem", sm: "2.5rem", md: "3rem" },
            fontWeight: 300,
            color: "#1a1a1a",
            letterSpacing: "0.02em",
            textAlign: "center",
            fontFamily: "var(--font-oracle-sans), sans-serif",
            background: "linear-gradient(135deg, #1a1a1a 0%, #4a4a4a 100%)",
            backgroundClip: "text",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            userSelect: "none",
            lineHeight: 1.4,
          }}
        >
          <Box component="span" sx={{ fontWeight: 600 }}>
            Oracle
          </Box>{" "}
          {appTitle.replace('Oracle ', '').replace('OCI ', '')}
        </Typography>
      </motion.div>

      {/* Subtle hint text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={
          isExiting
            ? { opacity: 0, y: 20, scale: 0.9 }
            : isLoaded
            ? { opacity: 1, y: 0, scale: 1 }
            : { opacity: 0, y: 0, scale: 1 }
        }
        transition={{
          duration: isExiting ? 0.4 : 0.6,
          delay: isExiting ? 0.2 : 1.2,
          ease: "easeInOut",
        }}
        whileHover={{
          scale: 1.1,
          transition: { duration: 0.3, ease: "easeOut" },
        }}
        whileTap={{
          scale: 0.95,
          transition: { duration: 0.1 },
        }}
        style={{ marginTop: "32px" }}
      >
        <Typography
          variant="body2"
          sx={{
            fontSize: "0.8rem",
            color: "#888",
            fontWeight: 300,
            letterSpacing: "0.05em",
            textAlign: "center",
            fontFamily: "var(--font-oracle-sans), sans-serif",
            textTransform: "uppercase",
            userSelect: "none",
            cursor: "pointer",
            transition: "color 0.3s ease",
            "&:hover": {
              color: "#555",
            },
          }}
        >
          Click anywhere to continue
        </Typography>
      </motion.div>

      {/* Subtle background pattern */}
      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          opacity: 0.02,
          background: `
            radial-gradient(circle at 20% 50%, rgba(0,0,0,0.1) 0%, transparent 50%),
            radial-gradient(circle at 80% 20%, rgba(0,0,0,0.1) 0%, transparent 50%),
            radial-gradient(circle at 40% 80%, rgba(0,0,0,0.1) 0%, transparent 50%)
          `,
          pointerEvents: "none",
          zIndex: -1,
        }}
      />
    </Box>
  );
}
