"use client";

import {
  Add,
  AttachFile,
  BugReport,
  CheckCircle,
  Close,
  InfoOutlined,
  RemoveCircle,
  Rule,
  TextFields,
  UploadFile,
} from "@mui/icons-material";
import {
  alpha,
  Avatar,
  Box,
  CircularProgress,
  Container,
  Fab,
  IconButton,
  Stack,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import {
  evaluateDocuments,
  uploadDocuments,
} from "../../services/documentEvaluationService";
import AnalysisResult from "./AnalysisResult";
import CriteriaIndicators from "./CriteriaIndicators";
import FancyButton from "./FancyButton";
import DropZone from "./ui/DropZone";

export default function AIChat() {
  const WIDTH_IDLE = 500;
  const WIDTH_COMPACT = 450;
  const WIDTH_RESULT = 510;

  const theme = useTheme();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("idle"); // idle, in_progress, complete, error

  const [attachedFiles, setAttachedFiles] = useState([]);
  const [additionalInstructions, setAdditionalInstructions] = useState("");
  const [criteriaMode, setCriteriaMode] = useState("manual");
  const [manualCriteria, setManualCriteria] = useState([
    { key: "", value: "" },
  ]);
  const [csvFile, setCsvFile] = useState(null);

  const [response, setResponse] = useState("");
  const [expanded, setExpanded] = useState(false);
  const isSubmitting = useRef(false);
  const newCriteriaRef = useRef(null);

  // Capture submission data for display
  const [submissionData, setSubmissionData] = useState({
    files: [],
    criteria: null,
    instructions: "",
  });

  const computeRadius = () => (loading || response ? 40 : 32);
  const computeWidth = () => {
    if (loading) return WIDTH_COMPACT;
    if (response) return WIDTH_RESULT;
    return WIDTH_IDLE;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!attachedFiles.length) return;
    isSubmitting.current = true;
    setLoading(true);
    setStatus("in_progress");

    // Capture submission data for display
    const fileNames = attachedFiles.map((file) => file.name);
    let criteriaDisplay = null;

    if (criteriaMode === "csv" && csvFile) {
      criteriaDisplay = { type: "csv", name: csvFile.name };
    } else if (criteriaMode === "manual") {
      const validCriteria = manualCriteria.filter((c) => c.key.trim());
      if (validCriteria.length > 0) {
        criteriaDisplay = {
          type: "manual",
          criteria: validCriteria.reduce((acc, curr) => {
            acc[curr.key] = curr.value;
            return acc;
          }, {}),
        };
      }
    }

    setSubmissionData({
      files: fileNames,
      criteria: criteriaDisplay,
      instructions: additionalInstructions,
    });

    try {
      // Upload documents first
      const uploadResult = await uploadDocuments(attachedFiles);
      console.log("Upload result:", uploadResult);

      // Prepare criteria for evaluation
      let criteriaFile = null;
      let criteriaJson = null;

      if (criteriaMode === "csv" && csvFile) {
        criteriaFile = csvFile;
      } else if (criteriaMode === "manual") {
        const validCriteria = manualCriteria.filter((c) => c.key.trim());
        if (validCriteria.length > 0) {
          criteriaJson = validCriteria.reduce((acc, curr) => {
            acc[curr.key] = curr.value;
            return acc;
          }, {});
        }
      }

      // Evaluate documents
      const evaluationResult = await evaluateDocuments(
        criteriaFile,
        criteriaJson,
        additionalInstructions
      );
      console.log("Evaluation result:", evaluationResult);

      setResponse(evaluationResult.evaluation || "Evaluation complete");
      setStatus("complete");
    } catch (error) {
      console.error("Error during evaluation:", error);
      setResponse("Unexpected error during evaluation");
      setStatus("error");
    } finally {
      setLoading(false);
      isSubmitting.current = false;
    }
  };

  const handleNew = () => {
    setAttachedFiles([]);
    setAdditionalInstructions("");
    setManualCriteria([{ key: "", value: "" }]);
    setCsvFile(null);
    setCriteriaMode("manual");
    setResponse("");
    setExpanded(false);
    setSubmissionData({ files: [], criteria: null, instructions: "" });
    setStatus("idle");
  };

  const handleAddCriteria = () => {
    setManualCriteria([...manualCriteria, { key: "", value: "" }]);
  };

  useEffect(() => {
    if (newCriteriaRef.current) {
      setTimeout(() => {
        newCriteriaRef.current.focus();
      }, 100);
    }
  }, [manualCriteria.length]);

  const handleRemoveCriteria = (index) => {
    setManualCriteria(manualCriteria.filter((_, i) => i !== index));
  };

  const handleCriteriaChange = (index, field, value) => {
    const newCriteria = [...manualCriteria];
    newCriteria[index][field] = value;
    setManualCriteria(newCriteria);
  };

  const handleCsvUpload = (file) => {
    setCsvFile(file);
  };

  const handleMockEvaluate = async () => {
    setLoading(true);
    setStatus("in_progress");

    // Generate mock data
    const mockFiles =
      attachedFiles.length > 0
        ? attachedFiles.map((file) => file.name)
        : ["Document1.pdf", "Document2.docx", "Document3.txt"];

    const mockCriteria =
      criteriaMode === "csv" && csvFile
        ? { type: "csv", name: csvFile.name }
        : criteriaMode === "manual" && manualCriteria.some((c) => c.key.trim())
        ? {
            type: "manual",
            criteria: manualCriteria
              .filter((c) => c.key.trim())
              .reduce((acc, curr) => {
                acc[curr.key] = curr.value;
                return acc;
              }, {}),
          }
        : {
            type: "manual",
            criteria: {
              Quality: "High",
              Relevance: "Strong",
              Structure: "Excellent",
            },
          };

    setSubmissionData({
      files: mockFiles,
      criteria: mockCriteria,
      instructions:
        additionalInstructions || "Mock evaluation for development testing",
    });

    // Mock evaluation with timeout
    await new Promise((resolve) => setTimeout(resolve, 3000));

    const mockResponse = `## Evaluation Results for ${mockFiles.join(", ")}
    
**Best Document:** ${mockFiles[0]}

This document excels in meeting the evaluation criteria with superior structure and content quality.

### Ranking:
1. **${mockFiles[0]}** - Excellent overall quality
${mockFiles
  .slice(1)
  .map(
    (file, index) =>
      `${index + 2}. **${file}** - Good quality with minor improvements needed`
  )
  .join("\n")}

### Key Findings:
- Strong adherence to requirements
- Well-structured content
- Clear and comprehensive information
- Professional presentation

### Criteria Analysis:
${Object.entries(
  mockCriteria.type === "manual"
    ? mockCriteria.criteria
    : { "CSV Criteria": mockCriteria.name }
)
  .map(([key, value]) => `- **${key}**: ${value}`)
  .join("\n")}

### Eligibility Summary Table

| Applicant Name | Completeness | Financial Sufficiency | Passport Validity | Employment/Sponsorship Validity | Category |
|---------------------|--------------------|-----------------------|-------------------|---------------------------------|-------------------|
| Kelly Cruz | Yes | Yes | Yes | Yes | Eligible |
| David Jenkins | Yes | Info not available | Yes | Yes | Requires Review |
| Tiffany Hernandez | Yes | Yes | Yes | Yes | Eligible |

This is a mock evaluation for development purposes.`;

    setResponse(mockResponse);
    setStatus("complete");
    setLoading(false);
  };

  const handleFileRemove = (index) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  };

  const handleMockEvaluateError = async () => {
    setLoading(true);
    setStatus("in_progress");

    // Generate mock data
    const mockFiles =
      attachedFiles.length > 0
        ? attachedFiles.map((file) => file.name)
        : ["Document1.pdf", "Document2.docx", "Document3.txt"];

    const mockCriteria =
      criteriaMode === "csv" && csvFile
        ? { type: "csv", name: csvFile.name }
        : criteriaMode === "manual" && manualCriteria.some((c) => c.key.trim())
        ? {
            type: "manual",
            criteria: manualCriteria
              .filter((c) => c.key.trim())
              .reduce((acc, curr) => {
                acc[curr.key] = curr.value;
                return acc;
              }, {}),
          }
        : {
            type: "manual",
            criteria: {
              Quality: "High",
              Relevance: "Strong",
              Structure: "Excellent",
            },
          };

    setSubmissionData({
      files: mockFiles,
      criteria: mockCriteria,
      instructions:
        additionalInstructions || "Mock evaluation for development testing",
    });

    // Mock evaluation with timeout
    await new Promise((resolve) => setTimeout(resolve, 3000));

    // Set error response
    setResponse(
      "Failed to evaluate documents: Connection timeout. The backend service is not responding. Please try again later."
    );
    setStatus("error");
    setLoading(false);
  };

  const handleDrop = (filesToAdd) => {
    if (filesToAdd.length > 0) {
      setAttachedFiles([...attachedFiles, ...filesToAdd]);
    }
  };

  const containerVariants = {
    initial: {
      width: WIDTH_IDLE,
      borderRadius: computeRadius(),
    },
    animate: {
      width: computeWidth(),
      borderRadius: computeRadius(),
    },
  };

  return (
    <Container
      maxWidth="xl"
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
      }}
    >
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <form onSubmit={handleSubmit}>
          <motion.div
            initial="initial"
            animate="animate"
            variants={containerVariants}
            transition={{ type: "spring", stiffness: 500, damping: 30 }}
            style={{
              background: theme.palette.background.default,
              color: theme.palette.text.primary,
              padding: loading || response ? 10 : 20,
              overflow: "hidden",
              display: "flex",
              flexDirection: "column",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.15)",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                gap: 3,
                mb: loading || response ? 0 : 2,
                alignItems: loading || response ? "center" : "flex-start",
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center" }}>
                <Avatar
                  sx={{
                    mr: 1.5,
                    bgcolor: (t) =>
                      status === "complete"
                        ? alpha(t.palette.success.main, 0.2)
                        : status === "error"
                        ? alpha(t.palette.error.main, 0.2)
                        : alpha(t.palette.primary.main, 0.2),
                    color: (t) =>
                      status === "complete"
                        ? t.palette.success.main
                        : status === "error"
                        ? t.palette.error.main
                        : t.palette.primary.main,
                    width: 44,
                    height: 44,
                  }}
                >
                  {status === "complete" ? <CheckCircle /> : <Rule />}
                </Avatar>
                <Stack direction="column" spacing={-0.1}>
                  <Typography variant="subtitle1">
                    {status === "complete"
                      ? "Evaluation Completed"
                      : status === "in_progress"
                      ? "Evaluation in Progress"
                      : status === "error"
                      ? "Evaluation Failed"
                      : "Smart Document Evaluator"}
                  </Typography>
                  {status === "idle" && !loading && !response && (
                    <Typography
                      variant="caption"
                      sx={{ color: "#9A9A9A", lineHeight: 1.2 }}
                    >
                      Compare, evaluate, and rank documents based on objective
                      criteria
                    </Typography>
                  )}
                </Stack>
              </Box>
              <AnimatePresence initial={false} exitBeforeEnter>
                {loading && (
                  <motion.div
                    key="loader"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{
                      scale: 0,
                      transition: {
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                      },
                    }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  >
                    <CircularProgress
                      size={30}
                      thickness={6}
                      sx={{
                        color: (theme) =>
                          theme.palette.mode === "light"
                            ? theme.palette.primary.main
                            : theme.palette.common.white,
                        mr: 0.6,
                        "& circle": {
                          strokeLinecap: "round",
                        },
                      }}
                    />
                  </motion.div>
                )}
                {!loading && response && (
                  <motion.div
                    key="new"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{
                      scale: 0,
                      transition: {
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                      },
                    }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  >
                    <FancyButton
                      type="button"
                      variant="contained"
                      onClick={handleNew}
                      sx={{ textTransform: "none", mr: 0.6 }}
                    >
                      {status === "error" ? "Try again" : "New evaluation"}
                    </FancyButton>
                  </motion.div>
                )}
                {!loading && !response && (
                  <motion.div
                    key="btn"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    exit={{
                      scale: 0,
                      transition: {
                        type: "spring",
                        stiffness: 500,
                        damping: 30,
                      },
                    }}
                    transition={{ type: "spring", stiffness: 500, damping: 30 }}
                  >
                    <FancyButton
                      type="submit"
                      variant="contained"
                      disabled={
                        !attachedFiles.length ||
                        (criteriaMode === "manual"
                          ? !manualCriteria.some(
                              (c) => c.key.trim() && c.value.trim()
                            )
                          : !csvFile)
                      }
                      pulseEnabled={
                        attachedFiles.length > 0 &&
                        (criteriaMode === "manual"
                          ? manualCriteria.some(
                              (c) => c.key.trim() && c.value.trim()
                            )
                          : csvFile)
                      }
                      sx={{
                        textTransform: "none",
                        animation:
                          !attachedFiles.length ||
                          (criteriaMode === "manual"
                            ? !manualCriteria.some(
                                (c) => c.key.trim() && c.value.trim()
                              )
                            : !csvFile)
                            ? "none"
                            : "pulse 2s ease-in-out infinite",
                        "@keyframes pulse": {
                          "0%, 100%": { transform: "scale(1)", opacity: 1 },
                          "50%": { transform: "scale(1.02)", opacity: 0.9 },
                        },
                      }}
                    >
                      Evaluate
                    </FancyButton>
                  </motion.div>
                )}
              </AnimatePresence>
            </Box>
            {!loading && !response && (
              <Stack spacing={3}>
                <Box>
                  <DropZone
                    onDrop={handleDrop}
                    onFileSelect={(files) => {
                      const maxFiles = 5;
                      const remainingSlots = maxFiles - attachedFiles.length;
                      const filesToAdd = files.slice(0, remainingSlots);

                      if (filesToAdd.length > 0) {
                        setAttachedFiles([...attachedFiles, ...filesToAdd]);
                      }
                    }}
                    accept="*/*"
                    multiple={true}
                    placeholder="Drop files here or click to attach"
                    description="Up to 5 documents"
                    dragPlaceholder="Drop files here"
                    icon={AttachFile}
                    disabled={attachedFiles.length >= 5}
                    showFileCount={true}
                    maxFiles={5}
                    currentFileCount={attachedFiles.length}
                  />

                  <AnimatePresence>
                    {attachedFiles.length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <Box
                          sx={{
                            background: (theme) =>
                              theme.palette.background.paper,
                            borderRadius: "16px",
                            border: "1px solid rgba(255, 255, 255, 0.05)",
                            p: 2,
                            mt: 2,
                          }}
                        >
                          <Box
                            sx={{
                              display: "flex",
                              flexDirection: "column",
                              gap: 1,
                            }}
                          >
                            <AnimatePresence>
                              {attachedFiles.map((file, index) => (
                                <motion.div
                                  key={file.name + index}
                                  initial={{
                                    opacity: 0,
                                    scale: 0.8,
                                    height: 0,
                                  }}
                                  animate={{
                                    opacity: 1,
                                    scale: 1,
                                    height: "auto",
                                  }}
                                  exit={{ opacity: 0, scale: 0.8, height: 0 }}
                                  transition={{ duration: 0.2 }}
                                >
                                  <Box
                                    sx={{
                                      display: "flex",
                                      alignItems: "center",
                                      justifyContent: "space-between",
                                      p: 1.5,
                                      background: "rgba(255, 255, 255, 0.03)",
                                      borderRadius: "8px",
                                      transition: "all 0.2s ease",
                                      "&:hover": {
                                        background: "rgba(255, 255, 255, 0.05)",
                                      },
                                    }}
                                  >
                                    <Box
                                      sx={{
                                        display: "flex",
                                        alignItems: "center",
                                        gap: 1,
                                        flex: 1,
                                        minWidth: 0,
                                      }}
                                    >
                                      <Box
                                        sx={{
                                          width: 8,
                                          height: 8,
                                          borderRadius: "50%",
                                          background:
                                            "linear-gradient(135deg, #34C759 0%, #30D158 100%)",
                                          flexShrink: 0,
                                        }}
                                      />
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          color: (theme) =>
                                            theme.palette.text.primary,
                                          fontSize: "0.875rem",
                                          overflow: "hidden",
                                          textOverflow: "ellipsis",
                                          whiteSpace: "nowrap",
                                          flex: 1,
                                          minWidth: 0,
                                          maxWidth: "60%",
                                        }}
                                      >
                                        {file.name}
                                      </Typography>
                                      <Typography
                                        variant="caption"
                                        sx={{
                                          color: (theme) =>
                                            theme.palette.text.secondary,
                                          fontSize: "0.75rem",
                                          flexShrink: 0,
                                          ml: "auto",
                                          mr: 2,
                                        }}
                                      >
                                        {(file.size / 1024).toFixed(1)} KB
                                      </Typography>
                                    </Box>
                                    <IconButton
                                      size="small"
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        handleFileRemove(index);
                                      }}
                                      sx={{
                                        p: 0.5,
                                        color: (theme) =>
                                          theme.palette.grey[700],
                                        transition: "all 0.2s ease",
                                        "&:hover": {
                                          color: (theme) =>
                                            theme.palette.error.main,
                                          background: "rgba(255, 69, 58, 0.1)",
                                        },
                                      }}
                                    >
                                      <Close fontSize="small" />
                                    </IconButton>
                                  </Box>
                                </motion.div>
                              ))}
                            </AnimatePresence>
                          </Box>
                        </Box>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Box>

                <Box>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      mb: 1.5,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{ color: (theme) => theme.palette.text.secondary }}
                    >
                      Criteria
                    </Typography>
                    <Tooltip
                      title="Define the evaluation criteria for comparing documents. Use manual input for custom key-value pairs or upload a CSV file with predefined criteria."
                      placement="top"
                      arrow
                    >
                      <InfoOutlined
                        sx={{
                          fontSize: 16,
                          color: (theme) => theme.palette.text.disabled,
                          cursor: "pointer",
                          "&:hover": {
                            color: (theme) => theme.palette.text.secondary,
                          },
                        }}
                      />
                    </Tooltip>
                  </Box>
                  <ToggleButtonGroup
                    value={criteriaMode}
                    exclusive
                    onChange={(e, newMode) =>
                      newMode && setCriteriaMode(newMode)
                    }
                    size="small"
                    sx={{
                      mb: 2,
                      "& .MuiToggleButton-root": {
                        background: (theme) => theme.palette.background.paper,
                        color: (theme) => theme.palette.text.secondary,
                        border: (theme) => `1px solid ${theme.palette.divider}`,
                        textTransform: "none",
                        px: 2,
                        "&.Mui-selected": {
                          background: (theme) =>
                            theme.palette.success.main + "1A",
                          color: (theme) => theme.palette.success.main,
                          border: (theme) =>
                            `1px solid ${theme.palette.success.main}`,
                        },
                        "&:hover": {
                          background: (theme) => theme.palette.grey[100],
                        },
                        "&:not(:first-of-type)": {
                          borderLeft: (theme) =>
                            `1px solid ${theme.palette.divider}`,
                        },
                      },
                    }}
                  >
                    <ToggleButton value="manual">
                      <TextFields sx={{ fontSize: 18, mr: 1 }} />
                      Manual Input
                    </ToggleButton>
                    <ToggleButton value="csv">
                      <UploadFile sx={{ fontSize: 18, mr: 1 }} />
                      CSV Upload
                    </ToggleButton>
                  </ToggleButtonGroup>

                  <AnimatePresence mode="wait">
                    {criteriaMode === "manual" ? (
                      <motion.div
                        key="manual"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <Box>
                          <AnimatePresence>
                            {manualCriteria.map((criteria, index) => (
                              <motion.div
                                key={index}
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                exit={{ opacity: 0, height: 0 }}
                                transition={{ duration: 0.2 }}
                              >
                                <Box
                                  sx={{
                                    display: "flex",
                                    gap: 1,
                                    mb: 1,
                                    alignItems: "center",
                                  }}
                                >
                                  <TextField
                                    placeholder="Key"
                                    variant="outlined"
                                    size="small"
                                    value={criteria.key}
                                    onChange={(e) =>
                                      handleCriteriaChange(
                                        index,
                                        "key",
                                        e.target.value
                                      )
                                    }
                                    sx={{ flex: 1 }}
                                    inputRef={
                                      index === manualCriteria.length - 1
                                        ? newCriteriaRef
                                        : null
                                    }
                                    InputProps={{
                                      sx: {
                                        background: (theme) =>
                                          theme.palette.background.paper,
                                        borderRadius: "12px",
                                        color: (theme) =>
                                          theme.palette.text.primary,
                                        "& .MuiOutlinedInput-notchedOutline": {
                                          border: "none",
                                        },
                                      },
                                    }}
                                  />
                                  <TextField
                                    placeholder="Value"
                                    variant="outlined"
                                    size="small"
                                    value={criteria.value}
                                    onChange={(e) =>
                                      handleCriteriaChange(
                                        index,
                                        "value",
                                        e.target.value
                                      )
                                    }
                                    sx={{ flex: 1 }}
                                    InputProps={{
                                      sx: {
                                        background: (theme) =>
                                          theme.palette.background.paper,
                                        borderRadius: "12px",
                                        color: (theme) =>
                                          theme.palette.text.primary,
                                        "& .MuiOutlinedInput-notchedOutline": {
                                          border: "none",
                                        },
                                      },
                                    }}
                                  />
                                  {manualCriteria.length > 1 && (
                                    <IconButton
                                      size="small"
                                      onClick={() =>
                                        handleRemoveCriteria(index)
                                      }
                                      sx={{
                                        color: (theme) =>
                                          theme.palette.mode === "light"
                                            ? theme.palette.grey[500]
                                            : theme.palette.text.secondary,
                                        width: 32,
                                        height: 32,
                                        "&:hover": {
                                          color: (theme) =>
                                            theme.palette.error.main,
                                          background: "rgba(255, 69, 58, 0.1)",
                                        },
                                      }}
                                    >
                                      <RemoveCircle fontSize="small" />
                                    </IconButton>
                                  )}
                                </Box>
                              </motion.div>
                            ))}
                          </AnimatePresence>
                          <Box sx={{ display: "flex", mt: 1 }}>
                            <Box
                              sx={{
                                flex: 1,
                                display: "flex",
                                justifyContent: "center",
                              }}
                            >
                              <IconButton
                                size="small"
                                onClick={handleAddCriteria}
                                sx={{
                                  background: (theme) =>
                                    theme.palette.background.paper,
                                  color: (theme) => theme.palette.primary.main,
                                  p: 0.75,
                                  "&:hover": {
                                    background: (theme) =>
                                      `${theme.palette.primary.main}1A`,
                                  },
                                }}
                              >
                                <Add fontSize="small" />
                              </IconButton>
                            </Box>
                            <Box sx={{ width: "32px" }} />
                          </Box>
                        </Box>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="csv"
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <DropZone
                          onDrop={(files) => {
                            const csvFile = files.find((file) =>
                              file.name.endsWith(".csv")
                            );
                            if (csvFile) {
                              handleCsvUpload(csvFile);
                            }
                          }}
                          onFileSelect={(files) => {
                            const csvFile = files[0];
                            if (csvFile) {
                              handleCsvUpload(csvFile);
                            }
                          }}
                          accept=".csv"
                          multiple={false}
                          placeholder="Drop CSV file here or click to upload"
                          description="Format: key,value per row"
                          dragPlaceholder="Drop CSV file here"
                          icon={UploadFile}
                          selectedFile={csvFile}
                          onFileRemove={() => setCsvFile(null)}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </Box>

                <Box>
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      gap: 0.5,
                      mb: 1.5,
                    }}
                  >
                    <Typography
                      variant="body2"
                      sx={{ color: (theme) => theme.palette.text.secondary }}
                    >
                      Additional Instructions
                    </Typography>
                    <Tooltip
                      title="Provide additional context or specific instructions that will be sent to the AI during document evaluation."
                      placement="top"
                      arrow
                    >
                      <InfoOutlined
                        sx={{
                          fontSize: 16,
                          color: (theme) => theme.palette.text.disabled,
                          cursor: "pointer",
                          "&:hover": {
                            color: (theme) => theme.palette.text.secondary,
                          },
                        }}
                      />
                    </Tooltip>
                  </Box>
                  <TextField
                    fullWidth
                    variant="outlined"
                    size="small"
                    multiline
                    rows={3}
                    value={additionalInstructions}
                    onChange={(e) => setAdditionalInstructions(e.target.value)}
                    InputProps={{
                      sx: {
                        background: (theme) => theme.palette.background.paper,
                        borderRadius: "16px",
                        color: (theme) => theme.palette.text.primary,
                        "& .MuiOutlinedInput-notchedOutline": {
                          border: "none",
                        },
                      },
                    }}
                  />
                </Box>
              </Stack>
            )}
            <AnimatePresence initial={false}>
              {!loading && !response && (
                <motion.div
                  key="indicators"
                  initial={{ opacity: 0, y: -20, height: 0 }}
                  animate={{ opacity: 1, y: 0, height: "auto" }}
                  exit={{
                    opacity: 0,
                    y: -10,
                    height: 0,
                    transition: {
                      type: "spring",
                      stiffness: 500,
                      damping: 30,
                    },
                  }}
                  transition={{
                    type: "spring",
                    stiffness: 500,
                    damping: 30,
                    delay: 0.1,
                  }}
                  style={{ overflow: "hidden" }}
                >
                  <AnimatePresence>
                    {manualCriteria.filter((criteria) => criteria.key.trim())
                      .length > 0 && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <Box
                          component={motion.div}
                          sx={{
                            display: "flex",
                            justifyContent: "center",
                            mt: 3,
                            alignItems: "flex-start",
                          }}
                          animate={{
                            gap: expanded ? "112px" : "30px",
                          }}
                          transition={{
                            type: "spring",
                            stiffness: 500,
                            damping: 30,
                          }}
                        >
                          {criteriaMode === "manual" && (
                            <CriteriaIndicators
                              criteria={manualCriteria}
                              loading={loading}
                            />
                          )}
                        </Box>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </form>
      </Box>

      <AnimatePresence>
        {(loading || (response && status !== "error")) && (
          <motion.div
            initial={{ height: 0, opacity: 0, marginTop: 0 }}
            animate={{
              height: "calc(100vh - 120px)",
              width: "100%",
              opacity: 1,
              marginTop: 16,
            }}
            exit={{ height: 0, opacity: 0, marginTop: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
          >
            <AnalysisResult
              input={response}
              submissionData={submissionData}
              isError={status === "error"}
              isLoading={loading}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Mock Evaluate FAB for development */}
      <Fab
        color="secondary"
        aria-label="mock-evaluate"
        onClick={handleMockEvaluate}
        disabled={loading}
        sx={{
          position: "fixed",
          bottom: 16,
          right: 16,
          zIndex: 1000,
          backgroundColor: theme.palette.success.main,
          color: theme.palette.success.contrastText,
          "&:hover": {
            backgroundColor: theme.palette.success.dark,
          },
          "&.Mui-disabled": {
            backgroundColor: theme.palette.grey[400],
          },
        }}
      >
        <BugReport />
      </Fab>

      {/* Mock Error FAB for development */}
      <Fab
        color="error"
        aria-label="mock-evaluate-error"
        onClick={handleMockEvaluateError}
        disabled={loading}
        sx={{
          position: "fixed",
          bottom: 16,
          right: 80,
          zIndex: 1000,
          backgroundColor: theme.palette.error.main,
          color: theme.palette.error.contrastText,
          "&:hover": {
            backgroundColor: theme.palette.error.dark,
          },
          "&.Mui-disabled": {
            backgroundColor: theme.palette.grey[400],
          },
        }}
      >
        <BugReport />
      </Fab>
    </Container>
  );
}
