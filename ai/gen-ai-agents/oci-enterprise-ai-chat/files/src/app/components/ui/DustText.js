"use client";
import { Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const DustText = ({
  text,
  duration = 1.5,
  delay = 0.05,
  blur = 6,
  distance = -25,
  sx = {},
}) => {
  const lines = text.split("\n");
  const scrollRef = useRef(null);
  const [showTopGradient, setShowTopGradient] = useState(false);
  const [showBottomGradient, setShowBottomGradient] = useState(false);

  useEffect(() => {
    const checkScroll = () => {
      if (!scrollRef.current) return;

      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;

      // Mostrar gradiente superior si no estamos arriba del todo
      setShowTopGradient(scrollTop > 5);

      // Mostrar gradiente inferior si no estamos abajo del todo
      setShowBottomGradient(scrollTop < scrollHeight - clientHeight - 5);
    };

    // Check inicial
    checkScroll();

    // Listener para scroll
    const element = scrollRef.current;
    element?.addEventListener("scroll", checkScroll);

    return () => {
      element?.removeEventListener("scroll", checkScroll);
    };
  }, [text]); // Re-check cuando cambie el texto

  return (
    <div style={{ position: "relative" }}>
      {/* Gradiente superior */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: "1.5rem",
          background: "linear-gradient(to bottom, white 0%, transparent 100%)",
          pointerEvents: "none",
          zIndex: 1,
          opacity: showTopGradient ? 1 : 0,
          transition: "opacity 0.3s ease",
        }}
      />

      {/* Contenedor con scroll */}
      <div
        ref={scrollRef}
        style={{
          maxHeight: "6.4rem",
          overflowY: "auto",
          overflowX: "hidden",
          position: "relative",
        }}
      >
        {lines.map((line, index) => (
          <motion.div
            key={index}
            initial={{
              opacity: 0,
              x: distance,
              filter: `blur(${blur}px)`,
            }}
            animate={{
              opacity: 1,
              x: 0,
              filter: "blur(0px)",
            }}
            transition={{
              duration,
              delay: delay,
              ease: "easeOut",
            }}
          >
            <Typography component="span" sx={sx}>
              {line}
            </Typography>
          </motion.div>
        ))}
      </div>

      {/* Gradiente inferior */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: "1.5rem",
          background: "linear-gradient(to top, white 0%, transparent 100%)",
          pointerEvents: "none",
          zIndex: 1,
          opacity: showBottomGradient ? 1 : 0,
          transition: "opacity 0.3s ease",
        }}
      />
    </div>
  );
};

export default DustText;