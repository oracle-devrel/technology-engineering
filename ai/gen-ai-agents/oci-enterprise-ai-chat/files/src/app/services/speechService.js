const createSpeechService = () => {
  let recognition = null;

  const isSupported = () => {
    return "SpeechRecognition" in window || "webkitSpeechRecognition" in window;
  };

  const startListening = (onResult, onError) => {
    if (!isSupported()) {
      onError("Speech recognition is not supported in your browser");
      return false;
    }

    try {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SpeechRecognition();

      recognition.lang = "en-US";
      recognition.interimResults = true;
      recognition.continuous = false;

      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((result) => result[0])
          .map((result) => result.transcript)
          .join("");

        onResult({
          transcript,
          isFinal: event.results[event.results.length - 1].isFinal,
        });
      };

      recognition.onend = () => {
        onResult({ stopped: true });
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error", event);
        onError(event.error);
      };

      recognition.start();
      return true;
    } catch (err) {
      console.error("Error starting speech recognition:", err);
      onError(err.message);
      return false;
    }
  };

  const stopListening = () => {
    if (recognition) {
      recognition.stop();
      recognition = null;
      return true;
    }
    return false;
  };

  return {
    isSupported,
    startListening,
    stopListening,
  };
};

export default createSpeechService;
