import { Box, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import PinIndicator from "./PinIndicator";

// Componente para la tarjeta con texto
const CardComponent = ({ content, isAnimated, isHovered }) => {
  return (
    <Box
      sx={{
        p: 2,
        display: "flex",
        justifyContent: "flex-start",
        alignItems: "flex-start",
        borderRadius: 2,
        boxShadow: isHovered
          ? "0 12px 24px rgba(0,0,0,0.3), 0 0 10px rgba(6,182,212,0.1)"
          : "0 8px 16px rgba(0,0,0,0.2)",
        backgroundColor: "#FFF",
        transition: "transform 700ms, border 500ms, box-shadow 500ms",
        overflow: "hidden",
        transform: isAnimated
          ? isHovered
            ? "rotateX(25deg) scale(0.85)"
            : "rotateX(40deg) scale(0.8)"
          : "rotateX(0) scale(1)",
        transformOrigin: "center center",
        mx: "auto",
      }}
    >
      <Box sx={{ width: 170, color: "white", overflow: "hidden" }}>
        <Typography
          sx={{
            fontSize: "9.6px",
            lineHeight: 1.5,
            display: "-webkit-box",
            WebkitLineClamp: 18,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            textOverflow: "ellipsis",
            fontFamily: "monospace",
            letterSpacing: 0.05,
            color: "black",
          }}
        >
          {content ||
            "This is a recreation of the pin effect using React and MUI. The animation occurs automatically once and stays in the final position. Now with enhanced hover effects on the ray, circle, and button."}
        </Typography>
      </Box>
    </Box>
  );
};


// Componente principal que integra los dos subcomponentes
const PinContainer = ({ content, type }) => {
  const [isAnimated, setIsAnimated] = useState(false);
  const [showRay, setShowRay] = useState(false);
  const [showButton, setShowButton] = useState(false);
  const [isHovered, setIsHovered] = useState(false);
  const [isButtonHovered, setIsButtonHovered] = useState(false);

  useEffect(() => {
    const timer1 = setTimeout(() => setIsAnimated(true), 500);
    const timer2 = setTimeout(() => setShowRay(true), 1200);
    const timer3 = setTimeout(() => setShowButton(true), 1900);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, []);

  return (
    <Box
      sx={{
        position: "relative",
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        width: "100%",
        height: "100%",
        zIndex: 50,
        height: "fit-content",
        pt: 8,
      }}
    >
      {/* Contenedor de la tarjeta */}
      <Box
        sx={{
          perspective: "1000px",
          transformOrigin: "center center",
          position: "relative",
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <CardComponent
          content={content}
          isAnimated={isAnimated}
          isHovered={isHovered}
        />

        <Box sx={{ position: "absolute", bottom: "50%", right: 0, left: 0 }}>
          <PinIndicator
            type={type}
            isAnimated={isAnimated}
            isHovered={isHovered}
            showRay={showRay}
            showButton={showButton}
            isButtonHovered={isButtonHovered}
            setIsButtonHovered={setIsButtonHovered}
          />
        </Box>
      </Box>

      {/* Pin visual elements component */}
    </Box>
  );
};

export default PinContainer;
