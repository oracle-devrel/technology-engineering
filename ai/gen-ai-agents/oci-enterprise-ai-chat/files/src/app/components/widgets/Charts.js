"use client";

import { Box } from "@mui/material";
import { motion } from "framer-motion";
import {
  LineChart as ReLineChart,
  Line,
  BarChart as ReBarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import {
  parseSeriesChart,
  parsePieChart,
  getChartColor,
  getChartColors,
} from "../../utils/chartParser";

const CHART_HEIGHT = { s: 150, m: 200, l: 280 };

const getHeight = (h) => {
  if (!h) return CHART_HEIGHT.m;
  if (typeof h === "number") return h;
  return CHART_HEIGHT[h] || CHART_HEIGHT.m;
};

const ChartWrapper = ({ children, height }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
    style={{ width: "100%", height }}
  >
    <ResponsiveContainer width="100%" height="100%">
      {children}
    </ResponsiveContainer>
  </motion.div>
);

export function WidgetLineChart({ props }) {
  const { data, series } = parseSeriesChart(props);
  const colors = getChartColors(props._colors);
  const showGrid = props._grid !== "0";
  const showLegend = props._legend && props._legend !== "n";
  const height = getHeight(props._h);

  return (
    <ChartWrapper height={height}>
      <ReLineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />}
        <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="rgba(0,0,0,0.4)" />
        <YAxis tick={{ fontSize: 11 }} stroke="rgba(0,0,0,0.4)" />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
        {showLegend && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {series.map((s, i) => (
          <Line
            key={s.key}
            type="monotone"
            dataKey={s.key}
            name={s.name}
            stroke={colors[i % colors.length]}
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        ))}
      </ReLineChart>
    </ChartWrapper>
  );
}

export function WidgetBarChart({ props }) {
  const { data, series } = parseSeriesChart(props);
  const colors = getChartColors(props._colors);
  const showGrid = props._grid !== "0";
  const showLegend = props._legend && props._legend !== "n";
  const height = getHeight(props._h);
  const stacked = props._stack === "1";

  return (
    <ChartWrapper height={height}>
      <ReBarChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
        {showGrid && <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.1)" />}
        <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="rgba(0,0,0,0.4)" />
        <YAxis tick={{ fontSize: 11 }} stroke="rgba(0,0,0,0.4)" />
        <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
        {showLegend && <Legend wrapperStyle={{ fontSize: 11 }} />}
        {series.map((s, i) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.name}
            fill={colors[i % colors.length]}
            radius={[4, 4, 0, 0]}
            stackId={stacked ? "stack" : undefined}
          />
        ))}
      </ReBarChart>
    </ChartWrapper>
  );
}

export function WidgetPieChart({ props, isDonut = false }) {
  const { data, centerValue, centerLabel } = parsePieChart(props);
  const colors = getChartColors(props._colors);
  const showLegend = props._legend !== "n";
  const baseHeight = getHeight(props._h);
  const height = Math.max(baseHeight, 220) + (showLegend ? 40 : 0);

  return (
    <ChartWrapper height={height}>
      <RePieChart margin={{ top: 5, right: 5, bottom: showLegend ? 10 : 5, left: 5 }}>
        <Pie
          data={data}
          cx="50%"
          cy={showLegend ? "42%" : "48%"}
          innerRadius={isDonut ? "45%" : 0}
          outerRadius="65%"
          paddingAngle={2}
          dataKey="value"
          label={({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
            if (percent < 0.08) return null; // Don't show label for slices < 8%
            const RADIAN = Math.PI / 180;
            const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
            const x = cx + radius * Math.cos(-midAngle * RADIAN);
            const y = cy + radius * Math.sin(-midAngle * RADIAN);
            return (
              <text
                x={x}
                y={y}
                fill="white"
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={10}
                fontWeight={600}
              >
                {`${(percent * 100).toFixed(0)}%`}
              </text>
            );
          }}
          labelLine={false}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={colors[i % colors.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
          formatter={(value, name) => [`${value}`, name]}
        />
        {showLegend && (
          <Legend
            wrapperStyle={{ fontSize: 11, paddingTop: 8 }}
            layout="horizontal"
            align="center"
            verticalAlign="bottom"
          />
        )}
        {isDonut && centerValue && (
          <text x="50%" y={showLegend ? "45%" : "50%"} textAnchor="middle" dominantBaseline="middle">
            <tspan x="50%" dy="-0.2em" fontSize="1.3rem" fontWeight="600">
              {centerValue}
            </tspan>
            {centerLabel && (
              <tspan x="50%" dy="1.3em" fontSize="0.65rem" fill="rgba(0,0,0,0.5)">
                {centerLabel}
              </tspan>
            )}
          </text>
        )}
      </RePieChart>
    </ChartWrapper>
  );
}

export function WidgetDonutChart({ props }) {
  return <WidgetPieChart props={props} isDonut={true} />;
}
