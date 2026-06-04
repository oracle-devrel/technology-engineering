import { useState } from "react";
import { Box, Typography, Dialog, DialogTitle, DialogContent, IconButton, Chip, Accordion, AccordionSummary, AccordionDetails } from "@mui/material";
import { motion } from "framer-motion";
import { ExternalLink, FileText, X, ChevronDown, Search } from "lucide-react";

export default function Sources({ sources, delay = 0 }) {
  const [openDialog, setOpenDialog] = useState(false);
  const [expandedChunk, setExpandedChunk] = useState(null);

  if (!sources || sources.length === 0) return null;

  // Split file_citation (chunks from RAG) from url_citation (web search)
  const fileChunks = sources.filter(s => s.type === 'file_citation');
  const urlSources = sources.filter(s => s.type !== 'file_citation');

  // Dedup URL sources by URL
  const seenUrls = new Set();
  const uniqueUrls = urlSources.filter(s => {
    const key = s.url;
    if (!key || seenUrls.has(key)) return false;
    seenUrls.add(key);
    return true;
  });

  // Sort chunks by score desc; keep query info on each chunk for the badge
  const sortedChunks = [...fileChunks].sort((a, b) => (b.score || 0) - (a.score || 0));

  // Count distinct queries to decide whether to show query-source labels
  const distinctQueries = new Set(fileChunks.map(c => c.query).filter(Boolean));
  const totalQueries = distinctQueries.size;
  const totalChunks = fileChunks.length;

  const fileChipLabel = (() => {
    if (totalChunks === 0) return null;
    if (totalQueries <= 1) return `Sources · ${totalChunks} chunk${totalChunks === 1 ? '' : 's'}`;
    return `Sources · ${totalQueries} searches · ${totalChunks} chunks`;
  })();

  if (uniqueUrls.length === 0 && fileChipLabel === null) return null;

  const fileChipSx = {
    display: "inline-flex",
    alignItems: "center",
    gap: 0.5,
    px: 1.25,
    py: 0.5,
    borderRadius: "16px",
    backgroundColor: "rgba(139,92,246,0.06)",
    border: "1px solid rgba(139,92,246,0.15)",
    color: "#6D28D9",
    fontSize: "0.8rem",
    lineHeight: 1.3,
    transition: "all 0.15s ease",
    cursor: "pointer",
    "&:hover": {
      backgroundColor: "rgba(139,92,246,0.1)",
      borderColor: "rgba(139,92,246,0.25)",
    },
  };

  const urlChipSx = {
    display: "inline-flex",
    alignItems: "center",
    gap: 0.5,
    px: 1.25,
    py: 0.5,
    borderRadius: "16px",
    backgroundColor: "rgba(0,0,0,0.04)",
    border: "1px solid rgba(0,0,0,0.08)",
    textDecoration: "none",
    color: "#444",
    fontSize: "0.8rem",
    lineHeight: 1.3,
    transition: "all 0.15s ease",
    maxWidth: 280,
    cursor: "pointer",
    "&:hover": { backgroundColor: "rgba(0,0,0,0.08)", borderColor: "rgba(0,0,0,0.15)" },
  };

  const scoreColor = (score) => {
    if (typeof score !== 'number') return { bg: "rgba(0,0,0,0.05)", fg: "rgba(0,0,0,0.5)" };
    if (score > 0.5) return { bg: "rgba(34,197,94,0.1)", fg: "#16a34a" };
    if (score > 0.25) return { bg: "rgba(234,179,8,0.1)", fg: "#ca8a04" };
    return { bg: "rgba(0,0,0,0.05)", fg: "rgba(0,0,0,0.5)" };
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay, ease: "easeOut" }}
      >
        <Box sx={{ mt: 1.5, display: "flex", flexWrap: "wrap", gap: 0.75 }}>
          {/* URL chips (web search) */}
          {uniqueUrls.map((s, i) => {
            const cleanUrl = s.url?.replace(/[?&]utm_source=openai/, '') || '#';
            const label = s.title || s.name || (() => {
              try { return new URL(s.url).hostname; } catch { return s.url; }
            })();
            return (
              <Box
                key={`u-${i}`}
                component="a"
                href={cleanUrl}
                target="_blank"
                rel="noopener noreferrer"
                sx={urlChipSx}
              >
                <ExternalLink size={12} style={{ flexShrink: 0, opacity: 0.6 }} />
                <Typography component="span" sx={{ fontSize: "inherit", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {label}
                </Typography>
              </Box>
            );
          })}

          {/* File summary chip */}
          {fileChipLabel && (
            <Box onClick={() => setOpenDialog(true)} sx={fileChipSx}>
              <FileText size={12} style={{ flexShrink: 0, opacity: 0.6 }} />
              <Typography component="span" sx={{ fontSize: "inherit" }}>
                {fileChipLabel}
              </Typography>
            </Box>
          )}
        </Box>
      </motion.div>

      {/* Sources detail modal — one accordion per chunk */}
      <Dialog
        open={openDialog}
        onClose={() => setOpenDialog(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            borderRadius: 2,
            height: "min(85vh, 760px)",
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
            backgroundColor: "#fbfaff",
            boxShadow: "0 24px 60px -20px rgba(76, 29, 149, 0.25), 0 8px 24px -8px rgba(0,0,0,0.08)",
          },
        }}
      >
        {/* Header — fixed; never shrinks under scroll content */}
        <DialogTitle
          sx={{
            flexShrink: 0,
            display: "flex",
            alignItems: "center",
            gap: 1.25,
            px: 2.5,
            py: 1.75,
            borderBottom: "1px solid rgba(109,40,217,0.1)",
            backgroundColor: "#fff",
            backgroundImage:
              "linear-gradient(180deg, rgba(139,92,246,0.04) 0%, rgba(139,92,246,0) 100%)",
          }}
        >
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              backgroundColor: "rgba(139,92,246,0.1)",
              flexShrink: 0,
            }}
          >
            <FileText size={14} style={{ color: "#6D28D9" }} />
          </Box>
          <Box sx={{ flex: 1, minWidth: 0 }}>
            <Typography sx={{ fontSize: "0.95rem", fontWeight: 600, color: "#1a1a1a", lineHeight: 1.2 }}>
              Sources used
            </Typography>
            <Typography sx={{ fontSize: "0.7rem", color: "rgba(0,0,0,0.5)", fontWeight: 500, mt: 0.25, fontVariantNumeric: "tabular-nums" }}>
              {fileChipLabel}
            </Typography>
          </Box>
          <IconButton
            size="small"
            onClick={() => setOpenDialog(false)}
            sx={{
              p: 0.5,
              color: "rgba(0,0,0,0.5)",
              "&:hover": { backgroundColor: "rgba(0,0,0,0.05)", color: "#1a1a1a" },
            }}
          >
            <X size={15} />
          </IconButton>
        </DialogTitle>

        {/* Body — flex:1 + minHeight:0 + overflowY:auto is what makes scroll work inside a flex column */}
        <DialogContent
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            overflowX: "hidden",
            display: "flex",
            flexDirection: "column",
            gap: 0.6,
            px: 2,
            py: 1.5,
            // Custom thin scrollbar that matches the purple accent
            "&::-webkit-scrollbar": { width: 8 },
            "&::-webkit-scrollbar-track": { backgroundColor: "transparent" },
            "&::-webkit-scrollbar-thumb": {
              backgroundColor: "rgba(109,40,217,0.18)",
              borderRadius: 4,
              border: "2px solid #fbfaff",
            },
            "&::-webkit-scrollbar-thumb:hover": { backgroundColor: "rgba(109,40,217,0.32)" },
            scrollbarWidth: "thin",
            scrollbarColor: "rgba(109,40,217,0.25) transparent",
          }}
        >
          {sortedChunks.map((c, i) => {
            const href = c.file_id
              ? `/api/files/${c.file_id}/content${c.vector_store_id ? `?vsId=${c.vector_store_id}` : ''}`
              : null;
            const scorePct = typeof c.score === 'number' ? `${(c.score * 100).toFixed(0)}%` : null;
            const sc = scoreColor(c.score);
            const isExpanded = expandedChunk === i;
            return (
              <Accordion
                key={i}
                expanded={isExpanded}
                onChange={(_, exp) => setExpandedChunk(exp ? i : null)}
                disableGutters
                elevation={0}
                square={false}
                sx={{
                  border: "1px solid rgba(109,40,217,0.08)",
                  borderRadius: "10px !important",
                  backgroundColor: "rgba(255,255,255,0.6)",
                  transition: "all 0.18s ease",
                  "&:before": { display: "none" },
                  "&:hover": {
                    borderColor: "rgba(109,40,217,0.18)",
                    backgroundColor: "rgba(255,255,255,0.95)",
                  },
                  "&.Mui-expanded": {
                    margin: 0,
                    backgroundColor: "#ffffff",
                    borderColor: "rgba(109,40,217,0.25)",
                    boxShadow: "0 4px 16px -6px rgba(109,40,217,0.18)",
                  },
                  "& .MuiCollapse-root": { borderRadius: "0 0 10px 10px" },
                }}
              >
                <AccordionSummary
                  expandIcon={<ChevronDown size={14} style={{ color: "rgba(109,40,217,0.7)" }} />}
                  sx={{
                    minHeight: 0,
                    px: 1.5,
                    py: 0.5,
                    borderRadius: "10px",
                    "& .MuiAccordionSummary-content": { my: 0.75, alignItems: "center", gap: 1.25 },
                    "&.Mui-expanded": {
                      minHeight: 0,
                      borderBottom: "1px solid rgba(109,40,217,0.08)",
                      borderRadius: "10px 10px 0 0",
                    },
                  }}
                >
                  <FileText size={12} style={{ color: "#6D28D9", opacity: 0.7, flexShrink: 0 }} />
                  <Typography
                    sx={{
                      fontSize: "0.78rem",
                      fontWeight: 500,
                      color: "rgba(0,0,0,0.82)",
                      flex: 1,
                      minWidth: 0,
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                    title={c.filename || c.file_id}
                  >
                    {c.filename || c.file_id || 'Unknown'}
                  </Typography>
                  {scorePct && (
                    <Chip
                      label={scorePct}
                      size="small"
                      sx={{
                        height: 18,
                        fontSize: "0.62rem",
                        fontWeight: 600,
                        backgroundColor: sc.bg,
                        color: sc.fg,
                        flexShrink: 0,
                      }}
                    />
                  )}
                  {href && (
                    <IconButton
                      size="small"
                      component="a"
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                      onFocus={(e) => e.stopPropagation()}
                      title="Open document in new tab"
                      sx={{
                        p: 0.4,
                        ml: 0.25,
                        color: "rgba(109,40,217,0.55)",
                        flexShrink: 0,
                        borderRadius: "6px",
                        "&:hover": {
                          backgroundColor: "rgba(109,40,217,0.1)",
                          color: "#6D28D9",
                        },
                      }}
                    >
                      <ExternalLink size={13} />
                    </IconButton>
                  )}
                </AccordionSummary>
                <AccordionDetails sx={{ px: 2, py: 1.5, backgroundColor: "transparent" }}>
                  {c.query && totalQueries > 1 && (
                    <Box
                      sx={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 0.5,
                        mb: 1.25,
                        px: 0.85,
                        py: 0.35,
                        borderRadius: "999px",
                        backgroundColor: "rgba(139,92,246,0.07)",
                        color: "#6D28D9",
                        maxWidth: "100%",
                      }}
                    >
                      <Search size={10} style={{ flexShrink: 0, opacity: 0.8 }} />
                      <Typography
                        sx={{
                          fontSize: "0.66rem",
                          fontWeight: 500,
                          letterSpacing: 0.1,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                        }}
                      >
                        {c.query}
                      </Typography>
                    </Box>
                  )}
                  {c.snippet ? (
                    <Box
                      sx={{
                        pl: 1.5,
                        borderLeft: "2px solid rgba(139,92,246,0.3)",
                      }}
                    >
                      <Typography
                        component="div"
                        sx={{
                          fontSize: "0.82rem",
                          lineHeight: 1.65,
                          color: "rgba(0,0,0,0.78)",
                          fontFamily: "'Iowan Old Style', 'Palatino Linotype', Georgia, serif",
                          whiteSpace: "pre-wrap",
                          wordBreak: "break-word",
                        }}
                      >
                        {c.snippet.length >= 3000 ? `${c.snippet.trim()}…` : c.snippet.trim()}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography sx={{ fontSize: "0.75rem", color: "rgba(0,0,0,0.4)", fontStyle: "italic" }}>
                      No snippet available
                    </Typography>
                  )}
                </AccordionDetails>
              </Accordion>
            );
          })}
        </DialogContent>
      </Dialog>
    </>
  );
}
