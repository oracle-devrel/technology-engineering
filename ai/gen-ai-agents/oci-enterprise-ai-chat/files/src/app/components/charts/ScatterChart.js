"use client";

import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

export default function ScatterChart({ data, title = "Defect Analysis" }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = svgRef.current;
    const width = 450;
    const height = 300;
    const margin = { top: 20, right: 20, bottom: 50, left: 60 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    
    // Clear previous content
    svg.innerHTML = '';

    // Create main group
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);
    svg.appendChild(g);

    // Create scales
    const maxX = Math.max(...data.points.map(p => p.x));
    const maxY = Math.max(...data.points.map(p => p.y));
    
    const scaleX = (x) => (x / maxX) * plotWidth;
    const scaleY = (y) => plotHeight - (y / maxY) * plotHeight;

    // Draw grid lines
    for (let i = 0; i <= 5; i++) {
      const x = (i / 5) * plotWidth;
      const y = (i / 5) * plotHeight;
      
      // Vertical grid lines
      const vLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      vLine.setAttribute("x1", x);
      vLine.setAttribute("y1", 0);
      vLine.setAttribute("x2", x);
      vLine.setAttribute("y2", plotHeight);
      vLine.setAttribute("stroke", "#f0f0f0");
      vLine.setAttribute("stroke-width", "1");
      g.appendChild(vLine);
      
      // Horizontal grid lines
      const hLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      hLine.setAttribute("x1", 0);
      hLine.setAttribute("y1", y);
      hLine.setAttribute("x2", plotWidth);
      hLine.setAttribute("y2", y);
      hLine.setAttribute("stroke", "#f0f0f0");
      hLine.setAttribute("stroke-width", "1");
      g.appendChild(hLine);
    }

    // Draw axes
    const xAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    xAxis.setAttribute("x1", 0);
    xAxis.setAttribute("y1", plotHeight);
    xAxis.setAttribute("x2", plotWidth);
    xAxis.setAttribute("y2", plotHeight);
    xAxis.setAttribute("stroke", "#333");
    xAxis.setAttribute("stroke-width", "2");
    g.appendChild(xAxis);

    const yAxis = document.createElementNS("http://www.w3.org/2000/svg", "line");
    yAxis.setAttribute("x1", 0);
    yAxis.setAttribute("y1", 0);
    yAxis.setAttribute("x2", 0);
    yAxis.setAttribute("y2", plotHeight);
    yAxis.setAttribute("stroke", "#333");
    yAxis.setAttribute("stroke-width", "2");
    g.appendChild(yAxis);

    // Add safe zone (0-8 hours)
    const safeZoneWidth = scaleX(8);
    const safeZone = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    safeZone.setAttribute("x", 0);
    safeZone.setAttribute("y", 0);
    safeZone.setAttribute("width", safeZoneWidth);
    safeZone.setAttribute("height", plotHeight);
    safeZone.setAttribute("fill", "#4caf50");
    safeZone.setAttribute("fill-opacity", "0.1");
    g.appendChild(safeZone);

    // Add danger zone (16+ hours)
    const dangerZoneStart = scaleX(16);
    const dangerZone = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    dangerZone.setAttribute("x", dangerZoneStart);
    dangerZone.setAttribute("y", 0);
    dangerZone.setAttribute("width", plotWidth - dangerZoneStart);
    dangerZone.setAttribute("height", plotHeight);
    dangerZone.setAttribute("fill", "#f44336");
    dangerZone.setAttribute("fill-opacity", "0.1");
    g.appendChild(dangerZone);

    // Draw data points with animation
    data.points.forEach((point, index) => {
      const cx = scaleX(point.x);
      const cy = scaleY(point.y);
      
      let color = "#2196f3"; // Default blue
      if (point.motor === "HD-2024") {
        color = point.x <= 8 ? "#4caf50" : "#ff9800"; // Green in safe zone, orange outside
      } else if (point.motor === "HD-2025") {
        color = "#9c27b0"; // Purple
      }
      
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", cx);
      circle.setAttribute("cy", cy);
      circle.setAttribute("r", "5");
      circle.setAttribute("fill", color);
      circle.setAttribute("stroke", "white");
      circle.setAttribute("stroke-width", "2");
      circle.style.opacity = "0";
      circle.style.animation = `scatterFadeIn 0.5s ease-in-out ${0.5 + index * 0.1}s forwards`;
      
      g.appendChild(circle);
    });

    // Add axis labels
    const xLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    xLabel.setAttribute("x", plotWidth / 2);
    xLabel.setAttribute("y", plotHeight + 35);
    xLabel.setAttribute("text-anchor", "middle");
    xLabel.setAttribute("font-size", "12");
    xLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
    xLabel.setAttribute("fill", "#666");
    xLabel.textContent = "Operating Hours per Day";
    g.appendChild(xLabel);

    const yLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    yLabel.setAttribute("x", -35);
    yLabel.setAttribute("y", plotHeight / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90, -35, ${plotHeight / 2})`);
    yLabel.setAttribute("font-size", "12");
    yLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
    yLabel.setAttribute("fill", "#666");
    yLabel.textContent = "Defect Rate (%)";
    g.appendChild(yLabel);

    // Add zone labels
    const safeLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    safeLabel.setAttribute("x", safeZoneWidth / 2);
    safeLabel.setAttribute("y", 15);
    safeLabel.setAttribute("text-anchor", "middle");
    safeLabel.setAttribute("font-size", "10");
    safeLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
    safeLabel.setAttribute("fill", "#4caf50");
    safeLabel.setAttribute("font-weight", "bold");
    safeLabel.textContent = "SAFE ZONE";
    g.appendChild(safeLabel);

    const dangerLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    dangerLabel.setAttribute("x", dangerZoneStart + (plotWidth - dangerZoneStart) / 2);
    dangerLabel.setAttribute("y", 15);
    dangerLabel.setAttribute("text-anchor", "middle");
    dangerLabel.setAttribute("font-size", "10");
    dangerLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
    dangerLabel.setAttribute("fill", "#f44336");
    dangerLabel.setAttribute("font-weight", "bold");
    dangerLabel.textContent = "HIGH RISK";
    g.appendChild(dangerLabel);

    // Add CSS animation
    const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
    style.textContent = `
      @keyframes scatterFadeIn {
        from {
          opacity: 0;
          transform: scale(0);
        }
        to {
          opacity: 1;
          transform: scale(1);
        }
      }
    `;
    svg.appendChild(style);

  }, [data]);

  if (!data || !data.points) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          mb: 3,
          p: 3,
          backgroundColor: "rgba(0, 0, 0, 0.01)",
          borderRadius: 2,
          border: "1px solid rgba(0, 0, 0, 0.05)",
        }}
      >
        <Typography
          variant="h6"
          sx={{
            mb: 2,
            fontSize: "1.1rem",
            fontWeight: 500,
            color: "#333",
            fontFamily: "var(--font-exo2), sans-serif",
          }}
        >
          {title}
        </Typography>
        
        <svg
          ref={svgRef}
          width="450"
          height="300"
          style={{ overflow: "visible" }}
        />
        
        {/* Legend */}
        <Box sx={{ display: "flex", gap: 3, mt: 2, flexWrap: "wrap", justifyContent: "center" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                backgroundColor: "#4caf50",
                borderRadius: "50%",
              }}
            />
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "#666" }}>
              HD-2024 (Safe Zone)
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                backgroundColor: "#ff9800",
                borderRadius: "50%",
              }}
            />
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "#666" }}>
              HD-2024 (High Risk)
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 12,
                height: 12,
                backgroundColor: "#9c27b0",
                borderRadius: "50%",
              }}
            />
            <Typography variant="body2" sx={{ fontSize: "0.8rem", color: "#666" }}>
              HD-2025
            </Typography>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}