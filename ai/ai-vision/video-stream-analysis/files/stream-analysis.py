import time
import base64
import json
import oci
import streamlit as st
from PIL import Image
from io import BytesIO
import numpy as np
import cv2
from datetime import datetime, timezone, timedelta
import logging, warnings
import pandas as pd
import altair as alt
from enum import Enum

#------------------ Constants -----------------
OBJECT_LIMIT = 500
OCCUPANCY_WINDOW_SEC = 20
FRAME_WIDTH = 700
FRAME_HEIGHT = 350

# ----------------- Enum -----------------
class DetectionMode(Enum):
    OBJECT = "Object Detection"
    FACE = "Face Detection"

# ----------------- Setup -----------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

st.set_page_config(page_title="OCI Vision Streaming", layout="wide", initial_sidebar_state="expanded")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ----------------- Session Defaults -----------------
defaults = {
    "stream_job_ocid": "",
    "bucket": "",
    "prefix": "",
    "os_namespace": "",
    "streaming": False,
    "occupancy_count": 0,
    "peak_occupancy": {"timestamp": "", "count": 0},
    "face_detection_timestamps": [],
    "occupancy_history": [],
    "object_counts": {},
    "mode": DetectionMode.OBJECT.value,  # default
    "start_stop_label": "▶️ Start Consumption"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# OCI Config
oci_config = oci.config.from_file("~/.oci/config", profile_name="DEFAULT")
service_endpoint = f"https://vision.aiservice.{oci_config.get('region')}.oci.oraclecloud.com"

# ----------------- Helpers -----------------
def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

#--------------------------------------------------------------------------------------#
def get_current_time():
    return datetime.now(timezone.utc)

#--------------------------------------------------------------------------------------#
def decode_image(image_data):
    image_bytes = base64.b64decode(image_data)
    image = Image.open(BytesIO(image_bytes))
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    return np.array(image)

#--------------------------------------------------------------------------------------#

def draw_objects_with_boxes(image, objects):
    h, w, _ = image.shape
    for obj in objects:
        pts = [(int(v['x'] * w), int(v['y'] * h)) for v in obj['boundingPolygon']['normalizedVertices']]
        x_coords = [pt[0] for pt in pts]
        y_coords = [pt[1] for pt in pts]
        x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{obj['name']} ({obj['confidence']:.2f})"
        cv2.putText(image, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2, cv2.LINE_AA)
    return image

#--------------------------------------------------------------------------------------#

def blur_faces(image, faces):
    h, w, _ = image.shape
    for face in faces:
        pts = [(int(v['x'] * w), int(v['y'] * h)) for v in face['boundingPolygon']['normalizedVertices']]
        x_coords = [pt[0] for pt in pts]
        y_coords = [pt[1] for pt in pts]
        x1, y1, x2, y2 = min(x_coords), min(y_coords), max(x_coords), max(y_coords)
        face_region = image[y1:y2, x1:x2]
        if face_region.size > 0:
            blurred = cv2.GaussianBlur(face_region, (51, 51), 30)
            image[y1:y2, x1:x2] = blurred
    return image

#--------------------------------------------------------------------------------------#

def process_frame(message, mode):
    data = json.loads(message.replace("'", '"'))
    image = decode_image(data['imageData'])
    if mode == DetectionMode.OBJECT.value:
        objects = data.get("detectedObjects", [])
        if objects:
            image = draw_objects_with_boxes(image, objects)
        return image, objects
    elif mode == DetectionMode.FACE.value:
        faces = data.get("detectedFaces", [])
        if faces:
            image = blur_faces(image, faces)
        return image, faces

#--------------------------------------------------------------------------------------#

def update_analytics(faces):
    current_time = get_current_time()
    occupancy = len(faces)
    st.session_state.occupancy_history.append((current_time, occupancy))
    cutoff = current_time - timedelta(seconds=OCCUPANCY_WINDOW_SEC)
    st.session_state.occupancy_history = [
        (t, o) for t, o in st.session_state.occupancy_history if t >= cutoff
    ]
    st.session_state.occupancy_count = occupancy

#--------------------------------------------------------------------------------------#

def update_object_counts(objects):
    """Accumulate detected object counts with up to last 5 timestamps each."""
    current_time = get_current_time()
    # Initialize dict if not exists
    if "object_counts" not in st.session_state:
        st.session_state.object_counts = {}

    for obj in objects:
        name = obj["name"]
        if name not in st.session_state.object_counts:
            st.session_state.object_counts[name] = {"timestamps": []}
        st.session_state.object_counts[name]["timestamps"].append(current_time)

        # Keep only last 5 timestamps
        st.session_state.object_counts[name]["timestamps"] = st.session_state.object_counts[name]["timestamps"][-5:]


#--------------------------------------------------------------------------------------#

def consume_stream(namespace, bucket, prefix, client, frame_placeholder, chart_placeholder, mode, delay=0):
    try:
        objs = client.list_objects(namespace, bucket, prefix=prefix, limit=OBJECT_LIMIT).data.objects
        if not objs:
            frame_placeholder.markdown('<div class="video-box"><p>⚠️ No frames found.</p></div>', unsafe_allow_html=True)
            return

        chart_ph = chart_placeholder.empty()
        objs = sorted(objs, key=lambda o: o.name)

        for obj in objs:
            content = client.get_object(namespace, bucket, obj.name).data.content.decode("utf-8")
            frame, detections = process_frame(content, mode)

            if mode == DetectionMode.OBJECT.value:
                update_object_counts(detections)
            elif mode == DetectionMode.FACE.value:
                update_analytics(detections)

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            _, buffer = cv2.imencode(".jpg", rgb_frame)
            frame_base64 = base64.b64encode(buffer).decode()

            frame_placeholder.markdown(
                f'<div class="video-box"><img src="data:image/jpeg;base64,{frame_base64}" '
                'style="width:100%; height:100%; object-fit:contain;" /></div>',
                unsafe_allow_html=True
            )

            # Different detections require different Analytics 
            if mode == DetectionMode.OBJECT.value and st.session_state.object_counts:
                data = []
                for obj_name, info in st.session_state.object_counts.items():
                    timestamps_str = ", ".join([t.strftime("%H:%M:%S") for t in info["timestamps"]])
                    data.append([obj_name, timestamps_str])
                df_counts = pd.DataFrame(data, columns=["Object Detected", "Timestamps"])
                chart_ph.dataframe(df_counts, use_container_width=True)

            elif mode == DetectionMode.FACE.value and st.session_state.occupancy_history:
                df_occupancy = pd.DataFrame(st.session_state.occupancy_history, columns=["Time", "Count"])
                df_occupancy["Time"] = pd.to_datetime(df_occupancy["Time"])
                peak_row = df_occupancy.loc[df_occupancy["Count"].idxmax()]
                peak_time = peak_row["Time"]
                peak_count = peak_row["Count"]

                col1, col2 = chart_ph.columns([2, 1])
                with col1:
                    chart = alt.Chart(df_occupancy).mark_line().encode(
                        x="Time:T",
                        y=alt.Y("Count:Q", scale=alt.Scale(domain=[0, 10]))
                    ).properties(width=FRAME_WIDTH, height=FRAME_HEIGHT, title="Occupancy Over Time")
                    col1.altair_chart(chart, use_container_width=False)
                with col2:
                    col2.markdown("### Peak Occupancy")
                    col2.markdown(f"**Count:** {peak_count}")
                    col2.markdown(f"**Time:** {peak_time.strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(delay)

    except Exception as e:
        st.error(f"Error reading stored frames: {e}")



#--------------------------------------------------------------------------------------#
#-----------------------------------PAGE SETUP-----------------------------------------#
#--------------------------------------------------------------------------------------#



logo_base64 = get_base64_image('../media/oracle_logo.png')
st.markdown(
    f"""
    <div class="banner">
        <img src="data:image/png;base64,{logo_base64}" alt="logo">
        <h1>OCI Vision Streaming</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<br><br><br>", unsafe_allow_html=True)

col1, col2 = st.columns([1, 3])

with col1:
    st.session_state.mode = st.radio(
        "Detection Mode",
        [DetectionMode.OBJECT.value, DetectionMode.FACE.value],
        index=0
    )

    st.session_state.stream_job_ocid = st.text_input("Stream Job OCID", value=st.session_state.stream_job_ocid)
    st.session_state.bucket = st.text_input("Bucket Name")
    st.session_state.prefix = st.text_input("Prefix")
    st.session_state.os_namespace = st.text_input("Object Storage Namespace")

with col2:
    frame_placeholder = st.empty()
    frame_placeholder.markdown('<div class="video-box"><p>🎥 Waiting for stream...</p></div>', unsafe_allow_html=True)

def toggle_streaming():
    st.session_state.streaming = not st.session_state.streaming
    st.session_state.start_stop_label = "⏹️ Stop Consumption" if st.session_state.streaming else "▶️ Start Consumption"

st.button(st.session_state.start_stop_label, on_click=toggle_streaming)

st.markdown("---")
chart_placeholder = st.empty()

try:
    token_file = oci_config["security_token_file"]
    with open(token_file, "r") as f:
        token = f.read()

    private_key = oci.signer.load_private_key_from_file(oci_config["key_file"])
    config = oci.config.from_file()
    signer = oci.auth.signers.SecurityTokenSigner(token, private_key)
    vision_client = oci.ai_vision.AIServiceVisionClient(config=config, signer=signer, service_endpoint=service_endpoint)

    if st.session_state.streaming:
        if not all([st.session_state.stream_job_ocid, st.session_state.bucket, st.session_state.prefix, st.session_state.os_namespace]):
            st.error("Please provide all required Stream Job and Object Storage details")
        else:
            storage_client = oci.object_storage.ObjectStorageClient(config, signer=signer)
            consume_stream(
                st.session_state.os_namespace,
                st.session_state.bucket,
                st.session_state.prefix,
                storage_client,
                frame_placeholder,
                chart_placeholder,
                st.session_state.mode
            )
    else:
        frame_placeholder.markdown('<div class="video-box"><p>⏹️ Stream stopped</p></div>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Operation failed: {e}")

