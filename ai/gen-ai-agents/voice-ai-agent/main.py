import asyncio
import json
import sys
import io
import wave
import sounddevice as sd
import winsound
import oci
import numpy as np
import time

from oci.ai_speech.models import RealtimeParameters
from oci_ai_speech_realtime import RealtimeSpeechClient, RealtimeSpeechClientListener
from oci.ai_speech import AIServiceSpeechClient
from oci.ai_speech.models import (
    SynthesizeSpeechDetails, TtsOracleConfiguration,
    TtsOracleTts2NaturalModelDetails, TtsOracleTts1StandardModelDetails,
    TtsOracleSpeechSettings
)
from oci.generative_ai_agent_runtime import GenerativeAiAgentRuntimeClient
from oci.generative_ai_agent_runtime.models import ChatDetails, CreateSessionDetails

import os
from dotenv import load_dotenv
load_dotenv()
# --- Configuration ---
PROFILE = os.getenv("OCI_PROFILE", "PHOENIX")
COMPARTMENT_OCID = os.getenv("OCI_COMPARTMENT_OCID")
AGENT_ENDPOINT_ID = os.getenv("OCI_AGENT_ENDPOINT_ID")
# STT settings
STT_LANGUAGE = "en-US"
SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2
CHUNK_MS = 100
CHUNK_BYTES = (SAMPLE_RATE * CHUNK_MS // 1000) * BYTES_PER_SAMPLE

# VAD settings
VAD_THRESHOLD = 0.01      # RMS threshold for detecting speech
SILENCE_DURATION = 1.5    # Seconds of silence to stop listening
PRE_SPEECH_BUFFER = 0.5   # Seconds of audio kept just before speech starts

# --- STT Helper Classes ---

class STTListener(RealtimeSpeechClientListener):
    def __init__(self, ready_evt: asyncio.Event):
        self.ready = ready_evt
        self.final_text = ""
        self.last_partial = ""

    def on_connect(self):
        self.ready.set()

    def on_connect_message(self, message): pass
    def on_network_event(self, event): pass
    def on_ack_message(self, message): pass
    def on_error(self, error): print(f"STT Error: {error}", file=sys.stderr)

    def on_result(self, message):
        if isinstance(message, dict):
            trans = (message.get("transcriptions") or [])
            if trans:
                t0 = trans[0] or {}
                text = t0.get("transcription") or ""
                if not text:
                    return
                if t0.get("isFinal") or t0.get("final"):
                    self.final_text = text
                else:
                    self.last_partial = text

async def send_audio_to_oci(config, audio_data):
    """Send recorded audio to OCI Realtime Speech and return the transcript."""
    print(f"[STT] Sending {len(audio_data)} bytes to OCI...")
    
    region = config["region"]
    endpoint = f"wss://realtime.aiservice.{region}.oci.oraclecloud.com"

    params = RealtimeParameters(
        encoding="audio/raw;rate=16000",
        language_code=STT_LANGUAGE,
        model_type="ORACLE",
        is_ack_enabled=True,
    )

    ready = asyncio.Event()
    listener = STTListener(ready)
    client = RealtimeSpeechClient(
        config=config,
        service_endpoint=endpoint,
        realtime_speech_parameters=params,
        listener=listener,
        compartment_id=COMPARTMENT_OCID,
    )

    connect_task = asyncio.create_task(client.connect())
    try:
        await asyncio.wait_for(ready.wait(), timeout=10)
    except asyncio.TimeoutError:
        print("[STT] Timeout connecting to OCI Speech.")
        return ""

    start_msg = {"type": "start"}
    r = client.send_data(json.dumps(start_msg))
    if asyncio.iscoroutine(r): await r

    # Send audio in small chunks
    for i in range(0, len(audio_data), CHUNK_BYTES):
        chunk = audio_data[i:i+CHUNK_BYTES]
        rs = client.send_data(chunk)
        if asyncio.iscoroutine(rs): await rs
        await asyncio.sleep(0.003)

    end_msg = {"type": "end"}
    rs = client.send_data(json.dumps(end_msg))
    if asyncio.iscoroutine(rs): await rs

    try:
        rf = client.request_final_result()
        if asyncio.iscoroutine(rf): await rf
    except Exception:
        pass

    await asyncio.sleep(1.0)  # Give a moment for final result

    try:
        rc = client.close()
        if asyncio.iscoroutine(rc): await rc
    except Exception:
        pass

    if not connect_task.done():
        connect_task.cancel()
        try: await connect_task
        except asyncio.CancelledError: pass

    text = listener.final_text or listener.last_partial
    if text:
        print(f"[STT] User said: {text}")
    else:
        print("[STT] No speech detected from audio.")
    
    return text

def listen_for_speech():
    """
    Synchronous placeholder for speech listening (not used; async version below).
    """
    print("\n[VAD] Listening... (Speak now)")
    
    q = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        loop.call_soon_threadsafe(q.put_nowait, indata.copy())

    # Pre-calculate buffer sizes
    chunk_samples = int(SAMPLE_RATE * CHUNK_MS / 1000)
    pre_speech_chunks = int(PRE_SPEECH_BUFFER * 1000 / CHUNK_MS)
    silence_chunks = int(SILENCE_DURATION * 1000 / CHUNK_MS)
    
    audio_buffer = []
    pre_buffer = []
    
    is_speaking = False
    silence_counter = 0
    
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', callback=callback, blocksize=chunk_samples):
        while True:
            # Kept as placeholder; logic moved to async version.
            pass
            break 
    return b""

async def listen_for_speech_async():
    """
    Asynchronous VAD-based recording: returns raw audio bytes of a single utterance.
    """
    print("\n[VAD] Listening... (Speak now)")
    
    q = asyncio.Queue()
    loop = asyncio.get_event_loop()

    def callback(indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        loop.call_soon_threadsafe(q.put_nowait, indata.copy())

    chunk_samples = int(SAMPLE_RATE * CHUNK_MS / 1000)
    pre_speech_chunks_count = int(PRE_SPEECH_BUFFER * 1000 / CHUNK_MS)
    silence_chunks_limit = int(SILENCE_DURATION * 1000 / CHUNK_MS)
    
    audio_data = []
    pre_buffer = []
    
    is_speaking = False
    silence_counter = 0
    
    stream = sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype='int16',
        callback=callback,
        blocksize=chunk_samples
    )
    stream.start()

    try:
        while True:
            indata = await q.get()
            
            # Approximate RMS in [0,1]
            rms = np.std(indata) / 32768.0

            if is_speaking:
                audio_data.append(indata)
                if rms < VAD_THRESHOLD:
                    silence_counter += 1
                else:
                    silence_counter = 0
                
                if silence_counter >= silence_chunks_limit:
                    print(f"\n[VAD] Silence detected ({SILENCE_DURATION}s). Stopping.")
                    break
            else:
                # Waiting for speech start
                pre_buffer.append(indata)
                if len(pre_buffer) > pre_speech_chunks_count:
                    pre_buffer.pop(0)
                
                if rms > VAD_THRESHOLD:
                    print(f"\n[VAD] Speech detected! (RMS: {rms:.4f})")
                    is_speaking = True
                    audio_data.extend(pre_buffer)
                    audio_data.append(indata)
                    silence_counter = 0

    finally:
        stream.stop()
        stream.close()

    if not audio_data:
        return b""
    
    return b"".join(audio_data)

# --- Agent Helper Functions ---

def create_agent_session(config):
    print(f"[Agent] Creating session...")
    agent_runtime = GenerativeAiAgentRuntimeClient(config)
    create_session_details = CreateSessionDetails(
        description="Voice Agent Session"
    )
    session = agent_runtime.create_session(create_session_details, agent_endpoint_id=AGENT_ENDPOINT_ID)
    session_id = session.data.id
    print(f"[Agent] Session created: {session_id}")
    return session_id

def query_agent(config, user_text, session_id):
    print(f"[Agent] Thinking...")
    agent_runtime = GenerativeAiAgentRuntimeClient(config)
    
    chat_details = ChatDetails(
        user_message=user_text,
        session_id=session_id
    )

    response = agent_runtime.chat(agent_endpoint_id=AGENT_ENDPOINT_ID, chat_details=chat_details)
    
    # Save Agent's traces to JSON for debugging
    if response.data.traces:
        try:
            with open("traces.json", "w") as f:
                f.write(str(response.data.traces))
                print("[Debug] Traces saved to traces.json")
        except Exception as e:
            print(f"[Debug] Failed to save traces: {e}")

    if response.data.message and response.data.message.content:
        response_text = response.data.message.content.text
        print(f"[Agent] Response: {response_text}")
        return response_text
    
    print("[Agent] No text response. Checking for tool calls...")
    return "I am processing your request, but I couldn't find the tool execution details."

# --- TTS Helper Functions ---

def speak_text(config, text):
    if not text:
        return

    print(f"[TTS] Synthesizing...")
    tts_client = AIServiceSpeechClient(config)
    
    voices = tts_client.list_voices(compartment_id=COMPARTMENT_OCID).data.items
    if not voices:
        print("[TTS] No voices found.", file=sys.stderr)
        return
    
    v = voices[0]
    voice_id = v.voice_id
    use_tts2 = "TTS_2_NATURAL" in (v.supported_models or [])
    model_details = (
        TtsOracleTts2NaturalModelDetails(model_name="TTS_2_NATURAL", voice_id=voice_id, language_code=v.language_code)
        if use_tts2 else
        TtsOracleTts1StandardModelDetails(model_name="TTS_1_STANDARD", voice_id=voice_id)
    )
    sample_rate = int(getattr(v, "sample_rate_in_hertz", 22050))

    details = SynthesizeSpeechDetails(
        text=text,
        is_stream_enabled=False,
        compartment_id=COMPARTMENT_OCID,
        configuration=TtsOracleConfiguration(
            model_family="ORACLE",
            model_details=model_details,
            speech_settings=TtsOracleSpeechSettings(
                text_type="TEXT",
                sample_rate_in_hz=sample_rate,
                output_format="PCM"
            )
        )
    )

    resp = tts_client.synthesize_speech(details)
    pcm_bytes = resp.data.content
    
    if not pcm_bytes:
        print("[TTS] Empty audio received.")
        return

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_bytes)
    wav_bytes = buf.getvalue()

    print("[TTS] Playing...")
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
    print("[TTS] Done.")

# --- Main Loop ---

async def main():
    try:
        config = oci.config.from_file("~/.oci/config", PROFILE)
    except Exception as e:
        print(f"Error loading OCI config: {e}")
        return

    print("--- Voice AI Agent Started ---")
    print("Listening... (Press Ctrl+C to exit)")

    # Create session once and reuse
    try:
        session_id = create_agent_session(config)
    except Exception as e:
        print(f"Failed to create agent session: {e}")
        return

    while True:
        try:
            # 1. Record speech
            audio_bytes = await listen_for_speech_async()
            
            if not audio_bytes:
                continue

            # 2. Transcribe
            user_text = await send_audio_to_oci(config, audio_bytes)
            
            if not user_text:
                continue

            # 3. Query agent
            agent_response = query_agent(config, user_text, session_id)

            # 4. Speak response
            speak_text(config, agent_response)
            
            # Small pause to reduce feedback from speakers
            await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            await asyncio.sleep(2)

    print("\n--- Voice AI Agent Stopped ---")

if __name__ == "__main__":
    asyncio.run(main())
