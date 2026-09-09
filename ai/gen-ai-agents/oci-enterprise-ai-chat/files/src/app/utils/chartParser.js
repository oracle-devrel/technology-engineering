/**
 * Parses widget chart data into recharts-compatible format
 */

// Parse semicolon-separated values into array
const parseValues = (str) => {
  if (!str) return [];
  return str.split(";").map(v => {
    const num = parseFloat(v.trim());
    return isNaN(num) ? v.trim() : num;
  });
};

// Parse line/bar/area chart data
export const parseSeriesChart = (props) => {
  const labels = parseValues(props.x);
  const series = [];

  // Find all y series (y, y2, y3, etc.)
  Object.keys(props).forEach(key => {
    if (key === "y" || /^y\d+$/.test(key)) {
      let rawValue = props[key];
      let seriesName = null;

      // Handle "Name:value1;value2" format (AI sometimes generates this)
      if (rawValue && rawValue.includes(":")) {
        const colonIdx = rawValue.indexOf(":");
        const beforeColon = rawValue.slice(0, colonIdx);
        // Check if before colon is a name (not a number)
        if (isNaN(parseFloat(beforeColon))) {
          seriesName = beforeColon.trim();
          rawValue = rawValue.slice(colonIdx + 1);
        }
      }

      const values = parseValues(rawValue);
      const nameKey = key === "y" ? "y_n" : `${key}_n`;
      series.push({
        key,
        name: seriesName || props[nameKey] || (key === "y" ? "Series 1" : `Series ${key.slice(1)}`),
        data: values
      });
    }
  });

  // Build recharts data format: [{name: "Ene", y: 100, y2: 90}, ...]
  const data = labels.map((label, i) => {
    const point = { name: label };
    series.forEach(s => {
      point[s.key] = s.data[i] ?? 0;
    });
    return point;
  });

  return { data, series };
};

// Parse pie/donut chart data (categorical)
export const parsePieChart = (props) => {
  const data = [];
  const skipKeys = ["ch_pie", "ch_don", "_c", "_colors", "_h", "_legend", "_anim", "n", "n_s", "t", "s", "d", "x", "y"];

  Object.entries(props).forEach(([key, value]) => {
    if (key.startsWith("_") || skipKeys.includes(key)) return;

    // Handle "Name:value" format for pie slices
    let name = key;
    let val = value;

    if (typeof value === "string" && value.includes(":")) {
      // This shouldn't happen for pie charts but handle it anyway
      const parts = value.split(":");
      if (parts.length === 2 && !isNaN(parseFloat(parts[1]))) {
        name = parts[0].trim();
        val = parts[1].trim();
      }
    }

    const numValue = parseFloat(val);
    if (!isNaN(numValue)) {
      data.push({ name, value: numValue });
    }
  });

  return { data, centerValue: props.n, centerLabel: props.n_s };
};

// Parse gauge data
export const parseGaugeChart = (props) => {
  return {
    value: parseFloat(props.v) || 0,
    max: parseFloat(props.max) || 100,
    target: props.target ? parseFloat(props.target) : null
  };
};

// Parse sparkline (just values)
export const parseSparkline = (value) => {
  return parseValues(value).map((v, i) => ({ i, v }));
};

// Color palette
export const CHART_COLORS = {
  p: "#C74634", // primary (oracle red)
  s: "#00758F", // secondary (teal)
  b: "#3B82F6", // blue
  g: "#22C55E", // green
  o: "#F59E0B", // orange
  r: "#EF4444", // red
  purple: "#8B5CF6",
  pink: "#EC4899",
};

export const getChartColor = (code) => {
  if (!code) return CHART_COLORS.p;
  if (code.startsWith("#")) return code;
  return CHART_COLORS[code] || CHART_COLORS.p;
};

export const getChartColors = (colorStr) => {
  if (!colorStr) return [CHART_COLORS.p, CHART_COLORS.s, CHART_COLORS.b, CHART_COLORS.g, CHART_COLORS.o];
  return colorStr.split(";").map(c => getChartColor(c.trim()));
};
