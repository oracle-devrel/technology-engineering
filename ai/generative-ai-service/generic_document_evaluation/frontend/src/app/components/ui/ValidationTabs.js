import {
  CheckCircle,
  Error as ErrorIcon,
  ExpandLess,
  ExpandMore,
  Info,
  Warning,
} from "@mui/icons-material";
import {
  Avatar,
  Box,
  Chip,
  Collapse,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
} from "@mui/material";
import { useState } from "react";

export default function SecurityIssuesGrid({
  criticalIssues = [],
  highIssues = [],
  mediumIssues = [],
  lowIssues = [],
}) {
  const [expandedSections, setExpandedSections] = useState({
    critical: true,
    high: true,
    medium: true,
    low: true,
  });

  const toggleSection = (section) => {
    setExpandedSections({
      ...expandedSections,
      [section]: !expandedSections[section],
    });
  };

  const getSeverityConfig = (severity) => {
    switch (severity) {
      case "critical":
        return {
          icon: <ErrorIcon fontSize="small" />,
          color: (theme) => theme.palette.error.main,
          bgcolor: "rgba(255, 59, 48, 0.1)",
          title: "Critical Issues",
        };
      case "high":
        return {
          icon: <ErrorIcon fontSize="small" />,
          color: (theme) => theme.palette.warning.main,
          bgcolor: "rgba(255, 149, 0, 0.1)",
          title: "High Priority Issues",
        };
      case "medium":
        return {
          icon: <Warning fontSize="small" />,
          color: (theme) => theme.palette.accent.gold,
          bgcolor: "rgba(255, 204, 0, 0.1)",
          title: "Medium Priority Issues",
        };
      case "low":
        return {
          icon: <Info fontSize="small" />,
          color: (theme) => theme.palette.primary.main,
          bgcolor: "rgba(0, 122, 255, 0.1)",
          title: "Low Priority Issues",
        };
      default:
        return {
          icon: <Info fontSize="small" />,
          color: (theme) => theme.palette.success.main,
          bgcolor: "rgba(52, 199, 89, 0.1)",
          title: "Issues",
        };
    }
  };

  const renderIssueSection = (issues, severity) => {
    const { icon, color, bgcolor, title } = getSeverityConfig(severity);
    const hasIssues = issues.length > 0;
    const isExpanded = expandedSections[severity];

    return (
      <Paper
        elevation={0}
        sx={{
          p: 2,
          height: "100%",
          borderRadius: 3,
          bgcolor: "rgba(255, 255, 255, 0.8)",
          border: "1px solid rgba(0, 0, 0, 0.05)",
          backdropFilter: "blur(10px)",
          transition: "all 0.2s ease",
          "&:hover": {
            boxShadow: hasIssues ? "0 4px 12px rgba(0, 0, 0, 0.08)" : "none",
            transform: hasIssues ? "translateY(-2px)" : "none",
          },
        }}
      >
        <Box
          onClick={hasIssues ? () => toggleSection(severity) : undefined}
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            cursor: hasIssues ? "pointer" : "default",
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
            <Avatar
              sx={{
                width: 36,
                height: 36,
                bgcolor: bgcolor,
                color: color,
              }}
            >
              {icon}
            </Avatar>
            <Box>
              <Typography
                variant="subtitle1"
                sx={{ fontWeight: 600, fontSize: "0.95rem" }}
              >
                {title}
              </Typography>
              <Chip
                label={`${issues.length} ${
                  issues.length === 1 ? "issue" : "issues"
                }`}
                size="small"
                sx={{
                  height: 20,
                  fontSize: "0.7rem",
                  fontWeight: 600,
                  bgcolor: hasIssues ? bgcolor : "rgba(0, 0, 0, 0.04)",
                  color: hasIssues ? color : "rgba(0, 0, 0, 0.4)",
                }}
              />
            </Box>
          </Box>
          {hasIssues &&
            (isExpanded ? (
              <ExpandLess sx={{ color: "rgba(0, 0, 0, 0.4)" }} />
            ) : (
              <ExpandMore sx={{ color: "rgba(0, 0, 0, 0.4)" }} />
            ))}
        </Box>

        <Collapse in={isExpanded && hasIssues} timeout="auto">
          {hasIssues ? (
            <List
              dense
              sx={{
                mt: 1.5,
                pt: 1.5,
                borderTop: "1px solid rgba(0, 0, 0, 0.06)",
                maxHeight: 180,
                overflowY: "auto",
                "&::-webkit-scrollbar": {
                  width: 6,
                },
                "&::-webkit-scrollbar-track": {
                  background: "rgba(0, 0, 0, 0.05)",
                  borderRadius: 3,
                },
                "&::-webkit-scrollbar-thumb": {
                  background: "rgba(0, 0, 0, 0.1)",
                  borderRadius: 3,
                },
              }}
            >
              {issues.map((issue, index) => (
                <ListItem
                  key={index}
                  sx={{
                    py: 0.75,
                    pl: 1,
                    pr: 1,
                    mb: 1,
                    borderRadius: 2,
                    bgcolor: "rgba(255, 255, 255, 0.7)",
                    border: "1px solid rgba(0, 0, 0, 0.03)",
                    "&:hover": {
                      bgcolor: "rgba(255, 255, 255, 0.9)",
                      boxShadow: "0 2px 4px rgba(0, 0, 0, 0.06)",
                    },
                  }}
                >
                  <ListItemIcon sx={{ minWidth: 32, color }}>
                    {icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body2"
                        sx={{ fontSize: "0.8rem", fontWeight: 500 }}
                      >
                        {issue}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : null}
        </Collapse>
      </Paper>
    );
  };

  const hasAnyIssues =
    criticalIssues.length ||
    highIssues.length ||
    mediumIssues.length ||
    lowIssues.length;

  if (!hasAnyIssues) {
    return (
      <Box
        sx={{
          py: 4,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          gap: 1,
        }}
      >
        <Avatar
          sx={{
            bgcolor: "rgba(52, 199, 89, 0.1)",
            width: 48,
            height: 48,
            mb: 1,
          }}
        >
          <CheckCircle sx={{ color: "#34C759" }} />
        </Avatar>
        <Typography variant="h6" sx={{ fontWeight: 600, color: "#34C759" }}>
          All security checks passed!
        </Typography>
        <Typography
          variant="body2"
          sx={{ color: "text.secondary", textAlign: "center" }}
        >
          No security issues were found in the code.
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} md={6}>
        {renderIssueSection(criticalIssues, "critical")}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderIssueSection(highIssues, "high")}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderIssueSection(mediumIssues, "medium")}
      </Grid>
      <Grid item xs={12} md={6}>
        {renderIssueSection(lowIssues, "low")}
      </Grid>
    </Grid>
  );
}
