"use client";

const createOracleSpeechService = () => {
  let ws = null;
  let mediaRecorder = null;
  let mediaStream = null;
  let isRecording = false;
  let isInitialized = false;

  const initialize = () => {
    isInitialized = true;
    return true;
  };

  const startRecording = async (onResult, onError) => {
    try {
      const speechServiceUrl = process.env.NEXT_PUBLIC_SPEECH_SERVICE_URL;
      ws = new WebSocket(speechServiceUrl);

      ws.onopen = () => {};
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "ready") {
        }
        if (data.type === "transcription") {
          onResult({ transcript: data.text, isFinal: data.isFinal });
        } else if (data.type === "error") {
          console.error("[Client] Oracle WS error:", data.message);

          onError(data.message);
        }
      };
      ws.onerror = (err) => {
        console.error("[Client][oracleSpeechService] 🔴 WS error:", err);
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
            console.error("[Client] Recorder error:", e)));

      mediaRecorder.start(500);
      isRecording = true;
      return true;
    } catch (error) {
      console.error("[Client] startRecording error:", error);
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

  initialize();

  return {
    isSupported,
    startRecording,
    stopRecording,
    isRecording: () => isRecording,
    initialize,
    isInitialized: () => isInitialized,
  };
};

export default createOracleSpeechService;
