"use client";

import { memo, useRef, useState, useEffect, useCallback } from "react";
import { Box } from "@mui/material";
import { motion } from "framer-motion";
import WIDGET_V2_REGISTRY from "./WidgetV2Registry";

/**
 * Recursive node renderer — walks the v2 tree and maps each tag to a React component.
 */
const WidgetV2Node = memo(function WidgetV2Node({ node, onSubmit, disabled }) {
  if (typeof node === "string") {
    return node || null;
  }

  if (node.tag === "root") {
    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: "16px", width: "100%" }}>
        {node.children.map((child, i) => (
          <WidgetV2Node key={i} node={child} onSubmit={onSubmit} disabled={disabled} />
        ))}
      </Box>
    );
  }

  const Component = WIDGET_V2_REGISTRY[node.tag];
  if (!Component) {
    // Unknown tag — skip silently (lenient)
    return null;
  }

  const childElements = node.children?.length > 0
    ? node.children.map((child, i) => (
        <WidgetV2Node key={i} node={child} onSubmit={onSubmit} disabled={disabled} />
      ))
    : null;

  return (
    <Component attrs={node.attrs} onSubmit={onSubmit} disabled={disabled} node={node}>
      {childElements}
    </Component>
  );
});

/**
 * Top-level Widget V2 component.
 * Receives a parsed tree and renders it recursively.
 * Shows fade indicators when content overflows horizontally.
 */
function WidgetV2({ tree, isComplete, onSubmit, disabled }) {
  if (!tree) return null;

  const scrollRef = useRef(null);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const [canScrollLeft, setCanScrollLeft] = useState(false);

  const checkScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const threshold = 2;
    setCanScrollRight(el.scrollWidth - el.clientWidth - el.scrollLeft > threshold);
    setCanScrollLeft(el.scrollLeft > threshold);
  }, []);

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    checkScroll();
    const observer = new ResizeObserver(checkScroll);
    observer.observe(el);
    return () => observer.disconnect();
  }, [checkScroll]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Box sx={{ position: "relative", width: "100%" }}>
        {canScrollRight && (
          <Box sx={{
            position: "absolute", top: 0, right: 0, bottom: 0, width: 40,
            background: "linear-gradient(to right, transparent, var(--dm-surface, rgba(255,255,255,0.9)))",
            pointerEvents: "none", zIndex: 1, borderRadius: "0 4px 4px 0",
          }} />
        )}
        {canScrollLeft && (
          <Box sx={{
            position: "absolute", top: 0, left: 0, bottom: 0, width: 40,
            background: "linear-gradient(to left, transparent, var(--dm-surface, rgba(255,255,255,0.9)))",
            pointerEvents: "none", zIndex: 1, borderRadius: "4px 0 0 4px",
          }} />
        )}
        <Box
          ref={scrollRef}
          onScroll={checkScroll}
          sx={{
            fontFamily: "var(--font-oracle-sans), sans-serif",
            width: "100%",
            maxWidth: "100%",
            overflowX: "auto",
          }}
        >
          <WidgetV2Node node={tree} onSubmit={onSubmit} disabled={disabled} />
        </Box>
      </Box>
    </motion.div>
  );
}

export default memo(WidgetV2);
export { WidgetV2Node };
