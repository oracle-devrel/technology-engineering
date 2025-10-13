"""
Document Understanding with LLMs — Images *or* Video (single final analysis)

Features
- Upload multiple images OR a single video
- Images: pass 1..N photos to Llama 4 Maverick in one go (original behaviour)
- Video: extract frames at a chosen interval and run **one final analysis** across all extracted frames (no per‑batch output)
- Insurance-only prompt (concise adjuster-style report)
- Shows thumbnails and the final analysis

Run:
  pip install -r requirements.txt
  streamlit run doc_llm_with_video.py

Author: Ali Ottoman
"""

import io
import os
import cv2
import json
import base64
import tempfile
from datetime import timedelta
from typing import List, Tuple

import pandas as pd
import streamlit as st
from PIL import Image
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
import oci
from pdf2image import convert_from_bytes

from config import COMPARTMENT_ID, MODEL_ID  # keep your existing config

# ========== OCI config ==========
config = oci.config.from_file(profile_name="DEFAULT")

# ========== Constants ==========
MAX_TOKENS = 2000
MAX_VIDEO_FRAMES = 120

# ========== Helpers ==========

def to_rgb(image: Image.Image) -> Image.Image:
    """Ensure image is RGB before saving as JPEG."""
    if image.mode in ("RGBA", "P"):
        return image.convert("RGB")
    return image


def save_images(images: List[Image.Image], output_format: str = "JPEG") -> List[io.BytesIO]:
    """Convert PIL Image objects to in-memory byte streams for downstream processing."""
    image_list: List[io.BytesIO] = []
    for image in images:
        img = to_rgb(image)
        buf = io.BytesIO()
        img.save(buf, format=output_format)
        buf.seek(0)
        image_list.append(buf)
    return image_list


def encode_image_bytes(image_bytes: io.BytesIO) -> str:
    """Return Base64-encoded str for an in-memory image (BytesIO)."""
    return base64.b64encode(image_bytes.getvalue()).decode("utf-8")


def encode_np_frame_to_bytes(frame) -> io.BytesIO:
    """Encode an OpenCV (numpy) frame to JPEG BytesIO."""
    success, encoded = cv2.imencode(".jpg", frame)
    if not success:
        raise RuntimeError("Failed to encode frame to JPEG")
    buf = io.BytesIO(encoded.tobytes())
    buf.seek(0)
    return buf


