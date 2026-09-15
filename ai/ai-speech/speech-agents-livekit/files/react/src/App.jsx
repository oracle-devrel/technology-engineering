import { useState, useCallback, useMemo } from "react";
import {
  LiveKitRoom,
  useVoiceAssistant,
  BarVisualizer,
  RoomAudioRenderer,
  VoiceAssistantControlBar,
  useLocalParticipant,
  useTranscriptions,
} from "@livekit/components-react";
import "@livekit/components-styles";

const SERVER_URL = "ws://localhost:7880";
const TOKEN_SERVER = "http://localhost:8000/api/token";

function TranscriptPanel() {
  const transcriptions = useTranscriptions() ?? [];
  const { localParticipant } = useLocalParticipant();

  const messages = useMemo(() => {
    return transcriptions
      .flatMap((t, idx) => {
       const identity =
        t.participantInfo?.identity ||
        t.participantIdentity ||
        t.identity ||
        "unknown";

        const textFromTopLevel = (t.text ?? "").trim();
        const segmentText =
          (t.segments ?? [])
            .map((s) => (s.text ?? "").trim())
            .filter(Boolean)
            .join(" ")
            .trim();

        const text = textFromTopLevel || segmentText;
        if (!text) return [];
        console.log("transcriptions raw", transcriptions);
        console.log("local identity", localParticipant?.identity);

        return [
          {
            id: `${identity}-${t.trackSid || t.track_sid || idx}-${idx}`,
            text,
            isYou: identity === localParticipant?.identity,
            identity,
          },
        ];
      })
      .filter(Boolean);
  }, [transcriptions, localParticipant?.identity]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "0.6rem",
        padding: "0.75rem",
        background: "var(--color-background-secondary)",
        borderRadius: 12,
        minHeight: 220,
        maxHeight: 260,
        overflowY: "auto",
      }}
    >
      {messages.length === 0 ? (
        <div style={{ color: "var(--color-text-tertiary)", fontSize: 14 }}>
          Transcript will appear here...
        </div>
      ) : (
        messages.map((m) => (
          <div
            key={m.id}
            style={{
              alignSelf: m.isYou ? "flex-end" : "flex-start",
              maxWidth: "85%",
              padding: "0.8rem 1rem",
              borderRadius: m.isYou
                ? "18px 18px 4px 18px"
                : "18px 18px 18px 4px",
              background: m.isYou ? "#111827" : "#eef2ff",
              color: m.isYou ? "#fff" : "#111827",
              whiteSpace: "pre-wrap",
              lineHeight: 1.4,
              boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
              fontSize: 14,
            }}
          >
            {m.text}
          </div>
        ))
      )}
    </div>
  );
}

function VoiceAssistant() {
  const { state, audioTrack } = useVoiceAssistant();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
      <p style={{ margin: 0, fontSize: 15 }}>
        Agent state: <strong>{state}</strong>
      </p>

      <BarVisualizer
        state={state}
        barCount={12}
        trackRef={audioTrack}
        style={{ height: 80 }}
      />

      <TranscriptPanel />

      <VoiceAssistantControlBar />
      <RoomAudioRenderer />
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(null);

  const connect = useCallback(async () => {
    const res = await fetch(TOKEN_SERVER, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        room_name: "demo-room",
        participant_identity: "user",
        participant_name: "Web User",
      }),
    });

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`Token server error: ${res.status} ${text}`);
    }

    const data = await res.json();
    setToken(data.participant_token);
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--color-background-tertiary)",
        fontFamily: "var(--font-sans)",
      }}
    >
      <div
        style={{
          background: "var(--color-background-primary)",
          border: "0.5px solid var(--color-border-tertiary)",
          borderRadius: 12,
          padding: "2rem",
          width: "100%",
          maxWidth: 520,
        }}
      >
        <h2 style={{ fontSize: 18, fontWeight: 500, marginBottom: "0.25rem" }}>
          Voice Assistant
        </h2>
        <p
          style={{
            fontSize: 14,
            color: "var(--color-text-secondary)",
            marginBottom: "1.5rem",
          }}
        >
          Powered by Oracle OCI + LiveKit
        </p>

        {!token ? (
          <button
            onClick={connect}
            style={{
              width: "100%",
              padding: "0.75rem",
              borderRadius: 8,
              border: "0.5px solid var(--color-border-secondary)",
              background: "transparent",
              cursor: "pointer",
              fontSize: 15,
            }}
          >
            Connect
          </button>
        ) : (
          <LiveKitRoom
            token={token}
            serverUrl={SERVER_URL}
            connect={true}
            audio={true}
            video={false}
          >
            <VoiceAssistant />
          </LiveKitRoom>
        )}
      </div>
    </div>
  );
}