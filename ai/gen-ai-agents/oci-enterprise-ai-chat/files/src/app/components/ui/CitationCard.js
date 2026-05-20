"use client";

import { ExitToApp as ExitToAppIcon } from "@mui/icons-material";
import {
  Box,
  Button,
  Link,
  Paper,
  Typography,
  useTheme,
} from "@mui/material";
import { useState } from "react";

export default function CitationCard({ citation, index }) {
  const theme = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const maxChars = 250;
  const shouldTruncate = citation.sourceText?.length > maxChars;

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        backgroundColor: "rgba(0, 0, 0, 0.02)",
        border: "1px solid rgba(0, 0, 0, 0.08)",
        borderRadius: 2,
        transition: "all 0.2s ease",
        "&:hover": {
          border: "1px solid rgba(0, 0, 0, 0.12)",
          boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
        },
      }}
    >
      <Box sx={{ mb: 1 }}>
        <Typography
          sx={{
            fontWeight: 600,
            fontSize: "13px",
            color: "rgba(0,0,0,0.9)",
          }}
        >
          {citation.title || `Source ${index + 1}`}
        </Typography>
        {citation.pageNumbers && citation.pageNumbers.length > 0 && (
          <Typography
            sx={{
              fontSize: "11px",
              color: "rgba(0,0,0,0.5)",
              mt: 0.25,
            }}
          >
            Pages: {citation.pageNumbers.join(", ")}
          </Typography>
        )}
      </Box>

      <Box
        sx={{
          backgroundColor: "rgba(0, 0, 0, 0.01)",
          borderRadius: 1,
          p: 1.5,
          mb: 1.5,
          border: "1px solid rgba(0, 0, 0, 0.04)",
        }}
      >
        <Typography
          sx={{
            fontSize: "12px",
            color: "rgba(0,0,0,0.8)",
            whiteSpace: "pre-wrap",
            lineHeight: 1.6,
            fontFamily: "var(--font-exo2), sans-serif",
          }}
        >
          {isExpanded
            ? citation.sourceText
            : citation.sourceText?.slice(0, maxChars)}
          {!isExpanded && shouldTruncate && "..."}
        </Typography>

        {shouldTruncate && (
          <Button
            onClick={() => setIsExpanded(!isExpanded)}
            size="small"
            variant="contained"
            sx={{
              mt: 1,
              padding: "4px 12px",
              fontSize: "11px",
              textTransform: "none",
              backgroundColor: theme.palette.primary.main,
              color: "white",
              fontFamily: "var(--font-exo2), sans-serif",
              fontWeight: 500,
              boxShadow: "none",
              "&:hover": {
                backgroundColor: theme.palette.primary.dark,
                boxShadow: "0 2px 4px rgba(0, 0, 0, 0.1)",
              },
            }}
          >
            {isExpanded ? "Show less" : "Show more"}
          </Button>
        )}
      </Box>

      {citation.sourceLocation?.url && (
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <ExitToAppIcon sx={{ fontSize: 14, color: "rgba(0,0,0,0.4)" }} />
          <Link
            href={citation.sourceLocation.url}
            target="_blank"
            rel="noopener noreferrer"
            sx={{
              fontSize: "12px",
              color: theme.palette.primary.main,
              textDecoration: "none",
              fontWeight: 500,
              fontFamily: "var(--font-exo2), sans-serif",
              "&:hover": {
                textDecoration: "underline",
              },
            }}
          >
            View Full Document
          </Link>
        </Box>
      )}
    </Paper>
  );
}