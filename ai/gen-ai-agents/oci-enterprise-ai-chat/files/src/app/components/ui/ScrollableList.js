"use client";

import { Box, CircularProgress, IconButton, Skeleton, Stack, Typography } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import { RefreshCw, Trash2 } from "lucide-react";
import { memo, useCallback, useEffect, useRef, useState } from "react";
import { formatRelativeTime } from "../../utils/relativeTime";

const SKELETON_COUNT = 4;
const MIN_LOADING_MS = 400;

const scrollContainerSx = {
  height: "200px",
  width: "100%",
  overflowY: "auto",
  overflowX: "hidden",
  paddingBottom: "40px",
  "&::-webkit-scrollbar": {
    display: "none",
  },
  scrollbarWidth: "none",
};

const titleSx = {
  fontSize: "0.75rem",
  fontWeight: 500,
  color: "rgba(0, 0, 0, 0.6)",
  mb: 1,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
};

const itemTextSx = {
  fontSize: "0.9rem",
  fontWeight: 200,
  color: "rgba(0, 0, 0, 0.35)",
  lineHeight: 1.3,
  overflow: "hidden",
  textOverflow: "ellipsis",
  whiteSpace: "nowrap",
  minWidth: 0,
  flex: 1,
};

const itemContainerSx = {
  padding: "6px 0",
  cursor: "pointer",
  borderRadius: "4px",
  transition: "all 0.2s ease",
  display: "flex",
  alignItems: "center",
  justifyContent: "space-between",
  overflow: "hidden",
  gap: 1,
  position: "relative",
  "&:hover": {
    backgroundColor: "transparent",
    transform: "translateX(2px)",
  },
  "&:hover .delete-btn": { opacity: 1 },
  "&:hover .relative-date": { opacity: 0 },
};

const gradientBaseSx = {
  position: "absolute",
  left: 0,
  right: 0,
  height: "60px",
  pointerEvents: "none",
  zIndex: 1,
  transition: "opacity 0.3s ease",
};

const MAX_TITLE_LENGTH = 32;

const ListItem = memo(({ item, index, isInitialRender, onClick, onDelete, isActive, accentColor, isDarkBg }) => {
  const rawText = typeof item === 'string' ? item : item.title || item.id;
  const displayText = rawText.length > MAX_TITLE_LENGTH
    ? rawText.substring(0, MAX_TITLE_LENGTH) + '...'
    : rawText;
  const canDelete = typeof item === 'object' && item.id;
  const timestamp = typeof item === 'object' ? (item.updatedAt || item.createdAt) : null;
  const relativeLabel = formatRelativeTime(timestamp);

  const handleDelete = (e) => {
    e.stopPropagation();
    if (onDelete && canDelete) {
      onDelete(item, index);
    }
  };

  return (
    <motion.div
      layout
      initial={isInitialRender ? { opacity: 0, x: -10 } : false}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10, height: 0, marginBottom: 0 }}
      transition={{
        duration: 0.2,
        ease: [0.25, 0.46, 0.45, 0.94],
      }}
      style={{ overflow: "hidden", width: "100%" }}
    >
      <Box
        sx={itemContainerSx}
        onClick={() => onClick && onClick(item, index)}
      >
        <Typography
          sx={{
            ...itemTextSx,
            fontWeight: isActive ? 500 : 200,
            color: isActive ? accentColor : isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0, 0, 0, 0.35)",
          }}
          noWrap
        >
          {displayText}
        </Typography>
        {relativeLabel && (
          <Typography
            className="relative-date"
            sx={{
              fontSize: "0.7rem",
              fontWeight: 300,
              color: isDarkBg ? "rgba(255,255,255,0.3)" : "rgba(0, 0, 0, 0.3)",
              flexShrink: 0,
              ml: 0.5,
              transition: "opacity 0.2s ease",
            }}
          >
            {relativeLabel}
          </Typography>
        )}
        {canDelete && (
          <IconButton
            className="delete-btn"
            size="small"
            onClick={handleDelete}
            sx={{
              position: "absolute",
              right: 0,
              opacity: 0,
              transition: "opacity 0.2s ease",
              padding: "2px",
              color: "rgba(0, 0, 0, 0.3)",
              "&:hover": {
                color: "rgba(200, 0, 0, 0.6)",
                backgroundColor: "rgba(200, 0, 0, 0.08)",
              },
            }}
          >
            <Trash2 size={14} />
          </IconButton>
        )}
      </Box>
    </motion.div>
  );
});

ListItem.displayName = "ListItem";

