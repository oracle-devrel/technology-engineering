"use client";

import { keyframes } from "@emotion/react";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import {
  Box,
  CircularProgress,
  Collapse,
  IconButton,
  Stack,
  Typography,
  styled,
} from "@mui/material";
import React, { useState } from "react";
import ValidationStats from "./ValidationStats";

const breathe = keyframes`
  0% { box-shadow: 5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff, inset 0 0 0 #d1d1d1, inset 0 0 0 #ffffff; }
  50% { box-shadow: 3px 3px 6px #d1d1d1, -3px -3px 6px #ffffff, inset 1px 1px 3px #d1d1d1, inset -1px -1px 3px #ffffff; }
  100% { box-shadow: 5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff, inset 0 0 0 #d1d1d1, inset 0 0 0 #ffffff; }
`;

const appear = keyframes`
  from { transform: scale(0.5); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
`;

const NeumorphicIcon = styled(Box)({
  display: "flex",
  justifyContent: "center",
  alignItems: "center",
  width: 36,
  height: 36,
  borderRadius: 18,
  background: "linear-gradient(145deg, #e6e6e6, #ffffff)",
  boxShadow:
    "5px 5px 10px #d1d1d1, -5px -5px 10px #ffffff, inset 0 0 0 #d1d1d1, inset 0 0 0 #ffffff",
  position: "relative",
  overflow: "visible",
  transition: "all 0.3s ease",
  "&:hover": {
    boxShadow:
      "3px 3px 6px #d1d1d1, -3px -3px 6px #ffffff, inset 2px 2px 5px #d1d1d1, inset -2px -2px 5px #ffffff",
    transform: "translateY(2px)",
  },
  "&::before": {
    content: '""',
    position: "absolute",
    inset: 0,
    borderRadius: 18,
    background:
      "linear-gradient(145deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 100%)",
    opacity: 0.6,
    zIndex: 1,
  },
  animation: `${breathe} 4s infinite ease-in-out`,
});

const IconWrapper = styled(Box)(({ bg, shadow }) => ({
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 28,
  height: 28,
  borderRadius: 14,
  background: bg,
  boxShadow: shadow,
  animation: `${appear} 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275)`,
}));

const ExpandButton = styled(IconButton)({
  padding: 4,
  transition: "transform 0.3s ease",
});

const ValidationStatus = ({
  issuesCount,
  recommendationsCount,
  isLoading,
  type,
  qualityScore = null,
}) => {
  if (isLoading)
    return (
      <CircularProgress
        size={20}
        thickness={6}
        sx={{
          color: "grey",
          mr: 0.5,
          "& circle": {
            strokeLinecap: "round",
          },
        }}
      />
    );

  if (qualityScore !== null) {
    const getScoreColor = (score) => {
      if (score >= 8) return (theme) => theme.palette.success.main;
      if (score >= 5) return (theme) => theme.palette.primary.main;
      if (score >= 3) return (theme) => theme.palette.warning.main;
      return (theme) => theme.palette.error.main;
    };

    return (
      <IconWrapper
        bg={`linear-gradient(145deg, ${getScoreColor(
          qualityScore
        )} 0%, ${getScoreColor(qualityScore)} 100%)`}
        shadow={`0 2px 8px ${getScoreColor(qualityScore)}40`}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "flex-start",
            position: "relative",
            transform: "rotate(-10deg)",
          }}
        >
          <Typography
            component="span"
            sx={{
              fontSize: 14,
              fontWeight: "bold",
              color: (theme) => theme.palette.common.white,
              lineHeight: 1,
              filter: "drop-shadow(0 1px 1px rgba(0,0,0,0.1))",
            }}
          >
            {qualityScore}
          </Typography>
          {qualityScore < 10 && (
            <Typography
              component="span"
              sx={{
                fontSize: 8,
                fontWeight: "medium",
                color: "rgba(255,255,255,0.85)",
                position: "relative",
                top: 1,
                left: 0,
                lineHeight: 1,
              }}
            >
              /10
            </Typography>
          )}
        </Box>
      </IconWrapper>
    );
  }

  if (issuesCount > 0) {
    return (
      <IconWrapper
        bg={(theme) => `linear-gradient(145deg, ${theme.palette.error.main} 0%, ${theme.palette.error.main} 100%)`}
        shadow={(theme) => `0 2px 8px ${theme.palette.error.main}40`}
      >
        <ErrorOutlineIcon
          sx={{
            fontSize: 16,
            color: (theme) => theme.palette.common.white,
            filter: "drop-shadow(0 1px 1px rgba(0,0,0,0.1))",
          }}
        />
      </IconWrapper>
    );
  }

  if (
    recommendationsCount > 0 ||
    (type === "Security" && recommendationsCount > 0)
  ) {
    return (
      <IconWrapper
        bg={(theme) => `linear-gradient(145deg, ${theme.palette.warning.main} 0%, ${theme.palette.warning.main} 100%)`}
        shadow={(theme) => `0 2px 8px ${theme.palette.warning.main}40`}
      >
        <InfoOutlinedIcon
          sx={{
            fontSize: 16,
            color: (theme) => theme.palette.common.white,
            filter: "drop-shadow(0 1px 1px rgba(0,0,0,0.1))",
          }}
        />
      </IconWrapper>
    );
  }

  return (
    <IconWrapper
      bg={(theme) => `linear-gradient(145deg, ${theme.palette.success.main} 0%, ${theme.palette.success.main} 100%)`}
      shadow={(theme) => `0 2px 8px ${theme.palette.success.main}40`}
    >
      <CheckCircleIcon
        sx={{
          fontSize: 16,
          color: "#fff",
          filter: "drop-shadow(0 1px 1px rgba(0,0,0,0.1))",
        }}
      />
    </IconWrapper>
  );
};

