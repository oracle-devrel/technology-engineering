"use client";

import CheckCircleIcon from "@mui/icons-material/CheckCircleOutline";
import ErrorIcon from "@mui/icons-material/ErrorOutline";
import InfoIcon from "@mui/icons-material/InfoOutlined";
import LightbulbIcon from "@mui/icons-material/LightbulbOutlined";
import NewReleasesIcon from "@mui/icons-material/NewReleasesOutlined";
import WarningIcon from "@mui/icons-material/WarningAmberOutlined";
import { Box, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";

// Pill component inspired by Apple's Dynamic Island design with expansion on hover
const StatusPill = ({ label, count, color, icon, delay }) => {
  if (count === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay: delay * 0.1,
        type: "spring",
        stiffness: 120,
      }}
    >
      <Box
        sx={{
          position: "relative",
          display: "flex",
          cursor: "pointer",
          alignItems: "center",
          borderRadius: "18px",
          height: "28px",
          py: 0.5,
          px: 1,
          mr: 1,
          mb: 0.75,
          backgroundColor: "rgba(250, 250, 253, 0.8)",
          backdropFilter: "blur(20px)",
          boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
          border: `1px solid rgba(0,0,0,0.06)`,
          overflow: "hidden",
          userSelect: "none",
          transition: "all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)",
          "&:hover": {
            transform: "translateY(-1px)",
            boxShadow: "0 3px 8px rgba(0,0,0,0.08)",
            width: "auto",
            px: 1.25,
            "& .label-text": {
              opacity: 1,
              maxWidth: "120px",
              marginLeft: "6px",
            },
          },
        }}
      >
        <Box
          sx={{
            color: color,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            "& .MuiSvgIcon-root": {
              fontSize: "0.95rem",
            },
          }}
        >
          {icon}
        </Box>

        <Typography
          variant="caption"
          sx={{
            fontWeight: 600,
            fontSize: "0.75rem",
            marginLeft: "4px",
            color: "rgba(0,0,0,0.75)",
          }}
        >
          {count}
        </Typography>

        <Typography
          variant="caption"
          className="label-text"
          sx={{
            fontWeight: 500,
            fontSize: "0.7rem",
            letterSpacing: "0.01em",
            color: "rgba(0,0,0,0.75)",
            opacity: 0,
            maxWidth: 0,
            overflow: "hidden",
            whiteSpace: "nowrap",
            transition: "all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
        >
          {label}
        </Typography>
      </Box>
    </motion.div>
  );
};

// Success badge component with Apple-like animation and Dynamic Island expansion behavior
const SuccessBadge = () => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.6, type: "spring", stiffness: 120 }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          borderRadius: "18px",
          height: "28px",
          py: 0.5,
          px: 1,
          mr: 1,
          mb: 0.75,
          background: "linear-gradient(to right, #32d74b, #34c759)",
          boxShadow: "0 2px 8px rgba(52, 199, 89, 0.25)",
          overflow: "hidden",
          transition: "all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)",
          "&:hover": {
            px: 1.5,
            transform: "translateY(-1px)",
            boxShadow: "0 3px 10px rgba(52, 199, 89, 0.3)",
            "& .success-text": {
              opacity: 1,
              maxWidth: "120px",
              marginLeft: "6px",
            },
          },
        }}
      >
        <Box
          sx={{
            color: "white",
            display: "flex",
            alignItems: "center",
            "& .MuiSvgIcon-root": {
              fontSize: "0.9rem",
            },
          }}
        >
          <CheckCircleIcon />
        </Box>

        <Typography
          variant="caption"
          sx={{
            fontWeight: 600,
            fontSize: "0.75rem",
            marginLeft: "4px",
            color: "white",
          }}
        >
          1
        </Typography>

        <Typography
          variant="caption"
          className="success-text"
          sx={{
            fontWeight: 500,
            letterSpacing: "0.01em",
            fontSize: "0.7rem",
            color: "white",
            opacity: 0,
            maxWidth: 0,
            overflow: "hidden",
            whiteSpace: "nowrap",
            transition: "all 0.35s cubic-bezier(0.34, 1.56, 0.64, 1)",
          }}
        >
          All Checks Passed
        </Typography>
      </Box>
    </motion.div>
  );
};

const ValidationStats = ({
  issuesCount = 0,
  recommendationsCount = 0,
  type = "default",
  security = null,
  isLoading = false,
}) => {
  const [showStats, setShowStats] = useState(false);

  useEffect(() => {
    if (!isLoading) {
      const timer = setTimeout(() => {
        setShowStats(true);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  if (isLoading) return null;

  const isSecuritySection = type === "Security" || security !== null;
  const allChecksPassed =
    (!isSecuritySection && issuesCount === 0 && recommendationsCount === 0) ||
    (isSecuritySection &&
      security &&
      security.criticalIssues.length === 0 &&
      security.highIssues.length === 0 &&
      security.mediumIssues.length === 0 &&
      security.lowIssues.length === 0);

  // Apple color palette
  const colors = {
    critical: (theme) => theme.palette.error.main,
    high: (theme) => theme.palette.warning.main,
    medium: (theme) => theme.palette.warning.light,
    low: (theme) => theme.palette.info.dark,
    issues: (theme) => theme.palette.error.main,
    recommendations: (theme) => theme.palette.warning.main,
    success: (theme) => theme.palette.success.main,
  };

  return (
    <AnimatePresence>
      {showStats && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Box
            sx={{
              display: "flex",
              flexWrap: "wrap",
              alignItems: "center",
              mt: 1.5,
              px: 0.5,
            }}
          >
            {allChecksPassed ? (
              <SuccessBadge />
            ) : (
              <>
                {isSecuritySection && security ? (
                  <>
                    <StatusPill
                      label="Critical"
                      count={security.criticalIssues.length}
                      color={colors.critical}
                      icon={<NewReleasesIcon />}
                      delay={0}
                    />
                    <StatusPill
                      label="High"
                      count={security.highIssues.length}
                      color={colors.high}
                      icon={<ErrorIcon />}
                      delay={1}
                    />
                    <StatusPill
                      label="Medium"
                      count={security.mediumIssues.length}
                      color={colors.medium}
                      icon={<WarningIcon />}
                      delay={2}
                    />
                    <StatusPill
                      label="Low"
                      count={security.lowIssues.length}
                      color={colors.low}
                      icon={<InfoIcon />}
                      delay={3}
                    />
                  </>
                ) : (
                  <>
                    <StatusPill
                      label="Issues"
                      count={issuesCount}
                      color={colors.issues}
                      icon={<ErrorIcon />}
                      delay={0}
                    />
                    <StatusPill
                      label="Recommendations"
                      count={recommendationsCount}
                      color={colors.recommendations}
                      icon={<LightbulbIcon />}
                      delay={1}
                    />
                  </>
                )}
              </>
            )}
          </Box>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default ValidationStats;
