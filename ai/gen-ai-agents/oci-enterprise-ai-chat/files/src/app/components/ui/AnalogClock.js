import { useEffect, useState } from "react";

const AnalogClock = ({ size = 60, status = "idle" }) => {
  const [time, setTime] = useState(null);
  const [animated, setAnimated] = useState(false);

  const [processingRotation, setProcessingRotation] = useState({
    hour: 0,
    minute: 0,
  });

  useEffect(() => {
    setTime(new Date());

    const animationTimer = setTimeout(() => {
      setAnimated(true);
    }, 50);

    const timer = setInterval(() => {
      setTime(new Date());
    }, 1000);

    return () => {
      clearTimeout(animationTimer);
      clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    if (status === "processing") {
      const interval = setInterval(() => {
        setProcessingRotation((prev) => ({
          hour: prev.hour + 1,
          minute: prev.minute + 3,
        }));
      }, 50);
      return () => clearInterval(interval);
    } else {
      setProcessingRotation({ hour: 0, minute: 0 });
    }
  }, [status]);

  const getStatusColor = () => {
    switch (status) {
      case "idle":
        return "#000000";
      case "processing":
        return "rgb(59, 130, 246)";
      case "success":
        return "rgb(34, 197, 94)";
      case "error":
        return "rgb(239, 68, 68)";
      default:
        return "#000000";
    }
  };

  const getGlowColor = () => {
    switch (status) {
      case "idle":
        return "rgba(0, 0, 0, 0.1)";
      case "processing":
        return "rgba(59, 130, 246, 0.5)";
      case "success":
        return "rgba(34, 197, 94, 0.5)";
      case "error":
        return "rgba(239, 68, 68, 0.5)";
      default:
        return "rgba(0, 0, 0, 0.1)";
    }
  };

  const center = size / 2;
  const radius = size / 2 - 4;
  const hourHandWidth = Math.max(1.5, size / 120);
  const minuteHandWidth = Math.max(1.2, size / 120);

  let hourAngle = 0;
  let minuteAngle = 0;

  if (time) {
    const hours = time.getHours() % 12;
    const minutes = time.getMinutes();
    const seconds = time.getSeconds();

    if (status === "error") {
      const shake = Math.sin(seconds * 10) * 5;
      hourAngle = hours * 30 + minutes * 0.5 + shake;
      minuteAngle = minutes * 6 + shake;
    } else {
      hourAngle = hours * 30 + minutes * 0.5;
      minuteAngle = minutes * 6;
    }

    if (status === "processing") {
      hourAngle += processingRotation.hour;
      minuteAngle += processingRotation.minute;
    }
    
    // Always apply modulo to prevent multiple rotations when transitioning
    hourAngle = hourAngle % 360;
    minuteAngle = minuteAngle % 360;
  }

  const currentColor = getStatusColor();
  const glowColor = getGlowColor();

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <svg width={size} height={size}>
        <defs>
          <radialGradient id={`clockGradient-${status}`}>
            <stop
              offset="0%"
              stopColor={
                status === "idle" ? "white" : "rgba(255, 255, 255, 0.9)"
              }
            />
            <stop
              offset="100%"
              stopColor={
                status === "idle" ? "white" : "rgba(255, 255, 255, 0.7)"
              }
            />
          </radialGradient>
        </defs>

        <circle
          cx={center}
          cy={center}
          r={radius}
          fill={`url(#clockGradient-${status})`}
          stroke={currentColor}
          strokeWidth={status === "processing" ? 2 : 1.5}
          style={{
            transition: "all 0.3s ease",
            strokeDasharray: status === "error" ? "2,2" : "none",
            animation: status === "error" ? "shake 0.3s ease-out" : "none",
          }}
        />

        {(status === "idle" || status === "processing") && (
          <>
            {status !== "processing" && (
              <line
                x1={center}
                y1={center}
                x2={center}
                y2={center - radius * 0.4}
                stroke={currentColor}
                strokeWidth={hourHandWidth}
                strokeLinecap="round"
                style={{
                  transformOrigin: `${center}px ${center}px`,
                  transform: `rotate(${hourAngle}deg)`,
                  transition: "transform 1s ease-out",
                }}
              />
            )}

            <line
              x1={center}
              y1={center}
              x2={center}
              y2={center - radius * 0.7}
              stroke={currentColor}
              strokeWidth={minuteHandWidth}
              strokeLinecap="round"
              style={{
                transformOrigin: `${center}px ${center}px`,
                transform: `rotate(${minuteAngle}deg)`,
                transition:
                  status === "processing"
                    ? "none"
                    : "transform 0.6s ease-out 0.1s",
              }}
            />
          </>
        )}

        {status === "success" && (
          <g
            style={{
              animation: "scaleFromCenter 0.4s ease-out",
              transformOrigin: `${center}px ${center}px`,
            }}
          >
            <polyline
              points={`${center - radius * 0.3},${center + radius * 0.1} ${
                center - radius * 0.1
              },${center + radius * 0.3} ${center + radius * 0.3},${
                center - radius * 0.2
              }`}
              fill="none"
              stroke={currentColor}
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </g>
        )}

        {status === "error" && (
          <g
            style={{
              animation: "scaleFromCenter 0.4s ease-out",
              transformOrigin: `${center}px ${center}px`,
            }}
          >
            <line
              x1={center - radius * 0.2}
              y1={center - radius * 0.2}
              x2={center + radius * 0.2}
              y2={center + radius * 0.2}
              stroke={currentColor}
              strokeWidth={2}
              strokeLinecap="round"
            />
            <line
              x1={center + radius * 0.2}
              y1={center - radius * 0.2}
              x2={center - radius * 0.2}
              y2={center + radius * 0.2}
              stroke={currentColor}
              strokeWidth={2}
              strokeLinecap="round"
            />
          </g>
        )}
      </svg>

      <style jsx>{`
        @keyframes rotateSlowly {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes rotateFast {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }

        @keyframes shake {
          0%,
          100% {
            transform: translateX(0);
          }
          25% {
            transform: translateX(-1px);
          }
          75% {
            transform: translateX(1px);
          }
        }

        @keyframes scaleFromCenter {
          from {
            opacity: 0;
            transform: scale(0);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
      `}</style>
    </div>
  );
};

export default AnalogClock;
