import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { Box, Typography, useTheme } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

const FancyButton = ({
  children = "Click me",
  primaryColor,
  secondaryColor,
  type = "button",
  disabled = false,
  onClick,
  sx = {},
  pulseEnabled = false,
}) => {
  const theme = useTheme();
  const [isHovered, setIsHovered] = useState(false);
  const [isPressed, setIsPressed] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  const primary = primaryColor || theme.palette.primary.main;
  const secondary = secondaryColor || theme.palette.text.primary;

  useEffect(() => {
    if (!isHovered) {
      const timer = setTimeout(() => {
        setIsAnimating(false);
      }, 100); // Much faster reset time
      return () => clearTimeout(timer);
    } else {
      setIsAnimating(true);
    }
  }, [isHovered]);

  const buttonVariants = {
    idle: { scale: 1 },
    hover: {
      transition: { duration: 0.3, type: "spring", stiffness: 400 },
    },
    pressed: { scale: 0.98, transition: { duration: 0.1 } },
  };

  const textVariants = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      filter: "blur(4px)",
      transition: { duration: 0.12 },
    },
    visible: {
      opacity: 1,
      scale: 1,
      filter: "blur(0px)",
      transition: {
        duration: 0.15,
        ease: "easeOut",
      },
    },
  };

  const circleVariants = {
    idle: {
      width: 10,
      height: 10,
      borderRadius: "50%",
      x: "-50%",
      y: "-50%",
    },
    expanded: {
      width: "300%", // Use percentage instead of fixed size
      height: "300%", // Use percentage instead of fixed size
      borderRadius: "50%",
      x: "-50%",
      y: "-50%",
      transition: {
        duration: 0.2,
        type: "spring",
        stiffness: 300,
        damping: 15,
      },
    },
  };

  const iconVariants = {
    hidden: {
      scale: 0.8,
      opacity: 0,
      x: -5,
      filter: "blur(2px)",
    },
    visible: {
      scale: 1,
      opacity: 1,
      x: 0,
      filter: "blur(0px)",
      transition: {
        delay: 0.05,
        duration: 0.15,
        type: "spring",
        stiffness: 800,
        damping: 25,
      },
    },
  };

  return (
    <Box
      component={motion.button}
      type={type}
      disabled={disabled}
      onClick={(e) => {
        setIsPressed(true);
        setTimeout(() => setIsPressed(false), 200);
        onClick && onClick(e);
      }}
      onMouseEnter={() => !disabled && setIsHovered(true)}
      onMouseLeave={() => !disabled && setIsHovered(false)}
      variants={buttonVariants}
      initial="idle"
      animate={isPressed ? "pressed" : isHovered ? "hover" : "idle"}
      sx={{
        position: "relative",
        padding: "6px 10px 6px 14px", // Use padding to control size
        borderRadius: "24px",
        border: "none",
        overflow: "hidden",
        display: "inline-flex", // Use inline-flex to fit content
        alignItems: "center",
        justifyContent: "center",
        cursor: disabled ? "not-allowed" : "pointer",
        backgroundColor: (theme) => {
          if (disabled) {
            return theme.palette.mode === 'light' ? theme.palette.grey[200] : theme.palette.background.paper;
          }
          return theme.palette.mode === 'dark' ? theme.palette.background.paper : theme.palette.grey[100];
        },
        boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
        border: disabled ? "2px solid transparent" : (theme) => `2px dashed ${theme.palette.grey[400]}`,
        transition: "border-radius 0.15s ease, box-shadow 0.15s ease, border 0.15s ease", // Faster transitions
        "&:hover": !disabled ? {
          boxShadow: "0 6px 20px rgba(0,0,0,0.12)",
          borderRadius: isAnimating ? "28px" : "24px",
          border: "2px solid transparent",
        } : {},
        opacity: disabled ? 0.6 : 1,
        ...sx,
      }}
    >
      {/* Background circle that grows on hover with Dynamic Island-like animation */}
      <Box
        component={motion.div}
        initial="idle"
        animate={isHovered && !disabled ? "expanded" : "idle"}
        variants={circleVariants}
        sx={{
          position: "absolute",
          left: "16px",
          top: "50%",
          background: isHovered
            ? `radial-gradient(circle, ${primary} 50%, ${primary}cc 100%)`
            : secondary,
          zIndex: 1,
          filter: isHovered ? "blur(0.5px)" : "none",
          animation: pulseEnabled && !disabled && !isHovered
            ? "circlePulse 2s ease-in-out infinite"
            : "none",
          "@keyframes circlePulse": {
            "0%, 100%": { background: secondary },
            "50%": { background: primary }
          }
        }}
      />

      {/* Container to ensure text alignment is consistent */}
      <Box
        sx={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 2,
        }}
      >
        <AnimatePresence mode="wait">
          {!isHovered || disabled ? (
            <Typography
              key="idle-text"
              component={motion.div}
              variants={textVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              sx={{
                fontWeight: 600,
                fontSize: 14,
                color: (theme) => theme.palette.text.primary,
                zIndex: 2,
                textAlign: "center",
                letterSpacing: "0.02em",
                transformOrigin: "center",
                ml: 2.5,
              }}
            >
              {children}
            </Typography>
          ) : (
            <Box
              key="hover-text"
              component={motion.div}
              variants={textVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 0.5,
                zIndex: 2,
                transformOrigin: "center",
              }}
            >
              <Typography
                component={motion.span}
                sx={{
                  fontWeight: 600,
                  fontSize: 14,
                  color: (theme) => theme.palette.common.white,
                  background:
                    "linear-gradient(45deg, white 30%, rgba(255,255,255,0.8) 90%)",
                  backgroundClip: "text",
                  display: "inline-block",
                  letterSpacing: "0.02em",
                }}
                initial={{
                  textShadow: "0 0 0 rgba(255,255,255,0)",
                }}
                animate={{
                  textShadow: "0 0 5px rgba(255,255,255,0.2)",
                }}
                transition={{
                  duration: 0.8,
                  repeat: Infinity,
                  repeatType: "reverse",
                }}
              >
                {children}
              </Typography>
              <Box
                component={motion.div}
                variants={iconVariants}
                initial="hidden"
                animate="visible"
              >
                <ArrowForwardIcon
                  sx={{ fontSize: 16, color: (theme) => theme.palette.common.white, mt: "1px" }}
                />
              </Box>
            </Box>
          )}
        </AnimatePresence>
      </Box>

      {/* Dynamic Island-like morphing light effects - FASTER */}
      {isHovered && !disabled && (
        <>
          <Box
            component={motion.div}
            initial={{ opacity: 0 }}
            animate={{
              opacity: 0.12,
              transition: {
                duration: 0.2,
                repeat: Infinity,
                repeatType: "reverse",
                repeatDelay: 0.7,
              },
            }}
            sx={{
              position: "absolute",
              top: "10%",
              left: "200px",
              width: "30%",
              height: "30%",
              background:
                "radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 70%)",
              zIndex: 3,
              pointerEvents: "none",
              filter: "blur(1px)",
            }}
          />
          <Box
            component={motion.div}
            initial={{ opacity: 0 }}
            animate={{
              opacity: [0, 0.07, 0],
              scale: [1, 1.1, 1],
              transition: {
                duration: 1.2, // Keep this animation subtle but noticeable
                repeat: Infinity,
                ease: "easeInOut",
              },
            }}
            sx={{
              position: "absolute",
              top: "50%",
              left: "50%",
              width: "80%",
              height: "70%",
              transform: "translate(-50%, -50%)",
              background:
                "radial-gradient(ellipse, rgba(255,255,255,0.3) 0%, rgba(255,255,255,0) 70%)",
              zIndex: 3,
              pointerEvents: "none",
              borderRadius: "50%",
              filter: "blur(2px)",
            }}
          />
        </>
      )}
    </Box>
  );
};

export default FancyButton;
