"use client";

import { Box, Typography } from "@mui/material";
import { motion } from "framer-motion";
import { useEffect, useRef } from "react";

export default function CostBenefitChart({ data, title = "Cost-Benefit Analysis" }) {
  const svgRef = useRef(null);

  useEffect(() => {
    if (!data || !svgRef.current) return;

    const svg = svgRef.current;
    const width = 500;
    const height = 350;
    const margin = { top: 40, right: 40, bottom: 80, left: 80 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    
    // Clear previous content
    svg.innerHTML = '';

    // Create main group
    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
    g.setAttribute("transform", `translate(${margin.left}, ${margin.top})`);
    svg.appendChild(g);

    // Calculate bar dimensions
    const barWidth = plotWidth / 4;
    const barSpacing = barWidth / 4;
    
    // Data for the chart
    const chartData = [
      { label: "Initial Cost", hd2024: 2850, hd2025: 4150, color2024: "#4caf50", color2025: "#f44336" },
      { label: "8h Operation Cost\n(Annual)", hd2024: 1200, hd2025: 800, color2024: "#4caf50", color2025: "#ff9800" },
      { label: "Maintenance Cost\n(Annual)", hd2024: 600, hd2025: 400, color2024: "#81c784", color2025: "#ffb74d" },
      { label: "Total 3-Year Cost", hd2024: 8250, hd2025: 7750, color2024: "#2e7d32", color2025: "#e64a19" }
    ];

    // Find max value for scaling
    const maxValue = Math.max(...chartData.flatMap(d => [d.hd2024, d.hd2025]));
    const scale = plotHeight / maxValue;

    // Draw grid lines
    for (let i = 0; i <= 5; i++) {
      const y = (i / 5) * plotHeight;
      const gridLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
      gridLine.setAttribute("x1", 0);
      gridLine.setAttribute("y1", plotHeight - y);
      gridLine.setAttribute("x2", plotWidth);
      gridLine.setAttribute("y2", plotHeight - y);
      gridLine.setAttribute("stroke", "#f0f0f0");
      gridLine.setAttribute("stroke-width", "1");
      g.appendChild(gridLine);

      // Add value labels
      const valueLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      valueLabel.setAttribute("x", -10);
      valueLabel.setAttribute("y", plotHeight - y + 4);
      valueLabel.setAttribute("text-anchor", "end");
      valueLabel.setAttribute("font-size", "10");
      valueLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
      valueLabel.setAttribute("fill", "#666");
      valueLabel.textContent = `$${Math.round((maxValue / 5) * i / 1000)}k`;
      g.appendChild(valueLabel);
    }

    // Draw bars for each category
    chartData.forEach((category, categoryIndex) => {
      const categoryX = categoryIndex * (barWidth + barSpacing);
      
      // HD-2024 bar
      const bar2024Height = category.hd2024 * scale;
      const bar2024 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bar2024.setAttribute("x", categoryX);
      bar2024.setAttribute("y", plotHeight);
      bar2024.setAttribute("width", barWidth * 0.4);
      bar2024.setAttribute("height", 0);
      bar2024.setAttribute("fill", category.color2024);
      bar2024.setAttribute("rx", "2");
      bar2024.style.animation = `growBar 1s ease-out ${categoryIndex * 0.2}s forwards`;
      g.appendChild(bar2024);

      // HD-2025 bar
      const bar2025Height = category.hd2025 * scale;
      const bar2025 = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      bar2025.setAttribute("x", categoryX + barWidth * 0.45);
      bar2025.setAttribute("y", plotHeight);
      bar2025.setAttribute("width", barWidth * 0.4);
      bar2025.setAttribute("height", 0);
      bar2025.setAttribute("fill", category.color2025);
      bar2025.setAttribute("rx", "2");
      bar2025.style.animation = `growBar 1s ease-out ${categoryIndex * 0.2 + 0.1}s forwards`;
      g.appendChild(bar2025);

      // Value labels on bars
      const value2024 = document.createElementNS("http://www.w3.org/2000/svg", "text");
      value2024.setAttribute("x", categoryX + barWidth * 0.2);
      value2024.setAttribute("y", plotHeight - bar2024Height - 5);
      value2024.setAttribute("text-anchor", "middle");
      value2024.setAttribute("font-size", "10");
      value2024.setAttribute("font-family", "var(--font-exo2), sans-serif");
      value2024.setAttribute("fill", "#333");
      value2024.setAttribute("font-weight", "bold");
      value2024.textContent = `$${category.hd2024}`;
      value2024.style.opacity = "0";
      value2024.style.animation = `fadeIn 0.5s ease-out ${categoryIndex * 0.2 + 0.8}s forwards`;
      g.appendChild(value2024);

      const value2025 = document.createElementNS("http://www.w3.org/2000/svg", "text");
      value2025.setAttribute("x", categoryX + barWidth * 0.65);
      value2025.setAttribute("y", plotHeight - bar2025Height - 5);
      value2025.setAttribute("text-anchor", "middle");
      value2025.setAttribute("font-size", "10");
      value2025.setAttribute("font-family", "var(--font-exo2), sans-serif");
      value2025.setAttribute("fill", "#333");
      value2025.setAttribute("font-weight", "bold");
      value2025.textContent = `$${category.hd2025}`;
      value2025.style.opacity = "0";
      value2025.style.animation = `fadeIn 0.5s ease-out ${categoryIndex * 0.2 + 0.9}s forwards`;
      g.appendChild(value2025);

      // Category labels
      const categoryLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
      categoryLabel.setAttribute("x", categoryX + barWidth * 0.425);
      categoryLabel.setAttribute("y", plotHeight + 25);
      categoryLabel.setAttribute("text-anchor", "middle");
      categoryLabel.setAttribute("font-size", "11");
      categoryLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
      categoryLabel.setAttribute("fill", "#666");
      categoryLabel.setAttribute("font-weight", "500");
      
      // Handle multi-line labels
      const lines = category.label.split('\n');
      if (lines.length > 1) {
        lines.forEach((line, lineIndex) => {
          const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
          tspan.setAttribute("x", categoryX + barWidth * 0.425);
          tspan.setAttribute("dy", lineIndex === 0 ? 0 : 12);
          tspan.textContent = line;
          categoryLabel.appendChild(tspan);
        });
      } else {
        categoryLabel.textContent = category.label;
      }
      
      g.appendChild(categoryLabel);

      // Add animation keyframes to the bar elements
      bar2024.style.setProperty('--target-height', `${bar2024Height}px`);
      bar2024.style.setProperty('--target-y', `${plotHeight - bar2024Height}px`);
      
      bar2025.style.setProperty('--target-height', `${bar2025Height}px`);
      bar2025.style.setProperty('--target-y', `${plotHeight - bar2025Height}px`);
    });

    // Add Winner indicator for Initial Cost
    const winnerBox = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    winnerBox.setAttribute("x", -5);
    winnerBox.setAttribute("y", plotHeight - chartData[0].hd2024 * scale - 25);
    winnerBox.setAttribute("width", barWidth * 0.4 + 10);
    winnerBox.setAttribute("height", 20);
    winnerBox.setAttribute("fill", "#4caf50");
    winnerBox.setAttribute("fill-opacity", "0.1");
    winnerBox.setAttribute("stroke", "#4caf50");
    winnerBox.setAttribute("stroke-width", "2");
    winnerBox.setAttribute("rx", "3");
    winnerBox.style.opacity = "0";
    winnerBox.style.animation = "fadeIn 0.5s ease-out 2s forwards";
    g.appendChild(winnerBox);

    const winnerText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    winnerText.setAttribute("x", barWidth * 0.2);
    winnerText.setAttribute("y", plotHeight - chartData[0].hd2024 * scale - 12);
    winnerText.setAttribute("text-anchor", "middle");
    winnerText.setAttribute("font-size", "10");
    winnerText.setAttribute("font-family", "var(--font-exo2), sans-serif");
    winnerText.setAttribute("fill", "#4caf50");
    winnerText.setAttribute("font-weight", "bold");
    winnerText.textContent = "WINNER";
    winnerText.style.opacity = "0";
    winnerText.style.animation = "fadeIn 0.5s ease-out 2.1s forwards";
    g.appendChild(winnerText);

    // Add axis labels
    const yLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
    yLabel.setAttribute("x", -50);
    yLabel.setAttribute("y", plotHeight / 2);
    yLabel.setAttribute("text-anchor", "middle");
    yLabel.setAttribute("transform", `rotate(-90, -50, ${plotHeight / 2})`);
    yLabel.setAttribute("font-size", "12");
    yLabel.setAttribute("font-family", "var(--font-exo2), sans-serif");
    yLabel.setAttribute("fill", "#666");
    yLabel.textContent = "Cost (USD)";
    g.appendChild(yLabel);

    // Add conclusion box
    const conclusionBox = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    conclusionBox.setAttribute("x", plotWidth - 150);
    conclusionBox.setAttribute("y", 10);
    conclusionBox.setAttribute("width", 140);
    conclusionBox.setAttribute("height", 80);
    conclusionBox.setAttribute("fill", "#e8f5e8");
    conclusionBox.setAttribute("stroke", "#4caf50");
    conclusionBox.setAttribute("stroke-width", "2");
    conclusionBox.setAttribute("rx", "5");
    conclusionBox.style.opacity = "0";
    conclusionBox.style.animation = "fadeIn 0.5s ease-out 2.5s forwards";
    g.appendChild(conclusionBox);

    const conclusionTitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
    conclusionTitle.setAttribute("x", plotWidth - 80);
    conclusionTitle.setAttribute("y", 28);
    conclusionTitle.setAttribute("text-anchor", "middle");
    conclusionTitle.setAttribute("font-size", "11");
    conclusionTitle.setAttribute("font-family", "var(--font-exo2), sans-serif");
    conclusionTitle.setAttribute("fill", "#2e7d32");
    conclusionTitle.setAttribute("font-weight", "bold");
    conclusionTitle.textContent = "8-Hour Shifts";
    conclusionTitle.style.opacity = "0";
    conclusionTitle.style.animation = "fadeIn 0.5s ease-out 2.6s forwards";
    g.appendChild(conclusionTitle);

    const conclusionText1 = document.createElementNS("http://www.w3.org/2000/svg", "text");
    conclusionText1.setAttribute("x", plotWidth - 80);
    conclusionText1.setAttribute("y", 45);
    conclusionText1.setAttribute("text-anchor", "middle");
    conclusionText1.setAttribute("font-size", "9");
    conclusionText1.setAttribute("font-family", "var(--font-exo2), sans-serif");
    conclusionText1.setAttribute("fill", "#2e7d32");
    conclusionText1.textContent = "HD-2024 saves";
    conclusionText1.style.opacity = "0";
    conclusionText1.style.animation = "fadeIn 0.5s ease-out 2.7s forwards";
    g.appendChild(conclusionText1);

    const conclusionText2 = document.createElementNS("http://www.w3.org/2000/svg", "text");
    conclusionText2.setAttribute("x", plotWidth - 80);
    conclusionText2.setAttribute("y", 58);
    conclusionText2.setAttribute("text-anchor", "middle");
    conclusionText2.setAttribute("font-size", "9");
    conclusionText2.setAttribute("font-family", "var(--font-exo2), sans-serif");
    conclusionText2.setAttribute("fill", "#2e7d32");
    conclusionText2.setAttribute("font-weight", "bold");
    conclusionText2.textContent = "$1,300 initially";
    conclusionText2.style.opacity = "0";
    conclusionText2.style.animation = "fadeIn 0.5s ease-out 2.8s forwards";
    g.appendChild(conclusionText2);

    const conclusionText3 = document.createElementNS("http://www.w3.org/2000/svg", "text");
    conclusionText3.setAttribute("x", plotWidth - 80);
    conclusionText3.setAttribute("y", 75);
    conclusionText3.setAttribute("text-anchor", "middle");
    conclusionText3.setAttribute("font-size", "9");
    conclusionText3.setAttribute("font-family", "var(--font-exo2), sans-serif");
    conclusionText3.setAttribute("fill", "#2e7d32");
    conclusionText3.textContent = "Perfect for your needs!";
    conclusionText3.style.opacity = "0";
    conclusionText3.style.animation = "fadeIn 0.5s ease-out 2.9s forwards";
    g.appendChild(conclusionText3);

    // Add CSS animations
    const style = document.createElementNS("http://www.w3.org/2000/svg", "style");
    style.textContent = `
      @keyframes growBar {
        from {
          height: 0;
        }
        to {
          height: var(--target-height);
          y: var(--target-y);
        }
      }
      @keyframes fadeIn {
        from {
          opacity: 0;
          transform: translateY(10px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }
    `;
    svg.appendChild(style);

  }, [data]);

  if (!data) {
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
          width="500"
          height="350"
          style={{ overflow: "visible" }}
        />
        
        {/* Legend */}
        <Box sx={{ display: "flex", gap: 3, mt: 2, flexWrap: "wrap", justifyContent: "center" }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                backgroundColor: "#4caf50",
                borderRadius: "2px",
              }}
            />
            <Typography variant="body2" sx={{ fontSize: "0.9rem", color: "#666" }}>
              HD-2024
            </Typography>
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Box
              sx={{
                width: 16,
                height: 16,
                backgroundColor: "#f44336",
                borderRadius: "2px",
              }}
            />
            <Typography variant="body2" sx={{ fontSize: "0.9rem", color: "#666" }}>
              HD-2025
            </Typography>
          </Box>
        </Box>
      </Box>
    </motion.div>
  );
}