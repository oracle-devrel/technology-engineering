import {
  Circle,
  ErrorOutline,
  ExpandLess,
  ExpandMore,
  InfoOutlined,
  LightbulbOutlined,
  NewReleasesOutlined,
  Shield,
  WarningAmberOutlined,
} from "@mui/icons-material";
import {
  Box,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import { motion } from "framer-motion";
import { useState } from "react";

export default function CollapsibleList({ title, items, severity = "error" }) {
  const [expanded, setExpanded] = useState(true);

  if (!items || items.length === 0) return null;

  const getSeverityStyle = () => {
    switch (severity) {
      case "critical":
        return {
          color: (theme) => theme.palette.error.main,
          iconColor: (theme) => theme.palette.error.main,
          bgColor: (theme) => `${theme.palette.error.main}14`,
          borderColor: (theme) => `${theme.palette.error.main}26`,
        };
      case "error":
        return {
          color: (theme) => theme.palette.error.main,
          iconColor: (theme) => theme.palette.error.main,
          bgColor: (theme) => `${theme.palette.error.main}0F`,
          borderColor: (theme) => `${theme.palette.error.main}1F`,
        };
      case "high":
        return {
          color: (theme) => theme.palette.warning.main,
          iconColor: (theme) => theme.palette.warning.main,
          bgColor: (theme) => `${theme.palette.warning.main}0F`,
          borderColor: (theme) => `${theme.palette.warning.main}1F`,
        };
      case "medium":
        return {
          color: (theme) => theme.palette.warning.light,
          iconColor: (theme) => theme.palette.warning.light,
          bgColor: (theme) => `${theme.palette.warning.light}0F`,
          borderColor: (theme) => `${theme.palette.warning.light}1F`,
        };
      case "warning":
        return {
          color: (theme) => theme.palette.warning.main,
          iconColor: (theme) => theme.palette.warning.main,
          bgColor: (theme) => `${theme.palette.warning.main}0F`,
          borderColor: (theme) => `${theme.palette.warning.main}1F`,
        };
      case "info":
      case "low":
        return {
          color: (theme) => theme.palette.primary.main,
          iconColor: (theme) => theme.palette.primary.main,
          bgColor: (theme) => `${theme.palette.primary.main}0D`,
          borderColor: (theme) => `${theme.palette.primary.main}1F`,
        };
      case "success":
        return {
          color: (theme) => theme.palette.success.main,
          iconColor: (theme) => theme.palette.success.main,
          bgColor: (theme) => `${theme.palette.success.main}0D`,
          borderColor: (theme) => `${theme.palette.success.main}1F`,
        };
      default:
        return {
          color: (theme) => theme.palette.grey[400],
          iconColor: (theme) => theme.palette.grey[400],
          bgColor: (theme) => `${theme.palette.grey[400]}0D`,
          borderColor: (theme) => `${theme.palette.grey[400]}1F`,
        };
    }
  };

  const getIcon = () => {
    const style = getSeverityStyle();
    const iconSize = 14;

    const iconWrapper = {
      display: "flex",
      justifyContent: "center",
      alignItems: "center",
      width: 22,
      height: 22,
      borderRadius: 11,
      background: "linear-gradient(145deg, #e6e6e6, #ffffff)",
      boxShadow: "3px 3px 6px #d1d1d1, -3px -3px 6px #ffffff",
      position: "relative",
      overflow: "visible",
      transition: "all 0.3s ease",
    };

    switch (severity) {
      case "critical":
        return (
          <Box sx={iconWrapper}>
            <NewReleasesOutlined
              sx={{ fontSize: iconSize, color: style.iconColor }}
            />
          </Box>
        );
      case "error":
        return (
          <Box sx={iconWrapper}>
            <ErrorOutline sx={{ fontSize: iconSize, color: style.iconColor }} />
          </Box>
        );
      case "high":
        return (
          <Box sx={iconWrapper}>
            <ErrorOutline sx={{ fontSize: iconSize, color: "#FF9F0A" }} />
          </Box>
        );
      case "medium":
        return (
          <Box sx={iconWrapper}>
            <WarningAmberOutlined
              sx={{ fontSize: iconSize, color: style.iconColor }}
            />
          </Box>
        );
      case "warning":
        return (
          <Box sx={iconWrapper}>
            <LightbulbOutlined
              sx={{ fontSize: iconSize, color: style.iconColor }}
            />
          </Box>
        );
      case "low":
      case "info":
        return (
          <Box sx={iconWrapper}>
            <InfoOutlined sx={{ fontSize: iconSize, color: style.iconColor }} />
          </Box>
        );
      case "success":
        return (
          <Box sx={iconWrapper}>
            <Shield sx={{ fontSize: iconSize, color: style.iconColor }} />
          </Box>
        );
      default:
        return (
          <Box sx={iconWrapper}>
            <InfoOutlined sx={{ fontSize: iconSize, color: style.iconColor }} />
          </Box>
        );
    }
  };

  const style = getSeverityStyle();

  const getItemDecoratorIcon = () => {
    return <Circle sx={{ fontSize: 6, color: style.color, opacity: 0.6 }} />;
  };

  const containerVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.3,
        when: "beforeChildren",
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -5 },
    visible: { opacity: 1, x: 0 },
  };

  return (
    <Box
      component={motion.div}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <Box
        sx={{
          borderRadius: 3,
          background: expanded ? "rgba(250,250,250,0.8)" : "transparent",
          // boxShadow: expanded
          //   ? "0 2px 10px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.01)"
          //   : "none",
          backdropFilter: expanded ? "blur(10px)" : "none",
          transition: "all 0.3s cubic-bezier(0.16,1,0.3,1)",
          overflow: "hidden",
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            p: 1.5,
            cursor: "pointer",
            transition: "background-color 0.2s ease",
          }}
          onClick={() => setExpanded(!expanded)}
        >
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 1.5,
            }}
          >
            {getIcon()}
            <Typography
              variant="subtitle2"
              sx={{
                fontSize: 12,
                fontWeight: 600,
                color: "rgba(0, 0, 0, 0.85)",
                letterSpacing: "-0.01em",
              }}
            >
              {title}{" "}
              <Box
                component="span"
                sx={{ fontSize: 11, fontWeight: 500, opacity: 0.7 }}
              >
                ({items.length})
              </Box>
            </Typography>
          </Box>
          <Box
            sx={{
              color: "rgba(0, 0, 0, 0.55)",
              opacity: 0.8,
              transition: "transform 0.2s ease",
              transform: expanded ? "rotate(0deg)" : "rotate(-90deg)",
            }}
          >
            {expanded ? <ExpandLess /> : <ExpandMore />}
          </Box>
        </Box>

        <Collapse in={expanded}>
          <List
            dense
            disablePadding
            component={motion.ul}
            sx={{
              mx: 1.5,
              mb: 1.5,
              mt: 0,
              borderRadius: 1.5,
              background: "rgba(255, 255, 255, 0.6)",
              backdropFilter: "blur(5px)",
              boxShadow: "inset 0 0 0 1px rgba(0, 0, 0, 0.02)",
              overflow: "hidden",
            }}
          >
            {items.map((item, i) => (
              <ListItem
                key={i}
                component={motion.li}
                variants={itemVariants}
                sx={{
                  py: 0.75,
                  px: 1,
                  borderBottom:
                    i < items.length - 1
                      ? "1px solid rgba(0,0,0,0.03)"
                      : "none",
                  "&:hover": {
                    backgroundColor: "rgba(0,0,0,0.01)",
                  },
                  transition: "background-color 0.2s ease",
                }}
              >
                <ListItemIcon sx={{ minWidth: 28 }}>
                  {getItemDecoratorIcon()}
                </ListItemIcon>
                <ListItemText
                  primary={item}
                  primaryTypographyProps={{
                    variant: "body2",
                    fontSize: 12,
                    fontWeight: 400,
                    lineHeight: 1.5,
                    color: "rgba(0, 0, 0, 0.75)",
                  }}
                />
              </ListItem>
            ))}
          </List>
        </Collapse>
      </Box>
    </Box>
  );
}
