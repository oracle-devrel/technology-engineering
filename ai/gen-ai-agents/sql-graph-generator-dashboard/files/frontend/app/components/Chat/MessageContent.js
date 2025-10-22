"use client";

import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
} from "@mui/material";
import { ExternalLink, Eye, FileText } from "lucide-react";
import Markdown from "markdown-to-jsx";
import { useState } from "react";

export default function MessageContent({ message, isFromBot }) {
  const payload = message.messagePayload;
  const [citationDialogOpen, setCitationDialogOpen] = useState(false);
  const [selectedCitationContent, setSelectedCitationContent] = useState("");

  const isLongText = (value) => {
    const stringValue =
      value !== null && value !== undefined ? String(value) : "";
    return stringValue.length > 100;
  };

  switch (payload.type) {
    case "text":
      return (
        <Box>
          <Box
            className="markdown-content"
            sx={{
              fontSize: "0.88rem",
              letterSpacing: "0.01px",
              lineHeight: 1.5,
              ...(isFromBot && {
                fontFamily: "var(--font-exo2), sans-serif !important",
                "& *": {
                  fontFamily: "var(--font-exo2), sans-serif !important",
                },
                "& span": {
                  fontFamily: "var(--font-exo2), sans-serif !important",
                },
              }),
            }}
          >
            <Markdown>{payload.text}</Markdown>
          </Box>

          {payload.citations && payload.citations.length > 0 && (
            <Box sx={{ mt: 2, pt: 2, borderTop: "1px solid #e0e0e0" }}>
              <Typography
                variant="caption"
                sx={{ fontWeight: 600, color: "text.secondary" }}
              >
                Sources:
              </Typography>
              {payload.citations.map((citation, index) => (
                <Box
                  key={index}
                  sx={{
                    mt: 1,
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    py: 0.5,
                  }}
                >
                  <FileText
                    size={14}
                    style={{ color: "#666", flexShrink: 0 }}
                  />

                  <Tooltip title={citation.document_name} arrow>
                    <Typography
                      variant="caption"
                      sx={{
                        flexGrow: 1,
                        maxWidth: "350px",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                        color: "text.primary",
                      }}
                    >
                      {citation.document_name}
                    </Typography>
                  </Tooltip>

                  {citation.page_numbers &&
                    citation.page_numbers.length > 0 && (
                      <Typography
                        variant="caption"
                        sx={{ color: "#999", fontSize: "0.7rem" }}
                      >
                        pages {citation.page_numbers.join(", ")}
                      </Typography>
                    )}

                  <Box sx={{ display: "flex", gap: 0.5, ml: "auto" }}>
                    <Tooltip title="View content" arrow>
                      <IconButton
                        size="small"
                        sx={{ width: 24, height: 24 }}
                        onClick={() => {
                          setSelectedCitationContent(citation.content);
                          setCitationDialogOpen(true);
                        }}
                      >
                        <Eye size={16} />
                      </IconButton>
                    </Tooltip>

                    <Tooltip title="Open document" arrow>
                      <IconButton
                        size="small"
                        sx={{ width: 24, height: 24 }}
                        onClick={() =>
                          window.open(citation.source_url, "_blank")
                        }
                      >
                        <ExternalLink size={16} />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
              ))}

              <Dialog
                open={citationDialogOpen}
                onClose={() => setCitationDialogOpen(false)}
                maxWidth="md"
                fullWidth
              >
                <DialogTitle>Citation Content</DialogTitle>
                <DialogContent>
                  <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>
                    {selectedCitationContent}
                  </Typography>
                </DialogContent>
                <DialogActions>
                  <Button onClick={() => setCitationDialogOpen(false)}>
                    Close
                  </Button>
                </DialogActions>
              </Dialog>
            </Box>
          )}
        </Box>
      );

    case "diagram":
      return (
        <Box>
          {payload.text && payload.text.trim() && (
            <Box sx={{ mb: 2 }}>
              <Markdown>{payload.text}</Markdown>
            </Box>
          )}
          <Box
            component="img"
            src={`data:image/png;base64,${payload.diagram_base64}`}
            alt="Generated diagram"
            sx={{
              maxWidth: "100%",
              height: "auto",
              borderRadius: 1,
              boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
            }}
          />
        </Box>
      );

    case "sql_result":
      return (
        <Box>
          {payload.generatedQuery && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                Generated Query:
              </Typography>
              <Box
                component="pre"
                sx={{
                  backgroundColor: "#f5f5f5",
                  padding: 1.5,
                  borderRadius: 1,
                  fontSize: "0.8rem",
                  overflow: "auto",
                  fontFamily: "monospace",
                }}
              >
                {payload.generatedQuery}
              </Box>
            </Box>
          )}

          {payload.executionResult &&
            payload.executionResult.length > 0 &&
            (() => {
              const data = payload.executionResult;
              const columns = Object.keys(data[0]);

              const getColumnWidth = (columnName, columnIndex) => {
                const columnValues = data.map(
                  (row) => Object.values(row)[columnIndex]
                );
                const allValues = [columnName, ...columnValues];

                const lengths = allValues.map(
                  (val) => String(val || "").length
                );
                const avgLength =
                  lengths.reduce((sum, len) => sum + len, 0) / lengths.length;
                const maxLength = Math.max(...lengths);
                const headerLength = columnName.length;

                const headerMinWidth = Math.max(headerLength * 8, 100);

                let calculatedWidth;
                if (maxLength > 200) {
                  calculatedWidth = { minWidth: "280px", maxWidth: "350px" };
                } else if (maxLength > 100) {
                  calculatedWidth = { minWidth: "200px", maxWidth: "280px" };
                } else if (avgLength > 30) {
                  calculatedWidth = { minWidth: "150px", maxWidth: "200px" };
                } else if (avgLength > 15) {
                  calculatedWidth = { minWidth: "120px", maxWidth: "150px" };
                } else {
                  calculatedWidth = { minWidth: "100px", maxWidth: "120px" };
                }

                const finalMinWidth = Math.max(
                  parseInt(calculatedWidth.minWidth),
                  headerMinWidth
                );

                return {
                  minWidth: `${finalMinWidth}px`,
                  maxWidth: calculatedWidth.maxWidth,
                };
              };

              return (
                <Box>
                  <Typography
                    variant="subtitle2"
                    sx={{ mb: 1, fontWeight: 600 }}
                  >
                    Results:
                  </Typography>
                  <TableContainer
                    component={Paper}
                    variant="outlined"
                    sx={{ maxHeight: 400 }}
                  >
                    <Table
                      size="small"
                      stickyHeader
                      sx={{ tableLayout: "fixed" }}
                    >
                      <TableHead>
                        <TableRow>
                          {columns.map((key, index) => {
                            const widths = getColumnWidth(key, index);
                            return (
                              <TableCell
                                key={key}
                                sx={{
                                  fontWeight: 600,
                                  verticalAlign: "top",
                                  ...widths,
                                  width: widths.minWidth,
                                }}
                              >
                                {key}
                              </TableCell>
                            );
                          })}
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {data.map((row, rowIndex) => (
                          <TableRow key={rowIndex}>
                            {Object.values(row).map((value, cellIndex) => {
                              const stringValue =
                                value !== null && value !== undefined
                                  ? String(value)
                                  : "";
                              const isLong = isLongText(value);
                              const widths = getColumnWidth(
                                columns[cellIndex],
                                cellIndex
                              );

                              return (
                                <TableCell
                                  key={cellIndex}
                                  sx={{
                                    verticalAlign: "top",
                                    padding: "8px 16px",
                                    ...widths,
                                  }}
                                >
                                  {isLong ? (
                                    <Box
                                      sx={{
                                        maxHeight: "120px",
                                        overflowY: "auto",
                                        overflowX: "hidden",
                                        wordBreak: "break-word",
                                        whiteSpace: "pre-wrap",
                                        fontSize: "0.875rem",
                                        lineHeight: 1.4,
                                        "&::-webkit-scrollbar": {
                                          width: "6px",
                                        },
                                        "&::-webkit-scrollbar-track": {
                                          background: "#f1f1f1",
                                          borderRadius: "3px",
                                        },
                                        "&::-webkit-scrollbar-thumb": {
                                          background: "#c1c1c1",
                                          borderRadius: "3px",
                                          "&:hover": {
                                            background: "#a8a8a8",
                                          },
                                        },
                                      }}
                                    >
                                      {stringValue}
                                    </Box>
                                  ) : (
                                    <Box
                                      sx={{
                                        wordBreak: "break-word",
                                        whiteSpace: "nowrap",
                                        overflow: "hidden",
                                        textOverflow: "ellipsis",
                                        fontSize: "0.875rem",
                                        lineHeight: 1.4,
                                        ...(stringValue.length > 50 && {
                                          whiteSpace: "pre-wrap",
                                          overflow: "visible",
                                          textOverflow: "clip",
                                        }),
                                      }}
                                      title={stringValue}
                                    >
                                      {stringValue}
                                    </Box>
                                  )}
                                </TableCell>
                              );
                            })}
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              );
            })()}
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
