import { Box } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

export default function BlinkingEye({
  isActive = false,
  blinkIntervals = [2500, 300, 15000, 20000, 8000, 25000, 12000, 30000, 18000],
  lookDirection = "center",
  initialOpenDelay = 900,
  followMouse = false,
  size = 1,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasOpenedOnce, setHasOpenedOnce] = useState(false);
  const [currentIntervalIndex, setCurrentIntervalIndex] = useState(0);
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 });
  const svgRef = useRef(null);

  const handleMouseMove = useCallback((e) => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    const dx = e.clientX - centerX;
    const dy = e.clientY - centerY;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const maxOffset = 12;
    const factor = Math.min(dist / 200, 1) * maxOffset;
    setMouseOffset({
      x: (dx / (dist || 1)) * factor,
      y: (dy / (dist || 1)) * factor,
    });
  }, []);

  useEffect(() => {
    if (followMouse) {
      window.addEventListener("mousemove", handleMouseMove);
      return () => window.removeEventListener("mousemove", handleMouseMove);
    }
  }, [followMouse, handleMouseMove]);

  const getPupilPosition = () => {
    if (followMouse) {
      return { x: 60 + mouseOffset.x, y: 40 + mouseOffset.y };
    }
    switch (lookDirection) {
      case "up":
        return { x: 60, y: 32 };
      case "down":
        return { x: 60, y: 45 };
      case "left":
        return { x: 48, y: 40 };
      case "right":
        return { x: 72, y: 40 };
      default:
        return { x: 60, y: 40 };
    }
  };

  const getIrisTransform = () => {
    if (followMouse) return "scale(1, 1)";
    switch (lookDirection) {
      case "down":
        return "scale(1, 0.92)";
      case "up":
        return "scale(1, 0.96)";
      default:
        return "scale(1, 1)";
    }
  };

  const getReflectionPosition = () => {
    const pupil = getPupilPosition();
    if (followMouse) {
      return { x: pupil.x + 4, y: pupil.y - 4 };
    }
    switch (lookDirection) {
      case "down":
        return { x: pupil.x + 3, y: pupil.y - 6 };
      case "up":
        return { x: pupil.x + 4, y: pupil.y - 2 };
      default:
        return { x: pupil.x + 4, y: pupil.y - 4 };
    }
  };

  const getReflectionOpacity = () => {
    if (followMouse) return 0.8;
    switch (lookDirection) {
      case "down":
        return 0.6;
      case "up":
        return 0.9;
      default:
        return 0.8;
    }
  };

  // useEffect 1: Solo para la apertura inicial
  useEffect(() => {
    if (!isActive && !hasOpenedOnce) {
      const timeout = setTimeout(() => {
        setIsOpen(true);
        setHasOpenedOnce(true);
      }, initialOpenDelay);

      return () => clearTimeout(timeout);
    }
  }, [isActive, hasOpenedOnce, initialOpenDelay]);

  // useEffect 2: Solo para el ciclo de parpadeo
  useEffect(() => {
    if (!isActive && hasOpenedOnce) {
      // Esperar el intervalo actual antes de parpadear
      const blinkTimeout = setTimeout(() => {
        // Cerrar el ojo
        setIsOpen(false);

        // Reabrir después de 150ms
        setTimeout(() => {
          setIsOpen(true);
          // Avanzar al siguiente intervalo
          setCurrentIntervalIndex((prev) => (prev + 1) % blinkIntervals.length);
        }, 150);
      }, blinkIntervals[currentIntervalIndex]);

      return () => clearTimeout(blinkTimeout);
    }
  }, [isActive, hasOpenedOnce, currentIntervalIndex, blinkIntervals]);

  const pupilPos = getPupilPosition();
  const reflectionPos = getReflectionPosition();
  const irisTransform = getIrisTransform();
  const reflectionOpacity = getReflectionOpacity();

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Box sx={{ position: "relative" }}>
        <svg
          ref={svgRef}
          width={120 * size}
          height={80 * size}
          viewBox="0 0 120 80"
          style={{ transition: "all 150ms ease-in-out" }}
        >
          <defs>
            <clipPath id="eyeClip">
              <motion.path
                d={
                  isOpen
                    ? "M 20 40 Q 35 20, 60 20 T 100 40 Q 85 60, 60 60 T 20 40"
                    : "M 20 40 Q 35 40, 60 40 T 100 40 Q 85 40, 60 40 T 20 40"
                }
                animate={{
                  d: isOpen
                    ? "M 20 40 Q 35 20, 60 20 T 100 40 Q 85 60, 60 60 T 20 40"
                    : "M 20 40 Q 35 40, 60 40 T 100 40 Q 85 40, 60 40 T 20 40",
                }}
                transition={{
                  duration: 0.15,
                  ease: "easeInOut",
                }}
              />
            </clipPath>
          </defs>

          <motion.path
            d={
              isOpen
                ? "M 20 40 Q 35 20, 60 20 T 100 40 Q 85 60, 60 60 T 20 40"
                : "M 20 40 Q 35 40, 60 40 T 100 40 Q 85 40, 60 40 T 20 40"
            }
            fill="none"
            stroke="#1a1a1a"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeDasharray={!hasOpenedOnce ? 180 : 0}
            strokeDashoffset={!hasOpenedOnce ? 180 : 0}
            animate={{
              d: isOpen
                ? "M 20 40 Q 35 20, 60 20 T 100 40 Q 85 60, 60 60 T 20 40"
                : "M 20 40 Q 35 40, 60 40 T 100 40 Q 85 40, 60 40 T 20 40",
              strokeDashoffset: !hasOpenedOnce ? 0 : 0,
            }}
            transition={{
              d: {
                duration: 0.15,
                ease: "easeInOut",
                delay: isOpen ? 0.05 : 0,
              },
              strokeDashoffset: {
                duration: 1.5,
                ease: "easeInOut",
                delay: 0,
              },
            }}
          />

          <g clipPath="url(#eyeClip)">
            <AnimatePresence>
              {isOpen && (
                <motion.g
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <circle
                    cx="60"
                    cy="40"
                    r="18"
                    fill="none"
                    stroke="#1a1a1a"
                    strokeWidth="2.5"
                  />

                  <g
                    transform={`translate(${pupilPos.x}, ${pupilPos.y}) ${isActive ? 'scale(1, 1)' : irisTransform} translate(-${pupilPos.x}, -${pupilPos.y})`}
                  >
                    <motion.circle
                      cx={pupilPos.x}
                      cy={pupilPos.y}
                      r="10"
                      fill="#1a1a1a"
                      animate={{
                        cx: isActive ? 60 : pupilPos.x,
                        cy: isActive ? 40 : pupilPos.y,
                        fill: isActive ? "#1a1a1a" : "#1a1a1a",
                        r: isActive ? [10, 11, 9, 10] : 10,
                      }}
                      transition={{
                        cx: {
                          type: "spring",
                          stiffness: isActive ? 200 : 300,
                          damping: isActive ? 25 : 30,
                          duration: isActive ? 0.8 : 0.6,
                        },
                        cy: {
                          type: "spring",
                          stiffness: isActive ? 200 : 300,
                          damping: isActive ? 25 : 30,
                          duration: isActive ? 0.8 : 0.6,
                        },
                        fill: {
                          duration: 0.4,
                          ease: "easeInOut",
                        },
                        r: {
                          duration: isActive ? 2.5 : 0.3,
                          ease: "easeInOut",
                          repeat: isActive ? Infinity : 0,
                        },
                      }}
                    />
                  </g>

                  <motion.circle
                    cx={reflectionPos.x}
                    cy={reflectionPos.y}
                    r="2.5"
                    fill="#fff"
                    opacity={reflectionOpacity}
                    animate={{
                      cx: isActive ? 64 : reflectionPos.x,
                      cy: isActive ? 36 : reflectionPos.y,
                      opacity: isActive ? [0.3, 1, 0.3] : reflectionOpacity,
                    }}
                    transition={{
                      cx: {
                        type: "spring",
                        stiffness: isActive ? 200 : 300,
                        damping: isActive ? 25 : 30,
                        duration: isActive ? 0.8 : 0.6,
                      },
                      cy: {
                        type: "spring",
                        stiffness: isActive ? 200 : 300,
                        damping: isActive ? 25 : 30,
                        duration: isActive ? 0.8 : 0.6,
                      },
                      opacity: {
                        duration: isActive ? 1.5 : 0.4,
                        ease: "easeInOut",
                        repeat: isActive ? Infinity : 0,
                      },
                    }}
                  />
                </motion.g>
              )}
            </AnimatePresence>
          </g>
        </svg>
      </Box>
    </Box>
  );
}
