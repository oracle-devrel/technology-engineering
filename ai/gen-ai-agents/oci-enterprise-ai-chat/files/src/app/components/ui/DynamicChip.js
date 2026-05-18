"use client";

import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";
import { CircularProgress, Typography, useTheme } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

export default function DynamicChip({
  icon: Icon,
  label,
  status = "success",
  content,
  onExpand,
  isActive,
  startDelay = 0,
}) {
  const theme = useTheme();
  const [isVisible, setIsVisible] = useState(true); // Start visible immediately
  const [isLoading, setIsLoading] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const [showExpandIcon, setShowExpandIcon] = useState(false);

  const getStatusColor = () => {
    switch (status) {
      case "error":
        return theme.palette.error?.main || "#f44336";
      case "warning":
        return theme.palette.warning?.main || "#ff9800";
      case "info":
        return theme.palette.info?.main || "#2196f3";
      case "purple":
        return "#9c27b0";
      case "success":
      default:
        return theme.palette.success?.main || theme.palette.secondary.main;
    }
  };

  const statusColor = getStatusColor();

  useEffect(() => {
    // Se expande automáticamente
    setTimeout(() => setShowExpandIcon(true), startDelay + 500);

    // Termina de cargar
    setTimeout(() => setIsLoading(false), startDelay + 1700);

    // Se contrae automáticamente
    setTimeout(() => setShowExpandIcon(false), startDelay + 2200);
  }, [startDelay]);

  const handleClick = () => {
    if (isVisible) {
      if (isActive) {
        onExpand(null);
      } else {
        onExpand({
          label,
          status,
          content: content || "No additional information available",
        });
      }
    }
  };

  // Mostrar texto si está en hover O si está mostrando el ícono de expandir O si está activo
  const shouldShowText = isHovered || showExpandIcon || isActive;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ scale: 0, opacity: 0 }}
          animate={{
            scale: 1,
            opacity: 1,
          }}
          exit={{ scale: 0, opacity: 0 }}
          whileHover={{ scale: 1.05 }}
          transition={{
            scale: { type: "spring", damping: 20, stiffness: 300 },
          }}
          onClick={handleClick}
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
          style={{
            height: 40,
            minWidth: 40,
            backgroundColor: isActive ? `${statusColor}15` : "transparent",
            border: `1px solid ${!isLoading ? statusColor : "#999"}`,
            borderRadius: 20,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "flex-start",
            paddingLeft: 12,
            paddingRight: shouldShowText ? 16 : 12,
            overflow: "hidden",
            cursor: "pointer",
            boxShadow: isHovered ? "0 4px 12px rgba(0, 0, 0, 0.15)" : "none",
          }}
        >
          {/* Ícono principal */}
          <motion.div
            style={{
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {isLoading ? (
              <CircularProgress size={16} sx={{ color: "#666" }} />
            ) : (
              <Icon size={16} color={statusColor} />
            )}
          </motion.div>

          {/* Contenedor del texto y flecha con animación suave */}
          <motion.div
            animate={{
              width: shouldShowText ? "auto" : 0,
              opacity: shouldShowText ? 1 : 0,
              marginLeft: shouldShowText ? 8 : 0,
            }}
            transition={{
              duration: 0.3,
              ease: "easeInOut",
            }}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              overflow: "hidden",
              whiteSpace: "nowrap",
            }}
          >
            <Typography
              sx={{
                color: !isLoading ? statusColor : "#000",
                fontSize: "16px",
                fontWeight: isActive ? 500 : 300,
              }}
            >
              {label}
            </Typography>

            {/* Ícono de expandir solo cuando showExpandIcon es true */}
            <AnimatePresence>
              {showExpandIcon && (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1, rotate: isActive ? 180 : 0 }}
                  exit={{ scale: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ExpandMoreIcon
                    sx={{
                      fontSize: 18,
                      color: !isLoading ? statusColor : "#666",
                    }}
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
