"use client";

import { Add, Delete, Edit } from "@mui/icons-material";
import { Avatar, Box, IconButton, Paper, Stack, Tooltip } from "@mui/material";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { useProject } from "../contexts/ProjectsContext";

const menuVariants = {
  initial: {
    x: -100,
    opacity: 0,
  },
  animate: {
    x: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 350,
      damping: 25,
      delay: 0.2,
    },
  },
};

export default function NavMenu({
  onAddProject,
  onEditProject,
  onDeleteProject,
}) {
  const router = useRouter();
  const { projects, switchProject, getCurrentProject } = useProject();
  const currentProject = getCurrentProject();

  const handleProjectSwitch = (projectId) => {
    switchProject(projectId);
    router.push(`/?projectId=${projectId}`);
  };

  return (
    <Paper
      component={motion.div}
      variants={menuVariants}
      initial="initial"
      animate="animate"
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        borderRadius: 6,
        backgroundColor: "white",
        boxShadow: "0 8px 24px -8px rgba(0, 0, 0, 0.15)",
        backdropFilter: "blur(10px)",
        border: "1px solid rgba(255, 255, 255, 0.2)",
        py: 1,
        px: 0.5,
      }}
    >
      <Stack spacing={1} alignItems="center">
        {projects.map((project) => (
          <Box
            key={project.id}
            sx={{
              position: "relative",
              display: "flex",
              justifyContent: "center",
            }}
          >
            <Tooltip
              title={
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 1,
                    alignItems: "flex-start",
                  }}
                >
                  <Box
                    sx={{
                      backgroundColor: "white",
                      color: "black",
                      padding: "6px 12px",
                      borderRadius: "12px",
                      textAlign: "center",
                      fontSize: "0.875rem",
                      boxShadow: "0 2px 8px rgba(0, 0, 0, 0.15)",
                    }}
                  >
                    {project.name}
                  </Box>
                  <Box
                    sx={{
                      display: "flex",
                      gap: 0.5,
                      justifyContent: "flex-start",
                    }}
                  >
                    <IconButton
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleProjectSwitch(project.id);
                        onEditProject(project);
                      }}
                      sx={{
                        width: 24,
                        height: 24,
                        backgroundColor: "white",
                        color: "black",
                        boxShadow: "0 2px 6px rgba(0, 0, 0, 0.12)",
                        "&:hover": {
                          backgroundColor: "rgba(255,255,255,0.8)",
                        },
                      }}
                    >
                      <Edit sx={{ fontSize: 14 }} />
                    </IconButton>
                    {project.id !== "default" && (
                      <IconButton
                        size="small"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteProject(project.id);
                        }}
                        sx={{
                          width: 24,
                          height: 24,
                          backgroundColor: "white",
                          color: "red",
                          boxShadow: "0 2px 6px rgba(0, 0, 0, 0.12)",
                          "&:hover": {
                            backgroundColor: "rgba(255,255,255,0.8)",
                          },
                        }}
                      >
                        <Delete sx={{ fontSize: 14 }} />
                      </IconButton>
                    )}
                  </Box>
                </Box>
              }
              placement="right"
              leaveDelay={100}
              componentsProps={{
                tooltip: {
                  sx: {
                    backgroundColor: "transparent",
                    padding: 0,
                    margin: 0,
                    "& .MuiTooltip-arrow": {
                      display: "none",
                    },
                  },
                },
              }}
            >
              <IconButton
                onClick={() => handleProjectSwitch(project.id)}
                sx={{
                  backgroundColor:
                    currentProject.id === project.id
                      ? project.mainColor
                      : "transparent",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  "&:hover": {
                    backgroundColor:
                      currentProject.id === project.id
                        ? project.mainColor
                        : "rgba(0, 0, 0, 0.04)",
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: 38,
                    height: 38,
                    fontSize: "0.85rem",
                    backgroundColor:
                      currentProject.id === project.id
                        ? "transparent"
                        : "rgba(0,0,0,0.1)",
                    color:
                      currentProject.id === project.id ? "white" : "inherit",
                  }}
                >
                  {project.name.charAt(0).toUpperCase()}
                </Avatar>
              </IconButton>
            </Tooltip>
          </Box>
        ))}
      </Stack>

      <Box
        sx={{
          width: "100%",
          height: "1px",
          bgcolor: "rgba(0,0,0,0.1)",
          mb: 0.5,
          mt: 1,
        }}
      />

      <Box sx={{ display: "flex", justifyContent: "center", width: "100%" }}>
        <Tooltip
          title={
            projects.length >= 8 ? "Maximum 8 projects allowed" : "Add Project"
          }
          placement="right"
        >
          <IconButton
            onClick={onAddProject}
            size="small"
            sx={{
              width: 36,
              height: 36,
              borderRadius: 2,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              "&:hover": {
                backgroundColor: "rgba(0, 0, 0, 0.04)",
              },
            }}
          >
            <Add size={16} />
          </IconButton>
        </Tooltip>
      </Box>
    </Paper>
  );
}
