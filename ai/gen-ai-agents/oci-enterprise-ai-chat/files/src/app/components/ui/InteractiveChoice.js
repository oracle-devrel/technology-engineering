"use client";

import { Button, Stack, Typography } from "@mui/material";
import { ArrowForward } from "@mui/icons-material";
import { motion } from "framer-motion";

export default function InteractiveChoice({ interactiveData, onChoiceSelect }) {
  if (!interactiveData || interactiveData.inputType !== "choice") {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <Stack direction="column" spacing={1.5}>
        {interactiveData.title && (
          <Typography
            variant="body1"
            sx={{
              fontWeight: 500,
              color: "#333",
              mb: 1,
            }}
          >
            {interactiveData.title}
          </Typography>
        )}
        {interactiveData.options.map((option, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ 
              duration: 0.4, 
              delay: 0.2 + (index * 0.15),
              ease: "easeOut" 
            }}
          >
            <Button
              variant="outlined"
              onClick={() => onChoiceSelect(option.label)}
              sx={{
                justifyContent: "space-between",
                alignItems: "center",
                textAlign: "left",
                py: 1.5,
                px: 2,
                borderRadius: 2,
                textTransform: "none",
                fontSize: "1rem",
                fontWeight: 500,
                border: "1px solid #e0e0e0",
                color: "#333",
                backgroundColor: "white",
                "&:hover": {
                  backgroundColor: "#f5f5f5",
                  borderColor: "#d0d0d0",
                  transform: "translateY(-1px)",
                  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
                },
                transition: "all 0.2s ease-in-out",
              }}
              endIcon={<ArrowForward sx={{ fontSize: 18 }} />}
            >
              <Typography
                component="span"
                sx={{
                  fontSize: "1rem",
                  fontWeight: 500,
                  flex: 1,
                }}
              >
                {option.label}
              </Typography>
            </Button>
          </motion.div>
        ))}
      </Stack>
    </motion.div>
  );
}