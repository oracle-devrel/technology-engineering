"use client";

import { Box, TextField, IconButton } from "@mui/material";
import { Plus } from "lucide-react";

export default function TextEditor({ 
  content, 
  onContentChange, 
  onSave, 
  showSaveButton = true,
  autoFocus = false 
}) {
  return (
    <Box sx={{ display: "flex", gap: 1, alignItems: "flex-start" }}>
      <TextField
        value={content}
        onChange={(e) => onContentChange(e.target.value)}
        placeholder="Message content..."
        variant="outlined"
        size="small"
        fullWidth
        multiline
        rows={2}
        autoFocus={autoFocus}
      />
      {showSaveButton && (
        <IconButton
          onClick={onSave}
          sx={{ 
            backgroundColor: "#1a1a1a",
            color: "white",
            "&:hover": { 
              backgroundColor: "#333" 
            },
            mt: 0.5
          }}
          size="small"
        >
          <Plus size={18} />
        </IconButton>
      )}
    </Box>
  );
}