"use client";

import { useState, useEffect } from "react";
import { Box } from "@mui/material";
import { motion } from "framer-motion";

const animationSpeed = 3000; // Two-phase color cycle

const grayColor = "#d0d0d0";

function getOffDotColor() {
  if (typeof window === "undefined") return "#ffffff";
  try {
    const settings = JSON.parse(localStorage.getItem("uiSettings") || "{}");
    return settings.darkMode ? "#3a3a3a" : "#ffffff";
  } catch { return "#ffffff"; }
}

function lightenColor(hex, amount = 0.4) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  const lr = Math.round(r + (255 - r) * amount);
  const lg = Math.round(g + (255 - g) * amount);
  const lb = Math.round(b + (255 - b) * amount);
  return `#${lr.toString(16).padStart(2, '0')}${lg.toString(16).padStart(2, '0')}${lb.toString(16).padStart(2, '0')}`;
}

function getAccentColor() {
  try {
    const settings = JSON.parse(localStorage.getItem("uiSettings") || "{}");
    return settings.accentColor || "#C74634";
  } catch { return "#C74634"; }
}

export default function DotMatrixLoader({ size = "medium", delay = 400, alwaysShow = false, color }) {
  const accentColor = color || getAccentColor();
  const lightAccentColor = lightenColor(accentColor, 0.4);
  const offDotColor = getOffDotColor();
  const [show, setShow] = useState(alwaysShow);

  useEffect(() => {
    if (alwaysShow) return;
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay, alwaysShow]);

  // Size presets
  const sizes = {
    small: { dot: 6, radius: 1.5, gap: 1 },
    medium: { dot: 8, radius: 2, gap: 1.5 },
    large: { dot: 12, radius: 3, gap: 2 },
  };

  const s = sizes[size] || sizes.medium;

  // Grid positions (1-indexed):
  // 1 2 3
  // 4 5 6
  // 7 8 9
  //
  // Animation: Clockwise rotation on cross (2→6→8→4), center (5) always on
  // Corners (1,3,7,9) stay off
  const keyframes = `
    @keyframes dot-1-spinner {
      0%, 100% {
        background-color: ${offDotColor};
      }
    }

    @keyframes dot-2-spinner {
      0% { background-color: ${accentColor}; }
      12% { background-color: ${lightAccentColor}; }
      24%, 34%, 44% { background-color: ${offDotColor}; }
      50% { background-color: ${grayColor}; }
      74%, 84%, 94% { background-color: ${offDotColor}; }
      97% { background-color: ${lightAccentColor}; }
      100% { background-color: ${accentColor}; }
    }

    @keyframes dot-3-spinner {
      0%, 100% {
        background-color: ${offDotColor};
      }
    }

    @keyframes dot-4-spinner {
      0%, 10%, 20% { background-color: ${offDotColor}; }
      23% { background-color: ${lightAccentColor}; }
      26% { background-color: ${accentColor}; }
      32% { background-color: ${lightAccentColor}; }
      45%, 50%, 60%, 70% { background-color: ${offDotColor}; }
      76% { background-color: ${grayColor}; }
      95%, 100% { background-color: ${offDotColor}; }
    }

    @keyframes dot-5-spinner {
      0% { background-color: ${accentColor}; }
      12% { background-color: ${lightAccentColor}; }
      25% { background-color: ${accentColor}; }
      37% { background-color: ${lightAccentColor}; }
      50%, 75% { background-color: ${grayColor}; }
      88% { background-color: ${lightAccentColor}; }
      100% { background-color: ${accentColor}; }
    }

    @keyframes dot-6-spinner {
      0% { background-color: ${offDotColor}; }
      3% { background-color: ${lightAccentColor}; }
      6% { background-color: ${accentColor}; }
      15% { background-color: ${lightAccentColor}; }
      30%, 40%, 50% { background-color: ${offDotColor}; }
      56% { background-color: ${grayColor}; }
      80%, 90%, 100% { background-color: ${offDotColor}; }
    }

    @keyframes dot-7-spinner {
      0%, 100% {
        background-color: ${offDotColor};
      }
    }

    @keyframes dot-8-spinner {
      0%, 10% { background-color: ${offDotColor}; }
      13% { background-color: ${lightAccentColor}; }
      16% { background-color: ${accentColor}; }
      25% { background-color: ${lightAccentColor}; }
      40%, 50%, 60% { background-color: ${offDotColor}; }
      66% { background-color: ${grayColor}; }
      90%, 100% { background-color: ${offDotColor}; }
    }

    @keyframes dot-9-spinner {
      0%, 100% {
        background-color: ${offDotColor};
      }
    }
  `;

  if (!show) return null;

  return (
    <>
      <style>{keyframes}</style>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.25, ease: "easeOut" }}
      >
        <Box
          sx={{
            display: "grid",
            gridTemplateColumns: `repeat(3, ${s.dot}px)`,
            gridTemplateRows: `repeat(3, ${s.dot}px)`,
            gap: `${s.gap}px`,
            width: "fit-content",
            "& > div": {
              width: s.dot,
              height: s.dot,
              backgroundColor: offDotColor,
              borderRadius: `${s.radius}px`,
              animationDuration: `${animationSpeed}ms`,
              animationIterationCount: "infinite",
              animationTimingFunction: "ease-in-out",
            },
            "& > div:nth-of-type(1)": { animationName: "dot-1-spinner" },
            "& > div:nth-of-type(2)": { animationName: "dot-2-spinner" },
            "& > div:nth-of-type(3)": { animationName: "dot-3-spinner" },
            "& > div:nth-of-type(4)": { animationName: "dot-4-spinner" },
            "& > div:nth-of-type(5)": { animationName: "dot-5-spinner" },
            "& > div:nth-of-type(6)": { animationName: "dot-6-spinner" },
            "& > div:nth-of-type(7)": { animationName: "dot-7-spinner" },
            "& > div:nth-of-type(8)": { animationName: "dot-8-spinner" },
            "& > div:nth-of-type(9)": { animationName: "dot-9-spinner" },
          }}
        >
          {Array.from({ length: 9 }, (_, i) => (
            <div key={i} />
          ))}
        </Box>
      </motion.div>
    </>
  );
}
