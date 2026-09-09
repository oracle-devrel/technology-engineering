"use client";

import { Box, TextField, ToggleButton, ToggleButtonGroup, IconButton } from "@mui/material";
import { Plus } from "lucide-react";

export default function ChipEditor({ 
  chipData, 
  onChipDataChange, 
  onSave, 
  showSaveButton = true,
  autoFocus = false 
}) {
  const handleChange = (field, value) => {
    onChipDataChange({ ...chipData, [field]: value });
  };

  return (
    <Box>
      <Box sx={{ display: "flex", gap: 2, mb: 2 }}>
        <TextField
          value={chipData.label || ""}
          onChange={(e) => handleChange("label", e.target.value)}
          label="Label"
          placeholder="What appears in the chip"
          variant="outlined"
          size="small"
          sx={{ flex: 1 }}
          autoFocus={autoFocus}
        />
        <ToggleButtonGroup
          value={chipData.status || "info"}
          exclusive
          onChange={(e, newStatus) => {
            if (newStatus) handleChange("status", newStatus);
          }}
          size="small"
        >
          <ToggleButton value="info" sx={{ px: 2 }}>Info</ToggleButton>
          <ToggleButton value="warning" sx={{ px: 2 }}>Warning</ToggleButton>
          <ToggleButton value="success" sx={{ px: 2 }}>Success</ToggleButton>
        </ToggleButtonGroup>
      </Box>
      <TextField
        value={chipData.content || ""}
        onChange={(e) => handleChange("content", e.target.value)}
        label="Content"
        placeholder="Detailed explanation that shows when clicked..."
        variant="outlined"
        size="small"
        fullWidth
        multiline
        rows={3}
        sx={{ mb: 2 }}
      />
      {showSaveButton && (
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
          <IconButton
            onClick={onSave}
            sx={{ 
              backgroundColor: "#1a1a1a",
              color: "white",
              "&:hover": { 
                backgroundColor: "#333" 
              }
            }}
          >
            <Plus size={18} />
          </IconButton>
        </Box>
      )}
    </Box>
  );
}