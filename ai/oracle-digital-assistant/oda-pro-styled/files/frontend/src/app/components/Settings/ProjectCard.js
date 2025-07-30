"use client";

import { useProject } from "@/app/contexts/ProjectsContext";
import { Box, Card, Typography, alpha, useTheme } from "@mui/material";
import { motion } from "framer-motion";
import { MessageSquare, Settings } from "lucide-react";
import { useRouter } from "next/navigation";

export default function ProjectCard({ project, onEdit }) {
  const router = useRouter();
  const { switchProject } = useProject();
  const theme = useTheme();

  const handleEditClick = (e) => {
    e.stopPropagation();
    onEdit(project);
  };

  const handleGoToChat = (e) => {
    e.stopPropagation();
    switchProject(project.id);
    router.push(`/?projectId=${project.id}`);
  };

  return (
    <Card
      component={motion.div}
      onClick={handleEditClick}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{ type: "spring", stiffness: 300 }}
      sx={{
        display: "flex",
        flexDirection: "column",
        borderRadius: "16px",
        overflow: "hidden",
        cursor: "pointer",
        width: 300,
        height: 220,
        boxShadow: `0 8px 20px ${alpha(theme.palette.primary.main, 0.08)}`,
        position: "relative",
        backgroundColor: "rgba(255, 255, 255, 0.8)",
        backdropFilter: "blur(8px)",
        border: `1px solid ${alpha("#fff", 0.2)}`,
        borderRadius: (theme) => theme.spacing(4, 4, 4, 1),
      }}
    >
      {/* Settings icon at top-right */}
      <Box
        onClick={handleEditClick}
        sx={{
          position: "absolute",
          top: 12,
          right: 12,
          width: 36,
          height: 36,
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: "pointer",
          zIndex: 3,
          transition: "all 0.2s ease",
          "&:hover": {
            backgroundColor: alpha(theme.palette.primary.main, 0.12),
          },
        }}
      >
        <Settings size={20} />
      </Box>

      <Box
        sx={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          opacity: 0.06,
          background: `
            linear-gradient(to right, #000 1px, transparent 1px) 0 0 / 20px 20px,
            linear-gradient(to bottom, #000 1px, transparent 1px) 0 0 / 20px 20px
          `,
          zIndex: 0,
          mask: "radial-gradient(circle at center, rgba(0,0,0,0.8) 40%, rgba(0,0,0,0.4) 70%, transparent 95%)",
        }}
      />
      <Box
        sx={{
          padding: 3,
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-start",
          position: "relative",
          zIndex: 2,
          height: "100%",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 56,
            height: 56,
            borderRadius: "12px",
            backgroundColor: project.logoUrl
              ? "rgba(255, 255, 255, 0.9)"
              : alpha(theme.palette.primary.main, 0.12),
            marginBottom: 2,
          }}
        >
          {project.logoUrl ? (
            <Box
              component="img"
              src={project.logoUrl || "/oda-logo.png"}
              alt={project.name}
              sx={{ width: 32, height: 32, objectFit: "contain" }}
            />
          ) : (
            <Typography
              variant="h5"
              sx={{
                fontWeight: 700,
                color: theme.palette.primary.main,
                letterSpacing: "-0.02em",
              }}
            >
              {project.name.charAt(0).toUpperCase()}
            </Typography>
          )}
        </Box>
        <Typography
          variant="subtitle1"
          sx={{
            fontWeight: 600,
            fontSize: "1rem",
            color: "text.primary",
            width: "100%",
            mb: 0.5,
          }}
        >
          {project.name}
        </Typography>

        {/* Chat button at bottom-right */}
        <Box
          sx={{
            marginTop: "auto",
            display: "flex",
            justifyContent: "flex-end",
            width: "100%",
            alignItems: "center",
          }}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1,
              backgroundColor: alpha(theme.palette.primary.main, 0.15),
              color: theme.palette.primary.main,
              padding: "8px 16px",
              borderRadius: "8px",
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s ease",
              "&:hover": {
                backgroundColor: alpha(theme.palette.primary.main, 0.25),
              },
            }}
            onClick={handleGoToChat}
          >
            <MessageSquare size={16} />
            <span>Go to chat</span>
          </Box>
        </Box>
      </Box>
    </Card>
  );
}
