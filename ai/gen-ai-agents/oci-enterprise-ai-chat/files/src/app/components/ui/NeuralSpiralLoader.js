"use client";

import { useState, useEffect } from "react";
import { Box } from "@mui/material";
import { motion } from "framer-motion";

const redColor = "#C74634";

export default function NeuralSpiralLoader({ size = "medium", delay = 400, alwaysShow = false, color = redColor }) {
  const [show, setShow] = useState(alwaysShow);

  useEffect(() => {
    if (alwaysShow) return;
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay, alwaysShow]);

  // Size presets
  const sizes = {
    small: { scale: 0.7 },
    medium: { scale: 1 },
    large: { scale: 1.3 },
  };

  const s = sizes[size] || sizes.medium;

  const keyframes = `
    @keyframes cross-container-rotate-loader {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes breathe-cross-loader {
      0%, 100% { transform: scale(0.4); opacity: 0.2; }
      50% { transform: scale(1); opacity: 1; }
    }
  `;

  // Cross pattern: 5 dots in plus shape
  const positions = [
    { x: 1, y: 0 },  // top
    { x: 0, y: 1 },  // left
    { x: 1, y: 1 },  // center
    { x: 2, y: 1 },  // right
    { x: 1, y: 2 },  // bottom
  ];

  if (!show) return null;

  return (
    <>
      <style>{keyframes}</style>
      <Box sx={{
        position: 'relative',
        width: 44 * s.scale,
        height: 44 * s.scale,
        animation: 'cross-container-rotate-loader 4s linear infinite',
      }}>
        {positions.map((pos, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              delay: i * 0.08,
              duration: 0.3,
              ease: "easeOut"
            }}
            style={{
              position: 'absolute',
              left: (pos.x * 14 + 1) * s.scale,
              top: (pos.y * 14 + 1) * s.scale,
              width: 12 * s.scale,
              height: 12 * s.scale,
              borderRadius: '50%',
              backgroundColor: color,
              animation: 'breathe-cross-loader 1.6s ease-in-out infinite',
              animationDelay: `${i * 0.12}s`,
            }}
          />
        ))}
      </Box>
    </>
  );
}
