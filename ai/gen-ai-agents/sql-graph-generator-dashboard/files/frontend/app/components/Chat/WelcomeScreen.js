"use client";

import { Box, Button, Typography, alpha, darken, lighten } from "@mui/material";
import { useTheme } from "@mui/material/styles";

const SUGGESTIONS = [
  "show the top 5 orders",
  "show the number of order per region?",
];

export default function WelcomeScreen({ projectName, logoUrl, onSendMessage }) {
  const theme = useTheme();

  const handleSuggestionClick = (suggestion) => {
    if (onSendMessage) {
      onSendMessage(suggestion);
    }
  };

  return (
    <Box
      sx={{
        position: "relative",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        height: "100%",
        p: 2,
        mb: 8,
      }}
    >
      <Box
        component="img"
        src={logoUrl || "/oracle-logo.png"}
        alt={`${projectName} logo`}
        sx={{
          height: 70,
          maxWidth: 270,
          objectFit: "contain",
          mb: 3,
        }}
      />

      <Typography variant="h5" gutterBottom align="center">
        {projectName}
      </Typography>
      <Typography
        variant="body2"
        color="text.secondary"
        align="center"
        sx={{ mb: 4 }}
      >
        How can I help you today?
      </Typography>

      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          gap: 1.5,
          width: "100%",
          maxWidth: 500,
          justifyContent: "center",
        }}
      >
        {SUGGESTIONS.map((suggestion, index) => (
          <Button
            key={index}
            variant="contained"
            onClick={() => handleSuggestionClick(suggestion)}
            sx={{
              py: 1,
              px: 2,
              borderRadius: 2,
              textTransform: "none",
              fontSize: "0.825rem",
              fontWeight: 400,
              flex: "1 1 calc(50% - 6px)",
              minWidth: "200px",
              backgroundColor: lighten(theme.palette.primary.main, 0.9),
              color: darken(theme.palette.primary.main, 0.1),
              border: "none",
              boxShadow: "none",
              "&:hover": {
                backgroundColor: alpha(theme.palette.primary.main, 0.2),
                color: theme.palette.primary.dark,
                boxShadow: "none",
              },
              "&:disabled": {
                backgroundColor: alpha(theme.palette.action.disabled, 0.1),
                color: theme.palette.action.disabled,
              },
            }}
          >
            {suggestion}
          </Button>
        ))}
      </Box>
    </Box>
  );
}
