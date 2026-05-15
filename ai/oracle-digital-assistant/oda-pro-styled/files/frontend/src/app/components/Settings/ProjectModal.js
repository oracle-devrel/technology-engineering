"use client";

import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import SaveIcon from "@mui/icons-material/Save";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  FormControl,
  FormControlLabel,
  IconButton,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import ChatPreview from "../Chat/ChatPreview";

const PRESET_COLORS = [
  "#2E2E2E",
  "#2979FF",
  "#34C759",
  "#FF9500",
  "#FF375F",
  "#AF52DE",
  "#8E8E93",
  "#FFD60A",
];

const BACKGROUND_IMAGES = [
  "/background.png",
  "/backgrounds/radial-sky-blue.jpg",
  "/backgrounds/sonoma.jpg",
  "/backgrounds/imac-blue.jpg",
  "/backgrounds/imac-green.jpg",
  "/backgrounds/imac-orange.jpg",
  "/backgrounds/imac-pink.jpg",
  "/backgrounds/imac-purple.jpg",
  "/backgrounds/imac-silver.jpg",
  "/backgrounds/imac-yellow.jpg",
];

export default function ProjectModal({
  open,
  onClose,
  project = null,
  onSave,
  onDelete,
}) {
  const isNewProject = !project;
  const [formData, setFormData] = useState({
    name: "",
    logoUrl: "",
    mainColor: "#007AFF",
    backgroundColor: "#F5F5F5",
    backgroundImage: "/background.png",
    backgroundType: "image",
    speechProvider: "browser",
  });
  const [errors, setErrors] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        logoUrl: project.logoUrl || "",
        mainColor: project.mainColor || "#007AFF",
        backgroundColor: project.backgroundColor || "#F5F5F5",
        backgroundImage: project.backgroundImage || "/background.png",
        backgroundType: "image",
        speechProvider: project.speechProvider || "browser",
      });

      if (!PRESET_COLORS.includes(project.mainColor || "#007AFF")) {
        setFormData((prev) => ({ ...prev, mainColor: "#007AFF" }));
      }
    } else {
      setFormData({
        name: "",
        logoUrl: "",
        mainColor: "#007AFF",
        backgroundColor: "#F5F5F5",
        backgroundImage: "/background.png",
        backgroundType: "image",
        speechProvider: "browser",
      });
    }
    setErrors({});
  }, [project, open]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }
  };

  const handleMainColorSelect = (colorValue) => {
    setFormData((prev) => ({
      ...prev,
      mainColor: colorValue,
    }));
  };

  const handleImageSelect = (imageUrl) => {
    setFormData((prev) => ({
      ...prev,
      backgroundImage: imageUrl,
      backgroundType: "image",
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }

    if (formData.logoUrl && !isValidUrl(formData.logoUrl)) {
      newErrors.logoUrl = "Please enter a valid URL";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const isValidUrl = (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSave = () => {
    if (!validateForm()) return;
    onSave(formData);
    onClose();
  };

  const handleDelete = () => {
    onDelete(project.id);
    setDeleteDialogOpen(false);
    onClose();
  };

  const handleClose = () => {
    onClose();
    setDeleteDialogOpen(false);
  };

  return (
    <>
      <Box
        sx={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          display: open ? "flex" : "none",
          alignItems: "stretch",
          justifyContent: "center",
          zIndex: 9999,
          backgroundColor: "rgba(0, 0, 0, 0.8)",
          p: 6,
          backdropFilter: "blur(14px)",
        }}
        onClick={handleClose}
      >
        <Box
          sx={{
            display: "flex",
            gap: 2,
            width: "100%",
            height: "100%",
            justifyContent: "center",
            alignItems: "stretch",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <Box
            sx={{
              backgroundColor: "white",
              borderRadius: 2,
              boxShadow: 24,
              width: "400px",
              flexShrink: 0,
              display: "flex",
              flexDirection: "column",
              overflow: "hidden",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                p: 3,
                borderBottom: "1px solid rgba(0, 0, 0, 0.12)",
              }}
            >
              <Typography variant="h6">
                {isNewProject ? "Create New Project" : "Edit Project"}
              </Typography>
              <IconButton onClick={handleClose} size="small">
                <CloseIcon />
              </IconButton>
            </Box>

            <Box sx={{ p: 3, flex: 1, overflow: "auto" }}>
              <Stack spacing={2}>
                <TextField
                  label="Project Name"
                  name="name"
                  size="small"
                  value={formData.name}
                  onChange={handleInputChange}
                  fullWidth
                  error={!!errors.name}
                  helperText={errors.name}
                />

                <TextField
                  label="Logo URL (optional)"
                  name="logoUrl"
                  size="small"
                  value={formData.logoUrl}
                  onChange={handleInputChange}
                  fullWidth
                  error={!!errors.logoUrl}
                  helperText={errors.logoUrl}
                />

                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 2 }}>
                    Main Color
                  </Typography>

                  <Box
                    sx={{
                      display: "grid",
                      gridTemplateColumns: "repeat(6, 1fr)",
                      gap: 1,
                      mb: 3,
                    }}
                  >
                    {PRESET_COLORS.map((color) => (
                      <Box
                        key={color}
                        onClick={() => handleMainColorSelect(color)}
                        sx={{
                          width: 40,
                          height: 40,
                          bgcolor: color,
                          borderRadius: 1,
                          cursor: "pointer",
                          border: "1px solid rgba(0, 0, 0, 0.1)",
                          transform:
                            formData.mainColor === color
                              ? "scale(1.2)"
                              : "scale(1)",
                          transition: "transform 0.15s ease-out",
                          "&:hover": {
                            transform:
                              formData.mainColor === color
                                ? "scale(1.2)"
                                : "scale(1.05)",
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Box>

                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 2 }}>
                    Background
                  </Typography>

                  <Box
                    sx={{
                      display: "flex",
                      flexWrap: "wrap",
                      gap: 1,
                      mb: 3,
                    }}
                  >
                    {BACKGROUND_IMAGES.map((image, index) => (
                      <Box
                        key={index}
                        onClick={() => handleImageSelect(image)}
                        sx={{
                          width: 50,
                          height: 50,
                          borderRadius: 1,
                          cursor: "pointer",
                          backgroundImage: `url(${image})`,
                          backgroundSize: "cover",
                          backgroundPosition: "center",
                          transform:
                            formData.backgroundType === "image" &&
                            formData.backgroundImage === image
                              ? "scale(1.2)"
                              : "scale(1)",
                          transition: "transform 0.15s ease-out",
                          "&:hover": {
                            transform:
                              formData.backgroundType === "image" &&
                              formData.backgroundImage === image
                                ? "scale(1.2)"
                                : "scale(1.05)",
                          },
                        }}
                      />
                    ))}
                  </Box>
                </Box>

                <Box>
                  <Typography variant="subtitle2" sx={{ mb: 2 }}>
                    Speech Service
                  </Typography>
                  <FormControl component="fieldset">
                    <RadioGroup
                      name="speechProvider"
                      value={formData.speechProvider}
                      onChange={handleInputChange}
                      row
                    >
                      <FormControlLabel
                        value="browser"
                        control={<Radio size="small" />}
                        label="Browser"
                      />
                      <FormControlLabel
                        value="oracle"
                        control={<Radio size="small" />}
                        label="Oracle"
                      />
                    </RadioGroup>
                  </FormControl>
                </Box>
              </Stack>
            </Box>

            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                p: 3,
                borderTop: "1px solid rgba(0, 0, 0, 0.12)",
              }}
            >
              {!isNewProject && project?.id !== "default" && (
                <Button
                  variant="text"
                  color="error"
                  startIcon={<DeleteIcon />}
                  onClick={() => setDeleteDialogOpen(true)}
                >
                  Delete
                </Button>
              )}
              <Box sx={{ flexGrow: 1 }} />
              <Stack direction="row" spacing={1}>
                <Button variant="outlined" onClick={handleClose}>
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSave}
                >
                  {isNewProject ? "Create" : "Save changes"}
                </Button>
              </Stack>
            </Box>
          </Box>

          <Box
            sx={{
              borderRadius: 2,
              flex: 1,
              display: "flex",
              flexDirection: "column",
              minWidth: 0,
            }}
          >
            <ChatPreview projectData={formData} />
          </Box>
        </Box>
      </Box>

      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Project?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this project? This action cannot be
            undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleDelete} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
