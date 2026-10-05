"""Client for text-to-speech models served on OCI Generative AI's
OpenAI-compatible speech route.

    POST https://inference.generativeai.<region>.oci.oraclecloud.com/openai/v1/audio/speech

Works for imported models on a dedicated AI cluster (for example k2-fsa/OmniVoice,
where `model` is the endpoint OCID) and for on-demand models that answer on the
same route. Requests are built with httpx rather than the OpenAI SDK because the
SDK forces a `voice` argument that voice-cloning models such as OmniVoice reject.

Facts verified live against an OmniVoice endpoint (Sep/Oct 2026):
  - the path is /openai/v1/audio/speech, with no /20231130 prefix
  - `model` is the endpoint OCID, not the display name
  - the compartment header is required with OCI request signing
  - `stream: true` returns a chunked byte stream; `stream_format: "sse"` does not work
  - wav/pcm output is 24 kHz mono 16-bit; audio seconds = bytes / 48000
"""
from __future__ import annotations

import base64
import io
import mimetypes
import os
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import httpx

AUDIO_FORMATS = ("wav", "mp3", "flac", "opus", "pcm")
AUTH_MODES = ("api_key", "resource_principal", "instance_principal", "security_token", "bearer")
SAMPLE_RATE = 24_000          # pcm/wav output: 24 kHz mono s16le
BYTES_PER_SECOND = 2 * SAMPLE_RATE

_OCID_REGION = re.compile(r"^ocid1\.generativeaiendpoint\.oc1\.([a-z0-9-]+)\.")
_SENTENCE_END = re.compile(r"(?<=[.!?؟])(?<![A-Z][.!?])\s+")      # not after an initial such as "C."
_CLAUSE_END = re.compile(r"(?<=[,;:،؛])\s+")


class TTSError(RuntimeError):
    def __init__(self, status: int, request_id: str | None, body: str):
        super().__init__(f"TTS request failed: HTTP {status} opc-request-id={request_id}\n{body[:800]}")
        self.status, self.request_id, self.body = status, request_id, body


@dataclass
class SpeechResult:
    audio: bytes
    content_type: str
    request_id: str | None     # opc-request-id, what Oracle Support asks for

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.audio)
        return path


class StreamingSpeech:
    """Context manager around a `stream: true` response. Iterate `.chunks()`."""

    def __init__(self, cm):
        self._cm = cm
        self.request_id: str | None = None
        self.content_type = ""

    def __enter__(self) -> "StreamingSpeech":
        self._resp = self._cm.__enter__()
        self.request_id = self._resp.headers.get("opc-request-id")
        self.content_type = self._resp.headers.get("content-type", "")
        if self._resp.status_code != 200:
            self._resp.read()
            raise TTSError(self._resp.status_code, self.request_id, self._resp.text)
        return self

    def chunks(self) -> Iterator[bytes]:
        return self._resp.iter_bytes()

    def __exit__(self, *exc):
        return self._cm.__exit__(*exc)


def resolve_auth_mode(explicit: str | None = None) -> str:
    """Pick the auth mode: explicit > OCI_AUTH env > bearer key present >
    resource principal environment (Data Science notebooks, jobs) > api_key."""
    mode = (explicit or os.getenv("OCI_AUTH") or "").lower().strip()
    if mode:
        if mode not in AUTH_MODES:
            raise ValueError(f"OCI_AUTH must be one of {AUTH_MODES}, got {mode!r}")
        return mode
    if os.getenv("GENAI_API_KEY"):
        return "bearer"
    if os.getenv("OCI_RESOURCE_PRINCIPAL_VERSION"):
        return "resource_principal"
    return "api_key"


def build_auth(mode: str, profile: str) -> httpx.Auth | None:
    """OCI request signer for httpx, or None for bearer-key auth."""
    if mode == "bearer":
        return None
    from oci_openai import (
        OciInstancePrincipalAuth, OciResourcePrincipalAuth, OciSessionAuth, OciUserPrincipalAuth,
    )
    if mode == "resource_principal":
        return OciResourcePrincipalAuth()
    if mode == "instance_principal":
        return OciInstancePrincipalAuth()
    if mode == "security_token":
        return OciSessionAuth(profile_name=profile)
    return OciUserPrincipalAuth(profile_name=profile)


def _region(model: str, mode: str, profile: str) -> str:
    m = _OCID_REGION.match(model)
    if m:
        return m.group(1)
    if os.getenv("OCI_REGION"):
        return os.environ["OCI_REGION"]
    if mode in ("api_key", "security_token"):
        import oci
        return oci.config.from_file(profile_name=profile)["region"]
    raise ValueError("Cannot derive the region: set OCI_REGION or GENAI_SERVICE_ENDPOINT")


