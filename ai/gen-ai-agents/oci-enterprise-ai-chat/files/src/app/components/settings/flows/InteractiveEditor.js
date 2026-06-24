"use client";

import { Box, TextField, Typography, Button, IconButton } from "@mui/material";
import { Plus, Trash2 } from "lucide-react";

export default function InteractiveEditor({ 
  interactiveData, 
  onInteractiveDataChange, 
  onSave, 
  showSaveButton = true,
  autoFocus = false 
}) {
  const handleTitleChange = (title) => {
    onInteractiveDataChange({ ...interactiveData, title });
  };

  const handleOptionChange = (index, field, value) => {
    const newOptions = [...(interactiveData.options || [])];
    newOptions[index] = { ...newOptions[index], [field]: value };
    onInteractiveDataChange({ ...interactiveData, options: newOptions });
  };

  const handleAddOption = () => {
    const newOptions = [...(interactiveData.options || []), { label: '' }];
    onInteractiveDataChange({ ...interactiveData, options: newOptions });
  };

  const handleDeleteOption = (index) => {
    const newOptions = interactiveData.options.filter((_, i) => i !== index);
    onInteractiveDataChange({ ...interactiveData, options: newOptions });
  };

  return (
    <Box>
      <TextField
        value={interactiveData.title || ""}
        onChange={(e) => handleTitleChange(e.target.value)}
        label="Title (optional)"
        placeholder="Question or instruction for users..."
        variant="outlined"
        size="small"
        fullWidth
        sx={{ mb: 2 }}
        autoFocus={autoFocus}
      />
      <Typography variant="caption" sx={{ display: "block", mb: 1.5, color: "rgba(0, 0, 0, 0.6)" }}>
        User Options:
      </Typography>
      <Box sx={{ display: "flex", flexDirection: "column", gap: 2, mb: 2 }}>
        {(interactiveData.options || []).map((option, optIndex) => (
          <Box key={optIndex} sx={{ p: 2, border: "1px solid rgba(0, 0, 0, 0.1)", borderRadius: 1, backgroundColor: "rgba(0, 0, 0, 0.02)" }}>
            <Box sx={{ display: "flex", gap: 1, alignItems: "center" }}>
              <TextField
                value={option.label || ''}
                onChange={(e) => handleOptionChange(optIndex, "label", e.target.value)}
                variant="outlined"
                size="small"
                label="Button text"
                placeholder="What the user will click..."
                fullWidth
              />
              <IconButton
                size="small"
                onClick={() => handleDeleteOption(optIndex)}
                sx={{ color: "rgba(0, 0, 0, 0.4)" }}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          </Box>
        ))}
        <Button
          startIcon={<Plus size={16} />}
          onClick={handleAddOption}
          variant="outlined"
          size="small"
          sx={{ 
            alignSelf: "flex-start",
            textTransform: "none",
            color: "rgba(0, 0, 0, 0.6)",
            borderColor: "rgba(0, 0, 0, 0.2)"
          }}
        >
          Add option
        </Button>
      </Box>
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