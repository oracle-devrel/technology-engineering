"use client";

import { AttachFile, Close } from "@mui/icons-material";
import { Box, IconButton, Typography } from "@mui/material";
import { useRef, useState } from "react";

const DropZone = ({
  onDrop,
  onFileSelect,
  accept = "*/*",
  multiple = false,
  placeholder = "Drop files here or click to attach",
  description = "Up to 5 documents",
  dragPlaceholder = "Drop files here",
  icon: CustomIcon = AttachFile,
  selectedFile = null,
  onFileRemove,
  disabled = false,
  showFileCount = false,
  maxFiles = 5,
  currentFileCount = 0,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    if (showFileCount) {
      const remainingSlots = maxFiles - currentFileCount;
      const filesToAdd = files.slice(0, remainingSlots);
      if (filesToAdd.length > 0) {
        onDrop && onDrop(filesToAdd);
      }
    } else {
      onDrop && onDrop(files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (disabled) return;

    dragCounter.current++;
    if (showFileCount && currentFileCount < maxFiles) {
      setIsDragging(true);
    } else if (!showFileCount) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (files.length > 0) {
      onFileSelect && onFileSelect(files);
    }
    e.target.value = "";
  };

  const handleClick = () => {
    if (!disabled && !selectedFile) {
      if (showFileCount && currentFileCount >= maxFiles) return;
      fileInputRef.current?.click();
    }
  };

  return (
    <Box
      sx={{
        mb: 2,
        p: 2,
        background: (theme) => theme.palette.background.paper,
        borderRadius: "16px",
        border: (theme) => `1.5px dashed ${theme.palette.divider}`,
        borderRadius: "16px",
        transition: "all 0.3s ease",
        "&:hover": {
          border: (theme) => `2px dashed ${theme.palette.divider}`,
        },
      }}
    >
      <input
        ref={fileInputRef}
        type="file"
        multiple={multiple}
        accept={accept}
        style={{ display: "none" }}
        onChange={handleFileChange}
      />

      <Box
        onClick={handleClick}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
          minHeight:
            selectedFile || (showFileCount && currentFileCount > 0)
              ? "50px"
              : "120px",
          cursor:
            disabled ||
            selectedFile ||
            (showFileCount && currentFileCount >= maxFiles)
              ? "default"
              : "pointer",
          opacity:
            disabled || (showFileCount && currentFileCount >= maxFiles)
              ? 0.5
              : 1,
          transition: "all 0.3s ease",
          borderRadius: "12px",
          border: isDragging
            ? "2px dashed #34C759"
            : (theme) => `1.5px dashed ${theme.palette.divider}`,
          background: isDragging
            ? "rgba(52, 199, 89, 0.05)"
            : "transparent",
          transform: "scale(1)",
          p: selectedFile ? 1 : 2,
          mb: selectedFile ? 1 : 0,
          "&:hover":
            !disabled &&
            !selectedFile &&
            !(showFileCount && currentFileCount >= maxFiles)
              ? {
                  background: (theme) => theme.palette.mode === 'light' ? "rgba(0, 0, 0, 0.05)" : "rgba(0, 0, 0, 0.1)",
                }
              : {},
        }}
      >
        {selectedFile ? (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              width: "100%",
            }}
          >
            <Typography
              variant="body2"
              sx={{ color: (theme) => theme.palette.text.primary }}
            >
              {selectedFile.name}
            </Typography>
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                onFileRemove && onFileRemove();
              }}
              sx={{
                color: (theme) => theme.palette.grey[700],
                "&:hover": {
                  color: (theme) => theme.palette.error.main,
                  background: "rgba(255, 69, 58, 0.1)",
                },
              }}
            >
              <Close fontSize="small" />
            </IconButton>
          </Box>
        ) : (
          <>
            {showFileCount && currentFileCount === 0 ? (
              <>
                <CustomIcon
                  sx={{
                    fontSize: 28,
                    color: isDragging
                      ? "#34C759"
                      : (theme) => theme.palette.text.secondary,
                    mb: 0.5,
                    transition: "all 0.3s ease",
                  }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    color: isDragging
                      ? "#34C759"
                      : (theme) => theme.palette.text.secondary,
                    fontWeight: 500,
                    transition: "all 0.3s ease",
                  }}
                >
                  {isDragging ? dragPlaceholder : placeholder}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.disabled,
                    mt: 0.5,
                  }}
                >
                  {description}
                </Typography>
              </>
            ) : showFileCount && currentFileCount > 0 ? (
              <Typography
                variant="caption"
                sx={{ color: (theme) => theme.palette.text.secondary }}
              >
                {maxFiles - currentFileCount} more file
                {maxFiles - currentFileCount !== 1 ? "s" : ""} can be added
              </Typography>
            ) : (
              <>
                <CustomIcon
                  sx={{
                    fontSize: 28,
                    color: isDragging
                      ? "#34C759"
                      : (theme) => theme.palette.text.secondary,
                    mb: 0.5,
                    transition: "all 0.3s ease",
                  }}
                />
                <Typography
                  variant="body2"
                  sx={{
                    color: isDragging
                      ? "#34C759"
                      : (theme) => theme.palette.text.secondary,
                    fontWeight: 500,
                    transition: "all 0.3s ease",
                  }}
                >
                  {isDragging ? dragPlaceholder : placeholder}
                </Typography>
                <Typography
                  variant="caption"
                  sx={{
                    color: (theme) => theme.palette.text.disabled,
                    mt: 0.5,
                  }}
                >
                  {description}
                </Typography>
              </>
            )}
          </>
        )}
      </Box>
    </Box>
  );
};

export default DropZone;
