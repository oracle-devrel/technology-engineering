"use client";
import { Box } from "@mui/material";
import Widget from "../../Widget";

export default function V2WidgetAdapter({ attrs = {}, onSubmit, disabled }) {
  return (
    <Box sx={{ flex: 1, minWidth: 0, width: "100%" }}>
      <Widget props={attrs} onSubmit={onSubmit} disabled={disabled} isComplete={true} embedded />
    </Box>
  );
}