const ValidationSection = ({
  title,
  icon,
  passed,
  issuesCount = 0,
  recommendationsCount = 0,
  renderContent,
  type = "default",
  isLoading,
  security = null,
  qualityScore = null,
}) => {
  console.log("qualityScorequalityScore", qualityScore);
  const [expanded, setExpanded] = useState(false);
  const hasContent =
    (issuesCount > 0 || recommendationsCount > 0) && !isLoading;

  const handleToggle = () => {
    setExpanded((prev) => !prev);
  };

  return (
    <Box
      sx={{
        minWidth: 320,
        borderRadius: 10,
        bgcolor: "rgba(250,250,250,1)",
        backdropFilter: "blur(25px) saturate(180%)",
        boxShadow: expanded
          ? "0 8px 32px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.02)"
          : "0 4px 24px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.01)",
        overflow: "hidden",
        transition: "all 0.4s cubic-bezier(0.16,1,0.3,1)",
        width: "100%",
        flex: "1 1 auto",
        // backgroundImage: "url('/icons/security.png')",
        backgroundPosition: "right bottom",
        backgroundRepeat: "no-repeat",
        backgroundSize: "160px",
      }}
    >
      <Box
        sx={{
          px: 3,
          py: 2.5,
          cursor: hasContent ? "pointer" : "default",
        }}
        onClick={hasContent ? handleToggle : undefined}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Stack direction="row" spacing={2} alignItems="center">
            {icon && (
              <NeumorphicIcon>
                {React.cloneElement(icon, {
                  sx: {
                    fontSize: 18,
                    color: (theme) => theme.palette.grey[600],
                    filter: "drop-shadow(0 1px 1px rgba(255,255,255,0.7))",
                    position: "relative",
                    zIndex: 2,
                  },
                })}
              </NeumorphicIcon>
            )}
            <Typography
              sx={{
                fontSize: 16,
                fontWeight: 600,
                letterSpacing: "-0.02em",
                color: (theme) => theme.palette.text.primary,
                textShadow: "0 1px 1px rgba(255,255,255,0.5)",
              }}
            >
              {title}
            </Typography>
          </Stack>

          <Stack direction="row" spacing={1} alignItems="center">
            <ValidationStatus
              passed={passed}
              issuesCount={issuesCount}
              recommendationsCount={recommendationsCount}
              isLoading={isLoading}
              type={type}
              qualityScore={qualityScore}
            />

            {hasContent && (
              <ExpandButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleToggle();
                }}
                aria-expanded={expanded}
                aria-label="mostrar detalles"
                sx={{
                  transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
                }}
              >
                <ExpandMoreIcon sx={{ color: "black" }} />
              </ExpandButton>
            )}
          </Stack>
        </Box>

        <Box mt={3}>
          <ValidationStats
            issuesCount={issuesCount}
            recommendationsCount={recommendationsCount}
            type={type}
            security={security}
            isLoading={isLoading}
          />
        </Box>
      </Box>

      {hasContent && (
        <Collapse in={expanded} timeout={200}>
          <Box
            sx={{
              px: 3,
              pt: 0.5,
              pb: 3,
              pt: 2,
              borderTop: "1px solid rgba(0,0,0,0.04)",
            }}
          >
            {renderContent()}
          </Box>
        </Collapse>
      )}
    </Box>
  );
};

export default ValidationSection;
