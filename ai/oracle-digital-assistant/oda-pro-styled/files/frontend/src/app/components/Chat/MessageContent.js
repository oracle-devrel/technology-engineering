"use client";

import { Box, Card, CardContent, Chip, Typography } from "@mui/material";
import { FileText } from "lucide-react";
import Markdown from "markdown-to-jsx";

export default function MessageContent({ message, isFromBot }) {
  const payload = message.messagePayload;

  switch (payload.type) {
    case "text":
      return (
        <Box
          className="markdown-content"
          sx={{
            fontSize: "0.88rem",
            letterSpacing: "0.01px",
            lineHeight: 1.5,
            ...(isFromBot && {
              fontFamily: "var(--font-exo2), sans-serif",
              "& *": { fontFamily: "var(--font-exo2), sans-serif !important" },
            }),
          }}
        >
          <Markdown>{payload.text}</Markdown>
        </Box>
      );

    case "tool_chip":
      return (
        <Chip
          label={`🔍 ${payload.toolName.toUpperCase()}`}
          size="small"
          variant="outlined"
          sx={{
            backgroundColor: "rgba(25, 118, 210, 0.08)",
            borderColor: "rgba(25, 118, 210, 0.3)",
            color: "rgba(25, 118, 210, 0.9)",
          }}
        />
      );

    case "citation":
      return (
        <Box
          sx={{
            backgroundColor: "rgba(33, 150, 243, 0.04)",
            border: "1px solid rgba(33, 150, 243, 0.12)",
            borderLeft: "3px solid #2196F3",
            borderRadius: "0 6px 6px 0",
            padding: "8px 12px",
            fontSize: "0.8rem",
            display: "flex",
            alignItems: "center",
            gap: 1,
            "& a": {
              color: "#1976d2",
              textDecoration: "none",
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: 0.5,
              "&:hover": {
                textDecoration: "underline",
              },
            },
          }}
        >
          <FileText size={14} color="#1976d2" />
          <Box
            className="markdown-content"
            dangerouslySetInnerHTML={{
              __html: payload.text.replace(
                /<a href="([^"]*)"[^>]*>([^<]*)<\/a>/g,
                '<a href="$1" target="_blank" rel="noopener noreferrer">$2</a>'
              ),
            }}
          />
        </Box>
      );
    case "card":
      return (
        <Card variant="outlined">
          <CardContent>
            {payload.cards &&
              payload.cards.map((card, idx) => (
                <Box key={idx}>
                  {card.title && (
                    <Typography variant="h6">{card.title}</Typography>
                  )}
                  {card.description && (
                    <Typography variant="body2">{card.description}</Typography>
                  )}
                  {card.url && (
                    <Typography variant="body2">
                      <a
                        href={card.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {card.url}
                      </a>
                    </Typography>
                  )}
                </Box>
              ))}
          </CardContent>
        </Card>
      );
    case "attachment":
      const attachment = payload.attachment;

      if (attachment.type.startsWith("image/")) {
        return (
          <Box
            component="img"
            src={attachment.url}
            alt={attachment.title || "Uploaded image"}
            sx={{
              maxWidth: 200,
              maxHeight: 300,
              borderRadius: 0.5,
              objectFit: "contain",
            }}
          />
        );
      }

      return (
        <Typography>
          Attachment: {attachment.type} -{" "}
          <a href={attachment.url} target="_blank" rel="noopener noreferrer">
            {attachment.title || "View"}
          </a>
        </Typography>
      );

    default:
      return (
        <Typography color="error">
          Unsupported message type: {payload.type}
        </Typography>
      );
  }
}
