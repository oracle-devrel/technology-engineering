"use client";
import { Box } from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { COLORS } from "../../../../config/widgetTheme";

export default function V2Text({ attrs = {}, node }) {
  const text = node?.children?.filter(c => typeof c === "string").join("") || attrs.content || "";
  return (
    <Box sx={{ fontSize: "0.9rem", color: "inherit", lineHeight: 1.7, fontFamily: "inherit", "& p": { my: 0.5 } }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text.trim()}</ReactMarkdown>
    </Box>
  );
}
