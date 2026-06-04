"use client";

import { Plus, Trash2 } from "lucide-react";
import { Box, IconButton, List, ListItem, ListItemText, Typography, Button, Switch, FormControlLabel } from "@mui/material";
import { useRouter } from "next/navigation";

export default function FlowsTab({ flows, onDeleteFlow, onToggleFlow }) {
  const router = useRouter();

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
        <Typography
          variant="h6"
          sx={{
            fontSize: "1.1rem",
            fontWeight: 400,
            color: "var(--dm-text, #1a1a1a)",
          }}
        >
          Flows ({flows.length})
        </Typography>
        <Button
          startIcon={<Plus size={16} />}
          onClick={() => router.push('/settings/flows/new')}
          sx={{
            textTransform: "none",
            color: "rgba(0, 0, 0, 0.6)",
            "&:hover": {
              backgroundColor: "rgba(0, 0, 0, 0.04)",
            },
          }}
        >
          Add New
        </Button>
      </Box>
      
      <List sx={{ p: 0 }}>
        {flows.map((flow, index) => (
          <ListItem
            key={flow.id || index}
            sx={{
              py: 1,
              px: 2,
              mb: 1,
              backgroundColor: flow.isDisabled ? "rgba(255, 255, 255, 0.4)" : "rgba(255, 255, 255, 0.7)",
              backdropFilter: "blur(10px)",
              borderRadius: 1,
              border: flow.isDisabled ? "1px solid rgba(0, 0, 0, 0.04)" : "1px solid rgba(0, 0, 0, 0.08)",
              cursor: "pointer",
              opacity: flow.isDisabled ? 0.6 : 1,
              "&:hover": {
                backgroundColor: flow.isDisabled ? "rgba(255, 255, 255, 0.5)" : "rgba(255, 255, 255, 0.85)",
                "& .action-buttons": {
                  opacity: 1,
                },
              },
            }}
            onClick={(e) => {
              // Only navigate if not clicking on action buttons
              if (!e.target.closest('.action-buttons') && !e.target.closest('button')) {
                router.push(`/settings/flows/${flow.id || index}`);
              }
            }}
          >
            <ListItemText
              primary={flow.name || flow.id || `Flow ${index + 1}`}
              secondary={flow.triggerPhrases?.[0] ? `"${flow.triggerPhrases[0]}"` : "No trigger phrases"}
              primaryTypographyProps={{
                fontSize: "0.95rem",
                fontWeight: 400,
                color: flow.isDisabled ? "rgba(0, 0, 0, 0.4)" : "inherit",
                textDecoration: flow.isDisabled ? "line-through" : "none"
              }}
              secondaryTypographyProps={{
                fontSize: "0.8rem",
                fontStyle: "italic",
                color: flow.isDisabled ? "rgba(0, 0, 0, 0.3)" : "rgba(0, 0, 0, 0.5)",
              }}
            />
            <Box
              className="action-buttons"
              sx={{
                display: "flex",
                gap: 1,
                alignItems: "center",
                opacity: 0,
                transition: "opacity 0.2s",
              }}
            >
              <FormControlLabel
                control={
                  <Switch
                    checked={!flow.isDisabled}
                    onChange={(e) => onToggleFlow(index, e)}
                    size="small"
                    sx={{
                      "& .MuiSwitch-switchBase.Mui-checked": {
                        color: "var(--dm-text, #1a1a1a)",
                      },
                      "& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track": {
                        backgroundColor: "#1a1a1a",
                      },
                    }}
                  />
                }
                label=""
                sx={{ margin: 0 }}
              />
              <IconButton
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteFlow(index);
                }}
                size="small"
                sx={{ 
                  color: "rgba(0, 0, 0, 0.4)",
                  "&:hover": {
                    color: "red",
                  },
                }}
              >
                <Trash2 size={16} />
              </IconButton>
            </Box>
          </ListItem>
        ))}
      </List>
    </Box>
  );
}