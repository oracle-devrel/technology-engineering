"use client";

import { useId } from "react";
import { motion } from "framer-motion";

export default function OracleLogo({ accentColor = "#C74634", isDarkBg = false, maxHeight = 100, style }) {
  const bg = isDarkBg ? "#1a1a1a" : "#ffffff";
  const rawId = useId();
  const uid = rawId.replace(/:/g, "");
  const leftId = `clip-left-${uid}`;
  const rightId = `clip-right-${uid}`;

  const leftTransition = { type: "spring", stiffness: 45, damping: 13, mass: 1.2 };
  const rightTransition = { type: "spring", stiffness: 45, damping: 13, mass: 1.2, delay: 0.08 };

  return (
    <svg
      viewBox="0 0 680 400"
      fill="none"
      style={{ maxHeight, width: "auto", userSelect: "none", overflow: "visible", ...style }}
    >
      <defs>
        <clipPath id={leftId}>
          <path d="M-100 -100 L240 -100 Q300 -100 300 -40 L300 440 Q300 500 240 500 L-100 500 Z" />
        </clipPath>
        <clipPath id={rightId}>
          <path d="M440 -100 L780 -100 L780 500 L440 500 Q380 500 380 440 L380 -40 Q380 -100 440 -100 Z" />
        </clipPath>
      </defs>

      <line x1="190" y1="0" x2="190" y2="400" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />
      <line x1="340" y1="0" x2="340" y2="400" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />
      <line x1="490" y1="0" x2="490" y2="400" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />
      <line x1="0" y1="120" x2="680" y2="120" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />
      <line x1="0" y1="200" x2="680" y2="200" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />
      <line x1="0" y1="280" x2="680" y2="280" stroke={accentColor} strokeWidth="0.5" strokeDasharray="6 4" opacity="0.25" />

      <motion.g
        clipPath={`url(#${leftId})`}
        initial={{ x: -600 }}
        animate={{ x: 0 }}
        transition={leftTransition}
      >
        <rect x="80" y="30" width="520" height="340" rx="170" ry="170" stroke="none" fill={accentColor} opacity="0.10" />
        <rect x="135" y="78" width="410" height="244" rx="122" ry="122" stroke="none" fill={bg} opacity="1" />
        <rect x="110" y="55" width="460" height="290" rx="145" ry="145" stroke="none" fill={accentColor} opacity="0.25" />
        <rect x="160" y="98" width="360" height="204" rx="102" ry="102" stroke="none" fill={bg} opacity="1" />
        <rect x="140" y="80" width="400" height="240" rx="120" ry="120" stroke="none" fill={accentColor} opacity="0.85" />
        <rect x="185" y="118" width="310" height="164" rx="82" ry="82" stroke="none" fill={bg} opacity="1" />
      </motion.g>

      <motion.g
        clipPath={`url(#${rightId})`}
        initial={{ x: 600 }}
        animate={{ x: 0 }}
        transition={rightTransition}
      >
        <rect x="80" y="30" width="520" height="340" rx="170" ry="170" stroke="none" fill={accentColor} opacity="0.10" />
        <rect x="135" y="78" width="410" height="244" rx="122" ry="122" stroke="none" fill={bg} opacity="1" />
        <rect x="110" y="55" width="460" height="290" rx="145" ry="145" stroke="none" fill={accentColor} opacity="0.25" />
        <rect x="160" y="98" width="360" height="204" rx="102" ry="102" stroke="none" fill={bg} opacity="1" />
        <rect x="140" y="80" width="400" height="240" rx="120" ry="120" stroke="none" fill={accentColor} opacity="0.85" />
        <rect x="185" y="118" width="310" height="164" rx="82" ry="82" stroke="none" fill={bg} opacity="1" />
      </motion.g>

      <circle cx="260" cy="200" r="120" stroke={accentColor} strokeWidth="0.4" strokeDasharray="4 6" fill="none" opacity="0.15" />
      <circle cx="420" cy="200" r="120" stroke={accentColor} strokeWidth="0.4" strokeDasharray="4 6" fill="none" opacity="0.15" />
    </svg>
  );
}
