"use client";

import { Chip, CircularProgress } from "@mui/material";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useEffect } from "react";

const CollapsibleChip = ({ 
  processingIcon, 
  completedIcon, 
  label, 
  isCompleted, 
  completionDelay = 1000 
}) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  useEffect(() => {
    if (isCompleted) {
      const timer = setTimeout(() => {
        setIsCollapsed(true);
      }, completionDelay);
      return () => clearTimeout(timer);
    }
  }, [isCompleted, completionDelay]);

  const chipStyles = {
    height: 'auto',
    fontSize: '0.85em !important',
    cursor: 'pointer',
    overflow: 'hidden',
    '& .MuiChip-icon': {
      fontSize: '0.85em !important'
    },
    '& .MuiChip-label': {
      fontSize: '0.85em !important',
      display: 'flex',
      alignItems: 'center',
      gap: 0.5,
      whiteSpace: 'nowrap'
    }
  };

  const currentIcon = isCompleted 
    ? completedIcon 
    : <CircularProgress size={16} />;

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      style={{ display: 'flex' }}
    >
      <motion.div
        animate={{
          width: isCollapsed ? 40 : 'auto',
          borderRadius: isCollapsed ? '50%' : '100px',
          padding: isCollapsed ? '0.4rem' : '0.25rem 0.75rem',
          minWidth: isCollapsed ? 40 : 'auto'
        }}
        transition={{ 
          duration: 0.6, 
          ease: [0.4, 0, 0.2, 1] // Dynamic Island easing
        }}
      >
        <Chip
          icon={currentIcon}
          label={
            <motion.span
              animate={{
                opacity: isCollapsed ? 0 : 1,
                width: isCollapsed ? 0 : 'auto'
              }}
              transition={{ 
                duration: 0.3, 
                ease: "easeInOut" 
              }}
              style={{ overflow: 'hidden' }}
            >
              {label}
            </motion.span>
          }
          color={isCompleted ? "success" : "default"}
          variant="outlined"
          sx={chipStyles}
        />
      </motion.div>
    </motion.div>
  );
};

export default CollapsibleChip;