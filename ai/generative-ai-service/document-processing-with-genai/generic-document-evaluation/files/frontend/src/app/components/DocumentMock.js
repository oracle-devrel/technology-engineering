import { Box, Typography, useTheme } from "@mui/material";
import { motion } from "framer-motion";

const MOCK_CONTENT = `Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam
          vehicula risus non lorem elementum, sed placerat orci suscipit.
          Vestibulum ante ipsum primis in faucibus orci luctus et ultrices
          posuere cubilia curae; Vivamus sit amet semper urna. Sed euismod,
          ipsum at facilisis pulvinar, mauris urna hendrerit arcu, id
          sollicitudin dolor lectus vitae ligula. Duis auctor nisi vel ex
          tincidunt, vitae scelerisque erat tincidunt.`;

export default function DocumentMock({ content, type = "Mock" }) {
  const theme = useTheme();
  const cardVariants = {
    initial: { scale: 0.5, opacity: 0 },
    animate: { scale: 1, opacity: 1, rotate: -1 },
  };
  const springConfig = { type: "spring", stiffness: 200, damping: 25 };

  return (
    <Box sx={{ display: "flex", justifyContent: "center" }}>
      <motion.div
        initial="initial"
        animate="animate"
        variants={cardVariants}
        transition={springConfig}
        whileHover={{ rotate: 2, transition: springConfig }}
        style={{
          width: "110px",
          height: "150px",
          background: (theme) => theme.palette.background.default,
          borderRadius: 8,
          boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
          padding: "16px",
          overflow: "hidden",
          cursor: "pointer",
          position: "relative",
        }}
      >
        <Box
          sx={{
            position: "absolute",
            bottom: 6,
            right: 6,
            px: 1.5,
            py: 0.5,
            backgroundColor: theme.palette.primary.main,
            color: theme.palette.primary.contrastText,
            fontSize: "10px",
            fontWeight: 600,
            textTransform: "uppercase",
            borderRadius: 1.5,
          }}
        >
          {type}
        </Box>
        <Typography
          variant="body2"
          sx={{
            mt: 1.5,
            fontFamily: "Georgia, serif",
            fontSize: "11px",
            lineHeight: 1.4,
            color: (theme) => theme.palette.grey[800],
            display: "-webkit-box",
            WebkitLineClamp: 12,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {content || MOCK_CONTENT}
        </Typography>
      </motion.div>
    </Box>
  );
}
