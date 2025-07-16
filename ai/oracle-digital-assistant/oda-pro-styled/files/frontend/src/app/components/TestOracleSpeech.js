"use client";

import { Box, Button, Chip, Paper, Typography } from "@mui/material";
import { Mic, MicOff } from "lucide-react";
import { useEffect, useState } from "react";
import createOracleSpeechService from "../services/oracleSpeechService";

export default function TestOracleSpeech() {
  const [speechService, setSpeechService] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState("");
  const [serviceState, setServiceState] = useState({});

  useEffect(() => {
    const service = createOracleSpeechService();
    setSpeechService(service);

    if (!service.isSupported()) {
      setError("Tu navegador no soporta las APIs necesarias");
    }

    const interval = setInterval(() => {
      if (service.getState) {
        setServiceState(service.getState());
      }
    }, 1000);

    return () => {
      clearInterval(interval);
      if (service) {
        service.disconnect();
      }
    };
  }, []);

  const addLog = (message, type = "info") => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { timestamp, message, type }]);
  };

  const handleStartRecording = async () => {
    if (!speechService) return;

    setError("");
    setTranscript("");
    addLog("Iniciando grabación...", "info");

    try {
      const success = await speechService.startRecording(
        (result) => {
          addLog(
            `Transcripción: "${result.transcript}" (Final: ${result.isFinal})`,
            "success"
          );
          if (result.isFinal) {
            setTranscript((prev) => prev + " " + result.transcript);
          }
        },
        (error) => {
          addLog(`Error: ${error}`, "error");
          setError(error);
          setIsRecording(false);
        }
      );

      if (success) {
        setIsRecording(true);
        addLog("Grabación iniciada exitosamente", "success");
      } else {
        addLog("Fallo al iniciar grabación", "error");
      }
    } catch (err) {
      addLog(`Error no capturado: ${err.message}`, "error");
      setError(err.message);
    }

    if (speechService.getState) {
      setServiceState(speechService.getState());
    }
  };

  const handleStopRecording = async () => {
    if (!speechService) return;

    addLog("Deteniendo grabación...", "info");
    await speechService.stopRecording();
    setIsRecording(false);
    addLog("Grabación detenida", "info");

    if (speechService.getState) {
      setServiceState(speechService.getState());
    }
  };

  const clearLogs = () => {
    setLogs([]);
    setTranscript("");
    setError("");
  };

  return (
    <Box sx={{ p: 3, maxWidth: 800, mx: "auto" }}>
      <Typography variant="h4" gutterBottom>
        Prueba Oracle Speech Service
      </Typography>

      {/* Estado del servicio */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Estado del Servicio:
        </Typography>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap" }}>
          <Chip
            label={`Conexión: ${
              serviceState.connectionState || "desconectado"
            }`}
            color={
              serviceState.connectionState === "oracle_ready"
                ? "success"
                : "default"
            }
            size="small"
          />
          <Chip
            label={`Oracle: ${
              serviceState.isOracleReady ? "Listo" : "No listo"
            }`}
            color={serviceState.isOracleReady ? "success" : "default"}
            size="small"
          />
          <Chip
            label={`Grabando: ${serviceState.isRecording ? "Sí" : "No"}`}
            color={serviceState.isRecording ? "error" : "default"}
            size="small"
          />
          <Chip
            label={`Cola: ${serviceState.queueLength || 0} chunks`}
            size="small"
          />
        </Box>
      </Paper>

      {/* Controles */}
      <Box sx={{ display: "flex", gap: 2, mb: 3 }}>
        <Button
          variant="contained"
          color={isRecording ? "error" : "primary"}
          onClick={isRecording ? handleStopRecording : handleStartRecording}
          startIcon={isRecording ? <MicOff /> : <Mic />}
          disabled={!!error && !isRecording}
        >
          {isRecording ? "Detener" : "Grabar"}
        </Button>
        <Button variant="outlined" onClick={clearLogs}>
          Limpiar Logs
        </Button>
      </Box>

      {/* Error */}
      {error && (
        <Paper sx={{ p: 2, mb: 2, bgcolor: "error.light" }}>
          <Typography color="error">{error}</Typography>
        </Paper>
      )}

      {/* Transcripción */}
      {transcript && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="h6" gutterBottom>
            Transcripción:
          </Typography>
          <Typography>{transcript}</Typography>
        </Paper>
      )}

      {/* Logs */}
      <Paper sx={{ p: 2, maxHeight: 400, overflow: "auto" }}>
        <Typography variant="h6" gutterBottom>
          Logs:
        </Typography>
        {logs.map((log, index) => (
          <Box
            key={index}
            sx={{
              mb: 0.5,
              color:
                log.type === "error"
                  ? "error.main"
                  : log.type === "success"
                  ? "success.main"
                  : "text.primary",
            }}
          >
            <Typography
              variant="body2"
              component="span"
              sx={{ fontFamily: "monospace" }}
            >
              [{log.timestamp}] {log.message}
            </Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
}
