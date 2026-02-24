import streamlit as st
import base64
import numpy as np
import oci
import cv2
import oracledb
import pandas as pd
import os
from pathlib import Path
from PIL import Image
from io import BytesIO

BASE_DIR = Path(__file__).resolve().parent
IMAGES_DIR = BASE_DIR / "images"
WALLET_DIR = BASE_DIR / "Wallet_DB"
#---------------------#
# App Setup + Styling #
#---------------------#
st.set_page_config(
    page_title="Image Vector DB Demo",
    layout="wide",
    page_icon="🧠"
)

def get_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

bg_base64 = get_base64(IMAGES_DIR / "background.png")
sidebar_bg = get_base64(IMAGES_DIR / "banner.jpg")

custom_css = f"""
<style>
.stApp {{
    background-image: url("data:image/png;base64,{bg_base64}");
    background-size: cover;
    background-repeat: no-repeat;
    background-attachment: fixed;
    color: white !important;
}}
h1, h2, h3 {{
    text-align: center !important;
}}
.main .block-container,
p, li, ul, ol {{
    color: white !important;
}}
section[data-testid="stSidebar"] {{
    background-color: #cbaf7a !important;
    color: #fff !important;
}}
.stButton>button {{
    background-color: #317efb !important;
    color: #black !important;
    border-radius: 6px !important;
}}
button {{
    color: black !important
}}
header[data-testid="stHeader"] {{
    background: #271b18 !important;
    min-height: 50px !important;
}}
header[data-testid="stHeader"]::after {{
    content: "";
    position: absolute;
    top: 20px;
    left: 35px;
    height: 85px;
    width: 100px;
    background-size: contain;
    background-repeat: no-repeat;
}}
img {{
    border-radius: 12px !important;
}}
.st-emotion-cache-1q82h82{{
    color: white !important
}}
.st-emotion-cache-p9nomz {{
    color: white !important
}}
.st-emotion-cache-1pbsqtx {{
    color: white !important
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

#-------------------------#
# DB + OCI Client Config #
#-------------------------#
conn = oracledb.connect(
    user="",
    password="",
    dsn="",
    config_dir=str(WALLET_DIR),
    wallet_location=str(WALLET_DIR),
    wallet_password=""
)
cursor = conn.cursor()

OCI_CONFIG_PATH = ""
COMPARTMENT_ID = ""
EMBED_MODEL_ID = "cohere.embed-v4.0"
OD_MODEL_ID = ""
GENAI_ENDPOINT = ""

config = oci.config.from_file(OCI_CONFIG_PATH)
genai_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
    config=config,
    service_endpoint=GENAI_ENDPOINT
)
vision_client = oci.ai_vision.AIServiceVisionClient(config)

#-----------------------------------#
# Core Logic (Embedding/DB/Vision)  #
#-----------------------------------#
def embed_image(image_bytes):
    encoded = base64.b64encode(image_bytes).decode()
    data_uri = f"data:image/jpeg;base64,{encoded}"
    detail = oci.generative_ai_inference.models.EmbedTextDetails(
        serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
            model_id=EMBED_MODEL_ID
        ),
        input_type="IMAGE",
        inputs=[data_uri],
        truncate="NONE",
        compartment_id=COMPARTMENT_ID
    )
    response = genai_client.embed_text(detail)
    vec = np.array(response.data.embeddings[0], dtype="float32")
    return vec / np.linalg.norm(vec)

def add_image_to_db(image_bytes, label):
    vec = embed_image(image_bytes)
    cursor.setinputsizes(embedding=oracledb.DB_TYPE_VECTOR)
    cursor.execute("""
        INSERT INTO image_vectors (label, embedding)
        VALUES (:label, VECTOR(:embedding, 1536))
    """, {
        "label": label,
        "embedding": vec.tolist()
    })

def search_image(image_bytes):
    vec = embed_image(image_bytes)

    cursor.setinputsizes(q=oracledb.DB_TYPE_VECTOR)

    cursor.execute("""
        SELECT label,
               vector_distance(
                   embedding,
                   :q,
                   COSINE
               ) AS dist
        FROM image_vectors
        ORDER BY dist
        FETCH FIRST 1 ROWS ONLY
    """, {
        "q": vec.tolist()
    })

    row = cursor.fetchone()
    if not row:
        return None, None

    return row[0], 1 - row[1]

def search_top_k(image_bytes, k=1):
    vec = embed_image(image_bytes)

    cursor.setinputsizes(q=oracledb.DB_TYPE_VECTOR)

    cursor.execute(f"""
        SELECT label,
               vector_distance(embedding, :q, COSINE) AS dist
        FROM image_vectors
        ORDER BY dist
        FETCH FIRST {k} ROWS ONLY
    """, {
        "q": vec.tolist()
    })

    return [(i + 1, r[0], 1 - r[1]) for i, r in enumerate(cursor.fetchall())]

def crop_from_detection(frame, obj):
    h, w, _ = frame.shape
    poly = obj.bounding_polygon.normalized_vertices
    x1 = max(0, int(poly[0].x * w))
    y1 = max(0, int(poly[0].y * h))
    x2 = min(w, int(poly[2].x * w))
    y2 = min(h, int(poly[2].y * h))
    if x2 <= x1 or y2 <= y1:
        return None
    return frame[y1:y2, x1:x2]

#---------------------#
# UI Pages / Routing  #
#---------------------#
st.sidebar.title("Navigation")
view = st.sidebar.radio(
    "Choose view",
    ["➕ Add Images", "🔍 Search Image", "🗂️ Database Overview", "🔎 Object Detection + Search"]
)

if view == "➕ Add Images":
    st.title("➕ Add Images to Oracle Vector DB")
    label = st.text_input("Label")
    uploads = st.file_uploader(
        "Upload images",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    if st.button("Embed & Store"):
        with st.spinner("Embedding images..."):
            for img in uploads:
                add_image_to_db(img.read(), label)
        conn.commit()

elif view == "🔍 Search Image":
    st.title("🔍 Search by Image")
    query = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if query:
        st.image(query, use_container_width=True)
        with st.spinner("Searching..."):
            label, score = search_image(query.read())
        if label:
            st.success(f"Prediction: {label}")
            st.caption(f"Similarity: {score:.3f}")
        else:
            st.warning("No match found")

elif view == "🗂️ Database Overview":
    st.title("🗂️ Database Overview")
    cursor.execute("SELECT COUNT(*) FROM image_vectors")
    total = cursor.fetchone()[0]
    st.metric("Total vectors", total)
    st.metric("Vector dimension", 1536)
    cursor.execute("""
        SELECT label, COUNT(*)
        FROM image_vectors
        GROUP BY label
        ORDER BY COUNT(*) DESC
    """)
    rows = cursor.fetchall()
    if rows:
        df = pd.DataFrame(rows, columns=["Label", "Images"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No data yet")

elif view == "🔎 Object Detection + Search":
    st.title("🔎 OCI Object Detection + Vector Search")
    uploaded = st.file_uploader("Upload image", type=["jpg", "jpeg", "png"])
    if uploaded:
        image_bytes = uploaded.read()
        pil = Image.open(BytesIO(image_bytes)).convert("RGB")
        frame = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        st.image(pil, use_container_width=True)

        with st.spinner("Running object detection..."):
            response = vision_client.analyze_image(
                analyze_image_details=oci.ai_vision.models.AnalyzeImageDetails(
                    features=[oci.ai_vision.models.ImageObjectDetectionFeature(
                        feature_type="OBJECT_DETECTION",
                        max_results=20,
                        model_id=OD_MODEL_ID
                    )],
                    image=oci.ai_vision.models.InlineImageDetails(
                        source="INLINE",
                        data=base64.b64encode(image_bytes).decode()
                    ),
                    compartment_id=COMPARTMENT_ID
                )
            )

        detections = response.data.image_objects or []
        cols = st.columns(3)
        i = 0
        for obj in detections:
            if obj.confidence < 0.4:
                continue
            crop = crop_from_detection(frame, obj)
            if crop is None:
                continue
            _, buf = cv2.imencode(".jpg", crop)
            results = search_top_k(buf.tobytes(), 1)
            with cols[i % 3]:
                st.image(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
                st.markdown(f"**OD Class:** `{obj.name}`")
                st.markdown(f"**Confidence:** `{obj.confidence:.2f}`")
                if results:
                    st.markdown(f"**DB Match:** `{results[0][1]}` ({results[0][2]:.3f})")
                else:
                    st.markdown("_No match_")
            i += 1