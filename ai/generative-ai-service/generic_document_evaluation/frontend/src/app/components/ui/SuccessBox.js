import { CheckCircle } from "@mui/icons-material";
import { Box, Typography } from "@mui/material";

export default function SuccessBox({ children, sx = {} }) {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        p: 1.5,
        borderRadius: 3,
        bgcolor: "success.light",
        color: "success.contrastText",
        ...sx,
      }}
    >
      <CheckCircle fontSize="small" sx={{ mr: 1 }} />
      <Typography variant="body2" sx={{ color: "black" }}>
        {children}
      </Typography>
    </Box>
  );
}
