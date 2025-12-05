# Voice AI Agent (OCI Realtime Speech + Generative AI Agent)

**Author:** msliwins  
**Last review date:** 2025-12-05  

A small voice assistant that:

1. Listens to your microphone with VAD (voice activity detection),
2. Streams audio to **OCI Realtime Speech** for STT,
3. Sends the recognized text to an **OCI Generative AI Agent Endpoint**,
4. Uses **OCI Text-to-Speech** to speak the answer back.

Everything runs in a loop until you stop it with `Ctrl+C`.

---

## Features

- 🎙️ Voice Activity Detection (VAD)  
  Automatically starts recording when you speak and stops after a short silence.

- 🧠 Generative AI Agent integration  
  Uses an OCI Generative AI Agent Endpoint to handle conversation and tools.

- 🗣️ Text-to-Speech  
  Uses OCI AI Speech to synthesize responses and plays them locally.

- 🔁 Persistent agent session  
  Single agent session reused across turns for conversational context.

- 🧪 Debug traces  
  Optionally saves agent traces to `traces.json` for debugging.

---

## Project Structure (key files)

- `main.py` – the script you shared; runs the whole loop.
- `requirements.txt` – Python dependencies.
- `.env` – **local**, not committed, real values.
- `example.env` – safe template with placeholder values for others.

---

## Requirements

- Python 3.11+ (recommended)
- Valid OCI tenancy and user with:
  - Permission to use **AI Speech** (STT + TTS),
  - Permission to use **Generative AI Agent Runtime**.
- Configured `~/.oci/config` with a profile matching your env (`OCI_PROFILE`).
- A working microphone on your machine (Windows, since it uses `winsound`).