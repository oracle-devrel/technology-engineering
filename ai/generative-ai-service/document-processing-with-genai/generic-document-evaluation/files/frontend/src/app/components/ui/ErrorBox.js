import { Error as ErrorIcon } from "@mui/icons-material";
import { Box, Typography } from "@mui/material";

export default function ErrorBox({ children, sx = {} }) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        p: 1.5,
        borderRadius: 3,
        bgcolor: "error.light",
        color: "error.contrastText",
        ...sx,
      }}
    >
      <ErrorIcon fontSize="small" sx={{ mr: 1 }} />
      <Typography variant="body2" sx={{ color: "black" }}>
        {children}
      </Typography>
    </Box>
  );
}
