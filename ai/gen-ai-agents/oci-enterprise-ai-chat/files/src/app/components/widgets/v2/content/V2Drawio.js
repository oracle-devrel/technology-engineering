"use client";
import { useState, useMemo } from "react";
import { Box, Dialog, Typography, CircularProgress, IconButton } from "@mui/material";
import { Maximize2, X, ExternalLink } from "lucide-react";
import { COLORS, BORDER } from "@/app/config/widgetTheme";

/**
 * Serialize a parsed V2 node tree back to XML string.
 */
function serializeToXml(node) {
  if (typeof node === "string") return node;
  const attrs = Object.entries(node.attrs || {})
    .map(([k, v]) => ` ${k}="${v}"`)
    .join("");
  const inner = (node.children || []).map(serializeToXml).join("");
  if (!inner && !node.children?.length) {
    return `<${node.tag}${attrs}/>`;
  }
  return `<${node.tag}${attrs}>${inner}</${node.tag}>`;
}

/**
 * Extract compressed diagram data from app.diagrams.net editor URLs.
 * These URLs contain #create={type,compressed,data} JSON with deflated XML.
 */
function extractCreateData(src) {
  try {
    const hashIdx = src.indexOf('#create=');
    if (hashIdx === -1) return null;
    const encoded = src.substring(hashIdx + 8);
    const json = decodeURIComponent(encoded);
    const parsed = JSON.parse(json);
    if (parsed.data) return parsed.data;
  } catch {}
  return null;
}

export default function V2Drawio({ node, attrs = {} }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  const title = attrs.title || "";
  const height = attrs.height || "400px";

  const { iframeSrc, editUrl } = useMemo(() => {
    if (attrs.src) {
      const src = attrs.src;

      // Extract XML file URL from fragment — handles both raw and URL-encoded forms
      // (app.diagrams.net deep-links often arrive encoded: #Uhttps%3A%2F%2F…)
      const hashIdx = src.indexOf('#U');
      if (hashIdx !== -1) {
        const rawHash = src.substring(hashIdx + 2);
        let xmlUrl = rawHash;
        try { xmlUrl = decodeURIComponent(rawHash); } catch {}
        if (/^https?:\/\//i.test(xmlUrl)) {
          return {
            iframeSrc: `https://viewer.diagrams.net/?lightbox=1&nav=1#U${encodeURIComponent(xmlUrl)}`,
            editUrl: src,
          };
        }
      }

      // Already a viewer URL
      if (src.includes('viewer.diagrams.net')) {
        return { iframeSrc: src, editUrl: null };
      }

      // Editor URL with #create= compressed data — extract and pass to viewer
      const compressedData = extractCreateData(src);
      if (compressedData) {
        return {
          iframeSrc: `https://viewer.diagrams.net/?lightbox=1&nav=1#R${compressedData}`,
          editUrl: src,
        };
      }

      // Fallback: app.diagrams.net refuses iframes (X-Frame-Options: SAMEORIGIN),
      // so rewrite the host to viewer.diagrams.net which allows embedding
      const viewerSrc = src.replace(/^https?:\/\/(app|www)\.diagrams\.net/i, 'https://viewer.diagrams.net');
      return { iframeSrc: viewerSrc, editUrl: src };
    }

    // Inline XML mode — serialize children and encode for viewer
    if (!node?.children?.length) return { iframeSrc: null, editUrl: null };
    const xml = node.children.map(serializeToXml).join("");
    if (!xml.trim()) return { iframeSrc: null, editUrl: null };
    const encoded = encodeURIComponent(xml);
    return {
      iframeSrc: `https://viewer.diagrams.net/?lightbox=1&nav=1#R${encoded}`,
      editUrl: null,
    };
  }, [node, attrs.src]);

  if (!iframeSrc) return null;

  return (
    <>
      <Box
        sx={{
          borderRadius: `${BORDER.radius}px`,
          overflow: "hidden",
          border: `1px solid var(--dm-border, rgba(0,0,0,0.08))`,
          backgroundColor: "var(--dm-surface, #fff)",
        }}
      >
        {title && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              px: 2,
              py: 1,
              borderBottom: `1px solid var(--dm-border, rgba(0,0,0,0.08))`,
              backgroundColor: COLORS.background.widget,
            }}
          >
            <Typography
              sx={{
                fontSize: "0.85rem",
                fontWeight: 600,
                color: COLORS.text.primary,
              }}
            >
              {title}
            </Typography>
            <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
              {editUrl && (
                <IconButton size="small" onClick={() => window.open(editUrl, '_blank')} title="Edit in Draw.io">
                  <ExternalLink size={15} />
                </IconButton>
              )}
              <IconButton size="small" onClick={() => setOpen(true)} title="Fullscreen">
                <Maximize2 size={16} />
              </IconButton>
            </Box>
          </Box>
        )}

        <Box sx={{ position: "relative", width: "100%", height }}>
          {loading && (
            <Box
              sx={{
                position: "absolute",
                inset: 0,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backgroundColor: "var(--dm-surface, #fff)",
                zIndex: 1,
              }}
            >
              <CircularProgress size={28} sx={{ color: COLORS.info }} />
            </Box>
          )}
          <Box
            component="iframe"
            src={iframeSrc}
            onLoad={() => setLoading(false)}
            sx={{
              width: "100%",
              height: "100%",
              border: "none",
              display: "block",
            }}
          />
        </Box>

        {!title && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "flex-end",
              px: 1,
              py: 0.5,
              borderTop: `1px solid var(--dm-border, rgba(0,0,0,0.08))`,
              backgroundColor: COLORS.background.widget,
            }}
          >
            {editUrl && (
              <IconButton size="small" onClick={() => window.open(editUrl, '_blank')} title="Edit in Draw.io">
                <ExternalLink size={15} />
              </IconButton>
            )}
            <IconButton size="small" onClick={() => setOpen(true)} title="Fullscreen">
              <Maximize2 size={16} />
            </IconButton>
          </Box>
        )}
      </Box>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        fullScreen
        PaperProps={{
          sx: {
            backgroundColor: "var(--dm-surface, #fff)",
          },
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            px: 2,
            py: 1,
            borderBottom: `1px solid var(--dm-border, rgba(0,0,0,0.08))`,
          }}
        >
          <Typography sx={{ fontSize: "0.9rem", fontWeight: 600, color: COLORS.text.primary }}>
            {title || "Diagram"}
          </Typography>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            {editUrl && (
              <IconButton size="small" onClick={() => window.open(editUrl, '_blank')} title="Edit in Draw.io">
                <ExternalLink size={18} />
              </IconButton>
            )}
            <IconButton onClick={() => setOpen(false)}>
              <X size={20} />
            </IconButton>
          </Box>
        </Box>
        <Box
          component="iframe"
          src={iframeSrc}
          sx={{
            flex: 1,
            width: "100%",
            border: "none",
            display: "block",
          }}
        />
      </Dialog>
    </>
  );
}
