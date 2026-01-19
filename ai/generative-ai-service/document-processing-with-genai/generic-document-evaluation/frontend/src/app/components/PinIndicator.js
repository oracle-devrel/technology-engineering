import { Box, Button } from "@mui/material";

const PinIndicator = ({
  type,
  isAnimated,
  isHovered,
  showRay,
  showButton,
  isButtonHovered,
  setIsButtonHovered,
}) => {
  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: 384,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        opacity: isAnimated ? 1 : 0,
        position: "relative",
        transition: "transform 700ms",
        transform: isHovered ? "translateY(2px)" : "translateY(0)",
      }}
    >
      {/* Button - Flat by default, with negative tilt on hover */}
      <Box
        sx={{
          transition: "transform 500ms",
          transformOrigin: "center bottom",
          // Por defecto sin rotación, en hover rotación negativa (más inclinado que el resto)
          transform: isHovered
            ? "rotateX(-5deg) translateZ(200px)"
            : "rotateX(0deg)",
          zIndex: 11,
        }}
      >
        <Button
          size="small"
          variant="contained"
          disableElevation
          sx={{
            bgcolor: "#FFF",
            color: "#000",
            fontWeight: "bold",
            opacity: showButton ? 1 : 0,
            mb: -0.5,
            transform: isButtonHovered ? "scale(1.08)" : "scale(1)",
            transition: "transform 0.3s ease, opacity 0.3s ease",
          }}
          onMouseEnter={() => setIsButtonHovered(true)}
          onMouseLeave={() => setIsButtonHovered(false)}
        >
          {type}
        </Button>
      </Box>

      {/* Ray - Intermediate tilt between card and button */}
      <Box
        sx={{
          position: "relative",
          height: showRay ? 160 : 0,
          zIndex: 2,
          transition: "transform 700ms",
          transformOrigin: "bottom center",
          // Intermediate tilt between card (25deg) and button (-15deg)
          transform: isHovered
            ? "rotateX(10deg) translateZ(2px)"
            : "rotateX(20deg)",
        }}
      >
        <Box
          sx={{
            width: "1px",
            height: "100%",
            background: "linear-gradient(to bottom, transparent, #06b6d4)",
          }}
        />
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            width: isHovered ? "1.5px" : "1px",
            height: "100%",
            background: (theme) =>
              `linear-gradient(to bottom, transparent, ${theme.palette.accent.cyan}C7)`,
            filter: isHovered ? "blur(3px)" : "blur(2px)",
            opacity: isHovered ? 0.9 : 0.7,
          }}
        />
      </Box>

      {/* Point - Follows card tilt */}
      <Box
        sx={{
          width: isHovered ? 5 : 4,
          height: isHovered ? 5 : 4,
          borderRadius: "50%",
          backgroundColor: (theme) =>
            isHovered
              ? theme.palette.accent.cyanLight
              : theme.palette.accent.cyan,
          boxShadow: isHovered
            ? "0 0 8px 4px rgba(6,182,212,0.5)"
            : "0 0 4px 2px rgba(6,182,212,0.2)",
          opacity: showRay ? 1 : 0,
          zIndex: 2,
          transition:
            "width 0.3s ease, height 0.3s ease, box-shadow 0.3s ease, transform 700ms",
          transform: isHovered
            ? "rotateX(25deg) scale(1.05)"
            : "rotateX(40deg) scale(1)",
        }}
      />

      {/* Circle - Similar to card */}
      <Box
        sx={{
          position: "absolute",
          width: 80,
          height: 80,
          bottom: -45,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <Box
          sx={{
            width: 80,
            height: 80,
            borderRadius: "50%",
            background:
              "linear-gradient(135deg, rgba(220, 230, 255, 0.35) 0%, rgba(240, 245, 255, 0.2) 100%)",
            border: "2px solid rgba(200, 200, 210, 0.7)",
            backdropFilter: "blur(1px) brightness(1.05)",
            boxShadow: isHovered
              ? "0 10px 20px rgba(0, 10, 50, 0.15), inset 0 0 15px 5px rgba(255, 255, 255, 0.3)"
              : "0 8px 15px rgba(0, 10, 50, 0.1), inset 0 0 10px 5px rgba(255, 255, 255, 0.2)",
            opacity: showRay ? (isHovered ? 1 : 0.85) : 0,
            transition:
              "opacity 0.8s ease-out, box-shadow 300ms, transform 700ms, backdrop-filter 300ms",
            transform: isHovered
              ? "rotateX(25deg) scale(1.05)"
              : "rotateX(40deg)",
            // Border refraction effect (gives thickness sensation)
            "&::after": {
              content: '""',
              position: "absolute",
              top: 6,
              left: 6,
              right: 6,
              bottom: 6,
              borderRadius: "50%",
              background: "transparent",
              border: "1px solid rgba(255, 255, 255, 0.5)",
              backdropFilter: "blur(0.5px) brightness(1.1)",
              boxShadow: "inset 0 0 8px 1px rgba(200, 210, 255, 0.3)",
            },
          }}
        />
      </Box>
    </Box>
  );
};

export default PinIndicator;
