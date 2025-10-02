"use client";

import { APP_CONFIG } from "@/app/config/app";
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
  FormLabel,
  IconButton,
  Radio,
  RadioGroup,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import ChatPreview from "../Chat/ChatPreview";

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
    logoUrl: APP_CONFIG.defaults.logoUrl,
    mainColor: APP_CONFIG.defaults.color,
    backgroundColor: APP_CONFIG.defaults.backgroundColor,
    backgroundImage: APP_CONFIG.defaults.image,
    backgroundType: "image",
    speechProvider: APP_CONFIG.defaults.speechProvider,
  });
  const [errors, setErrors] = useState({});
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  useEffect(() => {
    if (project) {
      setFormData({
        name: project.name,
        logoUrl: project.logoUrl || APP_CONFIG.defaults.logoUrl,
        mainColor: project.mainColor || APP_CONFIG.defaults.color,
        backgroundColor:
          project.backgroundColor || APP_CONFIG.defaults.backgroundColor,
        backgroundImage: project.backgroundImage || APP_CONFIG.defaults.image,
        backgroundType: "image",
        speechProvider:
          project.speechProvider || APP_CONFIG.defaults.speechProvider,
      });

      if (
        !APP_CONFIG.availableColors.includes(
          project.mainColor || APP_CONFIG.defaults.color
        )
      ) {
        setFormData((prev) => ({
          ...prev,
          mainColor: APP_CONFIG.defaults.color,
        }));
      }
    } else {
      setFormData({
        name: "",
        logoUrl: APP_CONFIG.defaults.logoUrl,
        mainColor: APP_CONFIG.defaults.color,
        backgroundColor: APP_CONFIG.defaults.backgroundColor,
        backgroundImage: APP_CONFIG.defaults.image,
        backgroundType: "image",
        speechProvider: APP_CONFIG.defaults.speechProvider,
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
                    {APP_CONFIG.availableColors.map((color) => (
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
                    }}
                  >
                    {APP_CONFIG.availableImages.map((image, index) => (
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

                <FormControl component="fieldset">
                  <FormLabel component="legend">
                    <Typography variant="subtitle2">Speech Service</Typography>
                  </FormLabel>
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
