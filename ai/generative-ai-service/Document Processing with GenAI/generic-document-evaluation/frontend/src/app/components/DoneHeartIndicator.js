import { Box, CircularProgress, Typography } from "@mui/material";
import { useEffect, useState } from "react";

const SemicircularProgress = ({
  value = 0,
  size = 60,
  thickness = 4,
  color = "primary",
  maxAngle = 240,
  icon,
  bottomText,
  ...props
}) => {
  const backgroundValue = (maxAngle / 360) * 100;
  const adjustedValue = (maxAngle / 360) * value;
  const rotation = 90 + (360 - maxAngle) / 2;
  const [progress, setProgress] = useState(0);

  const isHexColor = (color) => {
    return typeof color === "string" && color.startsWith("#");
  };

  const getColor = (theme, colorProp) => {
    return isHexColor(colorProp) ? colorProp : theme.palette[colorProp].main;
  };

  useEffect(() => {
    const timer = setTimeout(() => setProgress(adjustedValue), 50);
    return () => clearTimeout(timer);
  }, [adjustedValue]);

  return (
    <Box sx={{ position: "relative", width: size, height: size }}>
      <Box
        sx={{
          position: "relative",
          width: size,
          height: size,
          transform: `rotate(${rotation}deg)`,
          transformOrigin: "50% 50%",
        }}
      >
        <CircularProgress
          variant="determinate"
          value={backgroundValue}
          size={size}
          thickness={thickness}
          sx={{
            transform: "none !important",
            color: (theme) => theme.palette.mode === 'dark' ? theme.palette.grey[800] : theme.palette.grey[200],
            "& .MuiCircularProgress-circle": { strokeLinecap: "round" },
          }}
          {...props}
        />
        <CircularProgress
          variant="determinate"
          value={progress}
          size={size}
          thickness={thickness}
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            transform: "none !important",
            color: isHexColor(color) ? color : undefined,
            "& .MuiCircularProgress-circle": {
              strokeLinecap: "round",
              transition: "stroke-dashoffset 1s ease-out",
            },
          }}
          color={isHexColor(color) ? undefined : color}
          {...props}
        />
      </Box>
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          color: (theme) => getColor(theme, color),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {icon}
      </Box>
      <Box
        sx={{
          position: "absolute",
          bottom: -size * 0.1,
          left: "50%",
          transform: "translateX(-50%)",
        }}
      >
        <Typography
          variant="overline"
          sx={{
            fontSize: size / 7,
            fontWeight: 800,
            color: (theme) => getColor(theme, color),
          }}
        >
          {bottomText}
        </Typography>
      </Box>
    </Box>
  );
};

export default SemicircularProgress;
