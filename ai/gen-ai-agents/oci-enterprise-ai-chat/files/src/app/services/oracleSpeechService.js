"use client";

const createOracleSpeechService = () => {
  let ws = null;
  let mediaRecorder = null;
  let mediaStream = null;
  let isRecording = false;

  const startRecording = async (onResult, onError) => {
    try {
      ws = new WebSocket("ws://localhost:3001/ws/speech");

      ws.onopen = () => {};
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "ready") {
        }
        if (data.type === "transcription") {
          onResult({ transcript: data.text, isFinal: data.isFinal });
        } else if (data.type === "error") {
          console.error("[Cliente] Oracle WS error:", data.message);
          onError(data.message);
        }
      };
      ws.onerror = (err) => {
        console.error("[Cliente][oracleSpeechService] 🔴 WS error:", err);
        onError("WebSocket error");
      };
      ws.onclose = (ev) => {};

      await new Promise((resolve) => {
        ws.onopen = resolve;
      });

      mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: { sampleRate: 16000, channelCount: 1 },
      });

      mediaRecorder = new MediaRecorder(mediaStream);
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
          event.data.arrayBuffer().then((buffer) => {
            ws.send(buffer);
          });
        }
      };
      mediaRecorder.onstart = () =>
        (mediaRecorder.onstop = () =>
          (mediaRecorder.onerror = (e) =>
            console.error("[Cliente] Recorder error:", e)));

      mediaRecorder.start(500);
      isRecording = true;
      return true;
    } catch (error) {
      console.error("[Cliente] startRecording error:", error);
      onError(error.message);
      return false;
    }
  };

  const stopRecording = () => {
    if (mediaRecorder) mediaRecorder.stop();
    if (mediaStream) mediaStream.getTracks().forEach((t) => t.stop());
    if (ws) ws.close();
    isRecording = false;
    return true;
  };

  const isSupported = () =>
    !!(navigator.mediaDevices && window.MediaRecorder && window.WebSocket);

  return {
    isSupported,
    startRecording,
    stopRecording,
    isRecording: () => isRecording,
  };
};

export default createOracleSpeechService;
