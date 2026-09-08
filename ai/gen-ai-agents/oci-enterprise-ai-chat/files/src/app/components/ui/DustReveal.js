"use client";

import { Typography } from '@mui/material';
import { motion } from 'framer-motion';
import { Fragment, useState, useEffect } from 'react';

const MAX_ANIMATED_LENGTH = 300; // Don't animate texts longer than this

const DustReveal = ({ text, delay = 0, duration = 0.8, className = "", sx = {}, style = {} }) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(true);
    }, delay * 1000);

    return () => clearTimeout(timer);
  }, [delay]);

  // For long texts, just render as plain text to avoid performance issues
  if (text.length > MAX_ANIMATED_LENGTH) {
    return (
      <Typography className={className} sx={sx} style={style}>
        {text}
      </Typography>
    );
  }

  // Split preserving whitespace as separate tokens so the browser keeps real
  // line-break opportunities between words (otherwise motion.span transforms
  // turn each token into an atomic inline-block and the text never wraps).
  const tokens = text.split(/(\s+)/).filter(t => t.length > 0);
  const animatedCount = tokens.filter(t => !/^\s+$/.test(t)).length || 1;
  const staggerDelay = (duration * 0.1) / animatedCount;

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: staggerDelay,
        delayChildren: 0.1
      }
    }
  };

  const wordVariants = {
    hidden: {
      opacity: 0,
      y: 20,
      scale: 0.8,
      filter: "blur(4px)",
      rotateX: -90
    },
    visible: {
      opacity: 1,
      y: 0,
      scale: 1,
      filter: "blur(0px)",
      rotateX: 0,
      transition: {
        type: "spring",
        damping: 15,
        stiffness: 200,
        mass: 0.8,
        duration: duration * 0.6
      }
    }
  };

  return (
    <Typography
      component={motion.div}
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate={isVisible ? "visible" : "hidden"}
      sx={sx}
      style={{ perspective: "200px", ...style }}
    >
      {tokens.map((token, index) => {
        if (/^\s+$/.test(token)) {
          return <Fragment key={index}>{token}</Fragment>;
        }
        return (
          <motion.span
            key={index}
            variants={wordVariants}
            style={{
              display: "inline-block",
              transformOrigin: "50% 100%"
            }}
          >
            {token}
          </motion.span>
        );
      })}
    </Typography>
  );
};

export default DustReveal;