def extract_frames(video_path: str, interval: int, cap_frames: int = MAX_VIDEO_FRAMES) -> List[Tuple[io.BytesIO, str]]:
    """
    Extract frames from a video at a specified interval (every N frames).
    Returns list of (BytesIO JPEG, timecode) tuples, capped to `cap_frames`.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Unable to open video file")

    frames: List[Tuple[io.BytesIO, str]] = []
    frame_rate = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_rate = int(frame_rate)
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if idx % interval == 0:
            buf = encode_np_frame_to_bytes(frame)
            timecode = str(timedelta(seconds=idx // max(1, frame_rate)))
            frames.append((buf, timecode))
            if len(frames) >= cap_frames:
                break
        idx += 1

    cap.release()
    return frames

# ========== LLM Calls ==========

def build_llm(temperature: float = 0.0) -> ChatOCIGenAI:
    return ChatOCIGenAI(
        model_id=MODEL_ID[0],
        compartment_id=COMPARTMENT_ID,
        model_kwargs={"max_tokens": MAX_TOKENS, "temperature": temperature},
    )


def llm_multimodal_call(images_b64: List[str], user_text: str, system_prompt: str, llm: ChatOCIGenAI):
    content = [{"type": "text", "text": user_text}]
    for b64 in images_b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

    human_message = HumanMessage(content=content)
    system_message = SystemMessage(content=system_prompt)
    resp = llm.invoke(input=[human_message, system_message])
    return resp.content


# ======= Insurance System Prompt =======
INSURANCE_PROMPT = (
    """
    Produce a concise but comprehensive written assessment for an insurance adjuster, considering ALL provided images.

    Structure:
    ### Vehicle Details
    Make/model/year (if visible), color, plate, notable trim/badges (say "not visible" when unclear).

    ### Damage Assessment
    Front, Left Side, Rear, Right Side, Roof/Glass, Wheels/Tires: list damages with brief severity (minor/moderate/severe). Deduplicate repeated sightings across frames.

    ### Safety & Driveability
    Airbags/seatbelts, lights, glass integrity, structural concerns, leaks; is it driveable?

    ### ADAS & Calibration
    Sensors/cameras potentially requiring recalibration (e.g., radar in bumper, windshield camera).

    ### Prior Damage Indicators
    Mismatched paint, rust, old dents, non-OEM gaps.

    ### Summary
    2–4 sentences summarizing overall condition and key concerns. No costs or liability.
    """
).strip()

# ========== UI ==========

def app():
    st.title("🚗 Insurance Image/Video Analyzer — OCI GenAI (Maverick)")

    with st.sidebar:
        st.header("Parameters")
        temperature = st.slider("Temperature", 0.0, 1.0, 0.0, 0.1)
        interval = st.slider("Video frame interval (every N frames)", 1, 60, 12)
        max_frames = st.slider("Max frames to analyze (cap)", 10, 200, MAX_VIDEO_FRAMES, 10)
        st.caption("Video path extracts frames by interval, caps count, then performs a single final analysis across all frames.")

    uploaded_files = st.file_uploader(
        "Upload images (jpg/png) OR a single video (mp4/avi/mov) OR a PDF",
        type=["pdf", "jpg", "jpeg", "png", "mp4", "avi", "mov"],
        accept_multiple_files=True,
    )

    user_request = st.chat_input("Enter your request (e.g., 'Describe vehicle damages')")

    if not uploaded_files or not user_request:
        st.info("Upload files and enter a request to begin.")
        return

    # Detect if user provided a video
    video_files = [f for f in uploaded_files if f.type and f.type.startswith("video")]
    image_files = [f for f in uploaded_files if f.type in ("image/jpeg", "image/png", "image/jpg")]
    pdf_files = [f for f in uploaded_files if f.type == "application/pdf"]

    # Safety: do not allow mixing video with other types in a single run
    if video_files and (image_files or pdf_files):
        st.warning("Please upload either a video OR images/PDF in one run, not both.")
        return

    llm = build_llm(temperature=temperature)

    # ========== IMAGE / PDF PATH ==========
    if not video_files:
        # Expand PDFs to images, and concat with directly uploaded images
        images: List[Image.Image] = []
        for f in pdf_files:
            images.extend(convert_from_bytes(f.read(), fmt="jpeg"))
        for f in image_files:
            images.append(Image.open(f))

        if not images:
            st.error("No images found to process.")
            return

        # Show a grid of images
        st.subheader("Uploaded Images")
        cols = st.columns(3)
        for idx, img in enumerate(images, start=1):
            with cols[(idx - 1) % 3]:
                st.image(img, caption=f"Image {idx}", use_container_width=True)

        # Prepare bytes and b64
        image_list = save_images(images)
        images_b64 = [encode_image_bytes(b) for b in image_list]

        system_prompt = INSURANCE_PROMPT

        st.chat_message("user").write(user_request)
        with st.spinner("Extracting (Multimodal LLM)..."):
            result_text = llm_multimodal_call(images_b64, user_request, system_prompt, llm)
        st.chat_message("assistant").write(result_text)
        return

    # ========== VIDEO PATH ==========
    if len(video_files) != 1:
        st.error("Please upload exactly one video file for video analysis.")
        return

    # Save uploaded video to a temp file
    tmpdir = tempfile.mkdtemp()
    video_path = os.path.join(tmpdir, video_files[0].name)
    with open(video_path, "wb") as vf:
        vf.write(video_files[0].read())

    # Extract frames (BytesIO + timecode)
    with st.spinner("Extracting frames from video..."):
        frames = extract_frames(video_path, interval, cap_frames=max_frames)
    st.success(f"Extracted {len(frames)} frames (capped at {max_frames}).")

    if not frames:
        st.error("No frames extracted from the video.")
        return

    # Show thumbnails (up to first 30 to avoid UI overload)
    st.subheader("Sample Frames")
    cols = st.columns(5)
    for i, (buf, tc) in enumerate(frames[:30]):
        img = Image.open(buf)
        with cols[i % 5]:
            st.image(img, caption=f"{tc}", use_container_width=True)

    # One final analysis across ALL extracted frames
    system_prompt = INSURANCE_PROMPT
    images_b64 = [encode_image_bytes(buf) for (buf, _tc) in frames]

    st.chat_message("user").write(user_request)
    with st.spinner("Analyzing all frames together (single final report)..."):
        try:
            resp_text = llm_multimodal_call(images_b64, user_request, system_prompt, llm)
        except Exception as e:
            resp_text = f"ERROR: {e}"

    st.markdown("**Final Video Analysis:**")
    st.write(resp_text)


if __name__ == "__main__":
    app()