export default memo(function ScrollableList({
  items,
  title,
  titleDelay = 0.8,
  onItemClick,
  onItemDelete,
  emptyMessage = "No conversations yet",
  activeId = null,
  onRefresh,
  initialLoading = false,
  bgColor = "white",
  accentColor = "#C74634",
  isDarkBg = false,
  hasMore = false,
  isLoadingMore = false,
  onLoadMore,
}) {
  const scrollRef = useRef(null);
  const [gradients, setGradients] = useState({ top: false, bottom: true });
  const [refreshing, setRefreshing] = useState(false);
  const rafRef = useRef(null);
  const isInitialRenderRef = useRef(true);

  // After first render, mark as not initial
  useEffect(() => {
    const timer = setTimeout(() => {
      isInitialRenderRef.current = false;
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  const handleRefresh = useCallback(async () => {
    if (refreshing || !onRefresh) return;
    setRefreshing(true);
    const start = Date.now();
    try {
      await onRefresh();
    } finally {
      const elapsed = Date.now() - start;
      const remaining = MIN_LOADING_MS - elapsed;
      if (remaining > 0) {
        setTimeout(() => setRefreshing(false), remaining);
      } else {
        setRefreshing(false);
      }
    }
  }, [onRefresh, refreshing]);

  const checkScrollPosition = useCallback(() => {
    if (refreshing) return;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);

    rafRef.current = requestAnimationFrame(() => {
      if (scrollRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
        setGradients({
          top: scrollTop > 0,
          bottom: scrollTop + clientHeight < scrollHeight,
        });
        // Infinite scroll: trigger load when within 40px of bottom
        if (hasMore && !isLoadingMore && onLoadMore && scrollTop + clientHeight >= scrollHeight - 40) {
          onLoadMore();
        }
      }
    });
  }, [refreshing, hasMore, isLoadingMore, onLoadMore]);

  useEffect(() => {
    checkScrollPosition();
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [items, refreshing, checkScrollPosition]);

  // Get stable key for item
  const getItemKey = (item, index) => {
    if (typeof item === 'string') return `str-${item}`;
    return item.id || `idx-${index}`;
  };

  return (
    <Box sx={{ mt: 2, overflow: "hidden", width: "100%" }}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          duration: 0.4,
          delay: titleDelay,
          ease: [0.25, 0.46, 0.45, 0.94],
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <Typography variant="body2" sx={{ ...titleSx, color: isDarkBg ? "rgba(255,255,255,0.5)" : titleSx.color }}>
            {title}
          </Typography>
          {onRefresh && (
            <IconButton
              size="small"
              onClick={handleRefresh}
              disabled={refreshing}
              sx={{
                p: 0.5,
                mb: 1,
                color: isDarkBg ? "rgba(255,255,255,0.4)" : "rgba(0, 0, 0, 0.3)",
                transition: "color 0.2s ease",
                "&:hover": {
                  color: isDarkBg ? "rgba(255,255,255,0.6)" : "rgba(0, 0, 0, 0.5)",
                  backgroundColor: isDarkBg ? "rgba(255,255,255,0.06)" : "rgba(0, 0, 0, 0.04)",
                },
                "&.Mui-disabled": {
                  color: isDarkBg ? "rgba(255,255,255,0.2)" : "rgba(0, 0, 0, 0.2)",
                },
              }}
            >
              <RefreshCw
                size={13}
                style={{
                  animation: refreshing ? "spin 0.8s linear infinite" : "none",
                }}
              />
            </IconButton>
          )}
        </Box>
      </motion.div>

      <Box sx={{ position: "relative", overflow: "hidden" }}>
        <Box
          ref={scrollRef}
          onScroll={checkScrollPosition}
          sx={scrollContainerSx}
        >
          {(refreshing || initialLoading) ? (
            <Stack spacing={0.8}>
              {Array.from({ length: SKELETON_COUNT }).map((_, i) => (
                <Box key={i} sx={{ padding: "6px 0" }}>
                  <Skeleton
                    variant="text"
                    animation="wave"
                    sx={{
                      fontSize: "0.9rem",
                      lineHeight: 1.3,
                      width: `${80 - i * 12}%`,
                      bgcolor: "rgba(0, 0, 0, 0.06)",
                    }}
                  />
                </Box>
              ))}
            </Stack>
          ) : items.length === 0 ? (
            <Typography
              sx={{
                fontSize: "0.85rem",
                fontWeight: 300,
                color: isDarkBg ? "rgba(255,255,255,0.3)" : "rgba(0, 0, 0, 0.25)",
                fontStyle: "italic",
                pt: 0,
                pb: 2,
              }}
            >
              {emptyMessage}
            </Typography>
          ) : (
            <Stack spacing={0.8}>
              <AnimatePresence mode="popLayout">
                {items.map((item, index) => (
                  <ListItem
                    key={getItemKey(item, index)}
                    item={item}
                    index={index}
                    isInitialRender={isInitialRenderRef.current}
                    onClick={onItemClick}
                    onDelete={onItemDelete}
                    isActive={activeId && item.id === activeId}
                    accentColor={accentColor}
                    isDarkBg={isDarkBg}
                  />
                ))}
              </AnimatePresence>
              {isLoadingMore && (
                <Box sx={{ display: "flex", justifyContent: "center", py: 1 }}>
                  <CircularProgress size={12} sx={{ color: isDarkBg ? "rgba(255,255,255,0.3)" : "rgba(0,0,0,0.3)" }} />
                </Box>
              )}
            </Stack>
          )}
        </Box>

        <Box
          sx={{
            ...gradientBaseSx,
            top: 0,
            background:
              `linear-gradient(to bottom, ${bgColor} 0%, transparent 100%)`,
            opacity: gradients.top ? 1 : 0,
          }}
        />
        <Box
          sx={{
            ...gradientBaseSx,
            bottom: 0,
            background:
              `linear-gradient(to top, ${bgColor} 0%, transparent 100%)`,
            opacity: gradients.bottom ? 1 : 0,
          }}
        />
      </Box>

      {/* Spin keyframes for refresh icon */}
      <style jsx global>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Box>
  );
});
