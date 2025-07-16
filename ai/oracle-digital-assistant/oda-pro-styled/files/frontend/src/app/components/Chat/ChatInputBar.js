"use client";

import {
  alpha,
  Box,
  IconButton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { motion } from "framer-motion";
import { FileText, Forward, Mic, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

export default function ChatInputBar({
  onSendMessage,
  onToggleSpeechRecognition,
  onSendAttachment,
  isConnected,
  isListening,
  isPreview,
  currentSpeechProvider,
}) {
  const [input, setInput] = useState("");
  const [audioLevels, setAudioLevels] = useState([0, 0, 0, 0, 0]);
  const inputRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);

  const [selectedFile, setSelectedFile] = useState(null);
  const [filePreview, setFilePreview] = useState(null);
  const fileInputRef = useRef(null);

  const theme = useTheme();

  const handleSendMessage = async () => {
    if (!isConnected) return;

    const hasText = input.trim();
    const hasFile = selectedFile;

    if (!hasText && !hasFile) return;

    if (hasFile && onSendAttachment) {
      const success = await onSendAttachment(selectedFile);
      if (!success) return;
    }

    if (hasText && onSendMessage) {
      onSendMessage(input.trim());
    }

    setInput("");
    setSelectedFile(null);
    setFilePreview(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleAttachmentClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);

      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => setFilePreview(e.target.result);
        reader.readAsDataURL(file);
      } else {
        setFilePreview(null);
      }

      event.target.value = "";
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setFilePreview(null);
  };

  const isOracleListening = currentSpeechProvider === "oracle" && isListening;

  useEffect(() => {
    if (isOracleListening) {
      const startAudioAnalysis = async () => {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({
            audio: { sampleRate: 16000, channelCount: 1 },
          });

          audioContextRef.current = new AudioContext();
          analyserRef.current = audioContextRef.current.createAnalyser();

          const source =
            audioContextRef.current.createMediaStreamSource(stream);
          source.connect(analyserRef.current);

          analyserRef.current.fftSize = 256;
          const bufferLength = analyserRef.current.frequencyBinCount;
          const dataArray = new Uint8Array(bufferLength);

          const updateLevels = () => {
            analyserRef.current.getByteFrequencyData(dataArray);

            const newLevels = [];
            const segmentSize = Math.floor(bufferLength / 5);

            for (let i = 0; i < 5; i++) {
              const start = i * segmentSize;
              const end = start + segmentSize;
              let sum = 0;

              for (let j = start; j < end; j++) {
                sum += dataArray[j];
              }

              const average = sum / segmentSize;
              const normalized = Math.min(average / 80, 3);
              newLevels.push(normalized);
            }

            setAudioLevels(newLevels);
            animationFrameRef.current = requestAnimationFrame(updateLevels);
          };

          updateLevels();
        } catch (error) {
          console.error("Error accessing microphone:", error);
        }
      };

      startAudioAnalysis();
    } else {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      setAudioLevels([0, 0, 0, 0, 0]);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
      if (
        audioContextRef.current &&
        audioContextRef.current.state !== "closed"
      ) {
        audioContextRef.current.close();
      }
    };
  }, [isOracleListening]);

  useEffect(() => {
    if (isConnected && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isConnected]);

  useEffect(() => {
    const handleFileDropped = (event) => {
      const file = event.detail;
      setSelectedFile(file);

      if (file.type.startsWith("image/")) {
        const reader = new FileReader();
        reader.onload = (e) => setFilePreview(e.target.result);
        reader.readAsDataURL(file);
      } else {
        setFilePreview(null);
      }
    };

    window.addEventListener("fileDropped", handleFileDropped);
    return () => window.removeEventListener("fileDropped", handleFileDropped);
  }, []);

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        width: "100%",
        position: "relative",
      }}
    >
      {selectedFile && (
        <Box
          sx={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: 0,
            backgroundColor: alpha("#000", 0.6),
            backdropFilter: "blur(5px)",
            borderRadius: 1,
            padding: 1,
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.1)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 0.5,
            zIndex: 10,
            width: 80,
          }}
        >
          <IconButton
            size="small"
            onClick={handleRemoveFile}
            sx={{
              position: "absolute",
              top: -6,
              right: -6,
              color: "white",
              backgroundColor: "#404040",
              width: 16,
              height: 16,
              "&:hover": { backgroundColor: "#555" },
            }}
          >
            <X size={8} />
          </IconButton>

          {filePreview ? (
            <Box
              component="img"
              src={filePreview}
              sx={{
                width: "100%",
                height: 50,
                borderRadius: 0.5,
                objectFit: "contain",
              }}
            />
          ) : (
            <Box
              sx={{
                width: "100%",
                height: 50,
                borderRadius: 0.5,
                backgroundColor: "#404040",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FileText size={20} color="white" />
            </Box>
          )}

          <Typography
            variant="caption"
            sx={{
              fontWeight: 500,
              color: "white",
              whiteSpace: "nowrap",
              overflow: "hidden",
              textOverflow: "ellipsis",
              display: "block",
              maxWidth: 70,
              textAlign: "center",
              fontSize: "0.65rem",
            }}
          >
            {selectedFile.name}
          </Typography>
        </Box>
      )}

      <motion.div
        layout
        style={{
          borderRadius: 24,
          backgroundColor: "white",
          boxShadow: "0 8px 24px -8px rgba(0, 0, 0, 0.15)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          padding: 4,
          display: "flex",
          alignItems: "center",
          width: isOracleListening ? "auto" : "100%",
          maxWidth: "md",
          minHeight: 47,
        }}
        transition={{
          type: "spring",
          stiffness: 300,
          damping: 25,
        }}
      >
        {/* {!isOracleListening && (
          <IconButton
            onClick={handleAttachmentClick}
            disabled={!isConnected}
            title="Share attachment"
            sx={{
              color: theme.palette.text.secondary,
              "&:hover": {
                backgroundColor: theme.palette.primary.main + "14",
              },
              "&:disabled": {
                color: theme.palette.text.disabled,
              },
              mr: 1,
            }}
          >
            <Paperclip size={18} />
          </IconButton>
        )} */}
        {!isOracleListening && (
          <TextField
            size="small"
            fullWidth
            variant="standard"
            placeholder="Start with a message..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!isConnected || isListening}
            multiline
            maxRows={4}
            inputRef={inputRef}
            slotProps={{
              input: {
                disableUnderline: true,
                sx: {
                  color: theme.palette.text.primary,
                  "::placeholder": {
                    color: theme.palette.text.secondary,
                  },
                },
              },
            }}
            sx={{ pl: 2, pr: 2, py: 0.5 }}
          />
        )}
        <Stack direction="row" spacing={1} alignItems="center">
          <IconButton
            onClick={onToggleSpeechRecognition}
            disabled={!isConnected}
            title={isListening ? "Stop recording" : "Start voice recording"}
            sx={{
              color: isListening ? "white" : theme.palette.text.secondary,
              backgroundColor: isListening
                ? theme.palette.error.main
                : "transparent",
              "&:hover": {
                backgroundColor: isListening
                  ? theme.palette.error.dark
                  : theme.palette.primary.main + "14",
              },
              "&:disabled": {
                color: theme.palette.text.disabled,
              },
            }}
          >
            {isOracleListening ? (
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "1px",
                  width: 18,
                  height: 18,
                  overflow: "hidden",
                }}
              >
                {[2, 1, 0, 1, 2].map((position, index) => (
                  <motion.div
                    key={index}
                    style={{
                      width: 2,
                      backgroundColor: "white",
                      borderRadius: 1,
                      height: 4 + audioLevels[position] * 10,
                    }}
                    animate={{
                      height: 4 + audioLevels[position] * 10,
                    }}
                    transition={{
                      duration: 0.1,
                      ease: "easeOut",
                    }}
                  />
                ))}
              </Box>
            ) : (
              <Mic size={18} />
            )}
          </IconButton>
          {!isOracleListening && (
            <IconButton
              onClick={handleSendMessage}
              disabled={
                !isPreview && (!isConnected || (!input.trim() && !selectedFile))
              }
              title="Send message"
              sx={{
                backgroundColor: theme.palette.primary.main,
                color: theme.palette.primary.contrastText,
                "&:hover": {
                  backgroundColor: theme.palette.primary.dark,
                },
                "&:disabled": {
                  backgroundColor: theme.palette.action.disabled,
                  color: theme.palette.action.disabledBackground,
                },
              }}
            >
              <Forward
                size={16}
                style={{ paddingBottom: 2.5, paddingLeft: 2 }}
              />
            </IconButton>
          )}
        </Stack>
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*,.pdf"
          style={{ display: "none" }}
          onChange={handleFileSelect}
        />
      </motion.div>
    </Box>
  );
}
