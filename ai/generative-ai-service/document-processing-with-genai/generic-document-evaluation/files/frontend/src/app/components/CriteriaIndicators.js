import {
  AccountTreeRounded,
  AssessmentRounded,
  FileCopyRounded,
  SecurityRounded,
  VerifiedRounded,
} from "@mui/icons-material";
import { Box } from "@mui/material";
import { AnimatePresence, motion } from "framer-motion";
import SemicircularProgress from "./DoneHeartIndicator";

export default function CriteriaIndicators({ criteria, loading }) {
  const colors = [
    "#8E8E93",
    "#34C759", 
    "#FF3B30",
    "#007AFF",
    "#FFD60A",
  ];
  
  const icons = [
    <AssessmentRounded />,
    <VerifiedRounded />,
    <SecurityRounded />,
    <AccountTreeRounded />,
    <FileCopyRounded />,
  ];
  
  const marginTops = [0, 4, 0, 4, 0];

  return (
    <AnimatePresence>
      {criteria
        .filter((criteria) => criteria.key.trim())
        .map((criteria, index) => {
          const colorIndex = index % colors.length;
          const iconIndex = index % icons.length;
          const mtIndex = index % marginTops.length;

          return (
            <motion.div
              key={index}
              layout
              initial={{ opacity: 0, scale: 0.8, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: -20 }}
              transition={{
                duration: 0.4,
                delay: index * 0.1,
                type: "spring",
                stiffness: 300,
                damping: 25,
              }}
              layoutTransition={{
                type: "spring",
                stiffness: 300,
                damping: 25,
              }}
            >
              <Box sx={{ mt: marginTops[mtIndex] }}>
                <SemicircularProgress
                  value={Math.floor(Math.random() * 30) + 70}
                  color={colors[colorIndex]}
                  icon={icons[iconIndex]}
                  bottomText={criteria.key}
                />
              </Box>
            </motion.div>
          );
        })}
    </AnimatePresence>
  );
}