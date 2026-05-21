"use client";

import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

export default function RadarChart({ data, title = "Comparison Chart" }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = svgRef.current;
    const size = 300;
    const center = size / 2;
    const maxRadius = 120;
    
    // Clear previous content
    svg.innerHTML = '';

    // Create the radar grid
    const levels = 5;
    const metrics = data.metrics || [];
    const items = data.items || [];
    
    if (metrics.length === 0) return;

    const angleSlice = (Math.PI * 2) / metrics.length;

    // Draw concentric circles (grid)
    for (let level = 1; level <= levels; level++) {
      const radius = (maxRadius / levels) * level;
      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", center);
      circle.setAttribute("cy", center);
      circle.setAttribute("r", radius);
      circle.setAttribute("fill", "none");
      circle.setAttribute("stroke", "#e0e0e0");
      circle.setAttribute("stroke-width", "1");
      svg.appendChild(circle);
    }

    // Draw axis lines
    metrics.forEach((metric, i) => {
      const angle = angleSlice * i - Math.PI / 2;
      const x = center + Math.cos(angle) * maxRadius;
      const y = center + Math.sin(angle) * maxRadius;
      
      const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", center);
      line.setAttribute("y1", center);
      line.setAttribute("x2", x);
      line.setAttribute("y2", y);
      line.setAttribute("stroke", "#e0e0e0");
      line.setAttribute("stroke-width", "1");
      svg.appendChild(line);

      // Add labels
      const labelRadius = maxRadius + 20;
      const labelX = center + Math.cos(angle) * labelRadius;
      const labelY = center + Math.sin(angle) * labelRadius;
      
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", labelX);
      text.setAttribute("y", labelY);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("dominant-baseline", "middle");
      text.setAttribute("font-size", "12");
      text.setAttribute("font-family", "var(--font-exo2), sans-serif");
      text.setAttribute("fill", "#666");
      text.textContent = metric;
      svg.appendChild(text);
    });

    // Draw data for each item
    const colors = ["#2196f3", "#ff9800"];
    
    items.forEach((item, itemIndex) => {
      if (!item.values || item.values.length !== metrics.length) return;
      
      const color = colors[itemIndex] || "#666";
      let pathData = "";
      
      item.values.forEach((value, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        const radius = (value / 100) * maxRadius; // Assuming values are 0-100
        const x = center + Math.cos(angle) * radius;
        const y = center + Math.sin(angle) * radius;
        
        if (i === 0) {
          pathData += `M ${x} ${y}`;
        } else {
          pathData += ` L ${x} ${y}`;
        }
      });
      pathData += " Z"; // Close the path
      
      // Create animated path
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", pathData);
      path.setAttribute("fill", color);
      path.setAttribute("fill-opacity", "0.2");
      path.setAttribute("stroke", color);
      path.setAttribute("stroke-width", "2");
      
      // Add animation
      const totalLength = path.getTotalLength?.() || 0;
      if (totalLength > 0) {
        path.style.strokeDasharray = totalLength;
        path.style.strokeDashoffset = totalLength;
        path.style.animation = `drawPath 1.5s ease-in-out ${itemIndex * 0.3}s forwards`;
      }
      
      svg.appendChild(path);

      // Add data points
      item.values.forEach((value, i) => {
        const angle = angleSlice * i - Math.PI / 2;
        const radius = (value / 100) * maxRadius;
        const x = center + Math.cos(angle) * radius;
        const y = center + Math.sin(angle) * radius;
        
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", "4");
        circle.setAttribute("fill", color);
        circle.setAttribute("stroke", "white");
        circle.setAttribute("stroke-width", "2");
        circle.style.animation = `fadeIn 0.5s ease-in-out ${0.5 + itemIndex * 0.3}s forwards`;
        circle.style.opacity = "0";
        svg.appendChild(circle);
      });
    });

    // Add CSS animation styles
    const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
    style.textContent = `
      @keyframes drawPath {
        to {
          stroke-dashoffset: 0;
        }
      }
      @keyframes fadeIn {
        to {
          opacity: 1;
        }
      }
    `;
    svg.appendChild(style);

  }, [data]);

  if (!data || !data.metrics || !data.items) {
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
          width="300"
          height="300"
          style={{ overflow: "visible" }}
        />
        
        {/* Legend */}
        <Box sx={{ display: "flex", gap: 3, mt: 2 }}>
          {data.items.map((item, index) => (
            <Box key={index} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
              <Box
                sx={{
                  width: 16,
                  height: 16,
                  backgroundColor: index === 0 ? "#2196f3" : "#ff9800",
                  borderRadius: "50%",
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  fontSize: "0.9rem",
                  color: "#666",
                  fontFamily: "var(--font-exo2), sans-serif",
                }}
              >
                {item.name}
              </Typography>
            </Box>
          ))}
        </Box>
      </Box>
    </motion.div>
  );
}