def data_uri(audio: bytes | str | Path, mime: str | None = None) -> str:
    """Inline a reference clip as a base64 data URL, the form the server accepts."""
    if isinstance(audio, (str, Path)):
        path = Path(audio)
        mime = mime or mimetypes.guess_type(path.name)[0] or "audio/wav"
        audio = path.read_bytes()
    return f"data:{mime or 'audio/wav'};base64," + base64.b64encode(audio).decode("ascii")


class TTSClient:
    """Thread-safe: one instance can be shared by a ThreadPoolExecutor."""

    def __init__(
        self,
        *,
        model: str | None = None,
        compartment_id: str | None = None,
        auth_mode: str | None = None,
        profile: str | None = None,
        service_endpoint: str | None = None,
        api_key: str | None = None,
        timeout: float = 300.0,
    ):
        self.model = model or os.environ["TTS_MODEL"]
        self.compartment_id = compartment_id or os.environ["GENAI_COMPARTMENT_ID"]
        self.auth_mode = resolve_auth_mode(auth_mode)
        profile = profile or os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        host = service_endpoint or os.getenv("GENAI_SERVICE_ENDPOINT") or (
            f"https://inference.generativeai.{_region(self.model, self.auth_mode, profile)}.oci.oraclecloud.com"
        )
        self.url = host.rstrip("/") + "/openai/v1/audio/speech"
        headers = {"CompartmentId": self.compartment_id, "opc-compartment-id": self.compartment_id}
        if self.auth_mode == "bearer":
            key = api_key or os.getenv("GENAI_API_KEY")
            if not key:
                raise ValueError("OCI_AUTH=bearer needs GENAI_API_KEY")
            headers["Authorization"] = f"Bearer {key}"
        self._http = httpx.Client(auth=build_auth(self.auth_mode, profile), headers=headers, timeout=timeout)

    # -- request body ---------------------------------------------------------
    def body(
        self,
        text: str,
        *,
        response_format: str = "wav",
        language: str | None = None,
        voice: str | None = None,
        instructions: str | None = None,
        ref_audio: bytes | str | Path | None = None,
        ref_text: str | None = None,
        speed: float | None = None,
        stream: bool = False,
    ) -> dict:
        if response_format not in AUDIO_FORMATS:
            raise ValueError(f"response_format must be one of {AUDIO_FORMATS}")
        body: dict = {"model": self.model, "input": text, "response_format": response_format}
        if language:
            body["language"] = language
        if voice:                       # preset-voice models only; OmniVoice rejects it
            body["voice"] = voice
        if instructions:                # voice design
            body["instructions"] = instructions
        if ref_audio is not None:       # voice cloning
            body["ref_audio"] = ref_audio if isinstance(ref_audio, str) and ref_audio.startswith("data:") else data_uri(ref_audio)
            if ref_text:
                body["ref_text"] = ref_text
        if speed is not None:
            body["speed"] = speed
        if stream:
            body["stream"] = True
        return body

    # -- calls ----------------------------------------------------------------
    def speak(self, text: str, **kwargs) -> SpeechResult:
        """One request, whole audio back in the response body."""
        r = self._http.post(self.url, json=self.body(text, **kwargs))
        request_id = r.headers.get("opc-request-id")
        if r.status_code != 200:
            raise TTSError(r.status_code, request_id, r.text)
        return SpeechResult(r.content, r.headers.get("content-type", ""), request_id)

    def speak_stream(self, text: str, *, response_format: str = "pcm", **kwargs) -> StreamingSpeech:
        """`stream: true`. Use pcm so partial chunks are playable:

            with client.speak_stream("Hello") as s:
                for chunk in s.chunks(): ...
        """
        body = self.body(text, response_format=response_format, stream=True, **kwargs)
        return StreamingSpeech(self._http.stream("POST", self.url, json=body))

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# --- text and audio helpers --------------------------------------------------

def split_text(text: str, max_chars: int) -> list[str]:
    """Pack sentences into chunks of at most `max_chars`. A sentence longer than
    that on its own is cut at clause punctuation. Handles Latin and Arabic marks."""
    pieces: list[str] = []
    for sentence in _SENTENCE_END.split(" ".join(text.split())):
        pieces += _CLAUSE_END.split(sentence) if len(sentence) > max_chars else [sentence]
    chunks: list[str] = []
    for piece in pieces:
        if chunks and len(chunks[-1]) + 1 + len(piece) <= max_chars:
            chunks[-1] += " " + piece
        else:
            chunks.append(piece)
    return chunks


def cut_at_sentence(text: str, length: int) -> str:
    """The text up to the sentence end nearest `length` characters."""
    text = " ".join(text.split())
    ends = [m.end() for m in re.finditer(r"[.!?؟](?=\s|$)", text)] or [len(text)]
    return text[: min(ends, key=lambda e: abs(e - length))].strip()


def pcm_seconds(audio: bytes) -> float:
    return len(audio) / BYTES_PER_SECOND


def pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(pcm)
    return buf.getvalue()
