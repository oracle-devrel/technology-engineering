"""
Simple streamlit UI for comparison of vision models

Converts PDF to image -> Extracts all data into a JSON

Available models:
    - Llama 4 Scout
    - Llama 4 Maverick

Author - Ali Ottoman
"""

import io
import base64
import oci
from pdf2image import convert_from_bytes
import streamlit as st
from oci_models import get_llm
from prompt import OVERALL_PROMPT
from config import compartment_id, vision_models


# ─── LLM Creation ─────────────────────────────────────────────────────────────
llm_client = get_llm()

# ─── Helper Functions ─────────────────────────────────────────────────────────────
def save_images(images, output_format="JPEG"):
    """
        Saves images locally for processing
    """
    image_list = []
    for image in images:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)
        image_list.append(img_byte_arr)
    return image_list

def encode_image(image_path):
    """
        Encodes an image to base64 format.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def make_user_message(prompt: str, b64img: str):
    """
        Builds UserMessage with text + image
    """
    # Text part
    txt = oci.generative_ai_inference.models.TextContent()
    txt.text = prompt

    # Image part
    img = oci.generative_ai_inference.models.ImageContent()
    url = oci.generative_ai_inference.models.ImageUrl()
    url.url = f"data:image/jpeg;base64,{b64img}"
    img.image_url = url

    msg = oci.generative_ai_inference.models.UserMessage()
    msg.content = [txt, img]
    return msg

def call_vision_model(frame, prompt: str, vision_model: str):
    """
        Assemble and send the chat request
    """
    user_msg = make_user_message(prompt, frame)

    # GenericChatRequest
    chat_req = oci.generative_ai_inference.models.GenericChatRequest(
        messages     = [user_msg],
        api_format   = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
        num_generations   = 1,
        is_stream         = False,
        temperature       = 0.5,
        top_p             = 0.7,
        top_k             = -1,
        frequency_penalty = 1.0
    )

    details = oci.generative_ai_inference.models.ChatDetails(
        serving_mode   = oci.generative_ai_inference.models.OnDemandServingMode(model_id=vision_model),
        compartment_id = compartment_id,
        chat_request   = chat_req
    )

    # Invoke the model
    resp = llm_client.chat(details)
    return resp.data.chat_response.choices[0].message.content[0].text

# ─── Main Function ─────────────────────────────────────────────────────────────
def main():
    """
        Streamlit UI and model selection + Running & outputting the JSON
    """
    st.title("Model Comparison")

    uploaded_image = st.file_uploader("Upload image here")

    prompt = OVERALL_PROMPT

    with st.sidebar:
        st.subheader("Select your model for comparison")
        vision_model = st.selectbox("Choose your model:", vision_models)
    if uploaded_image is not None:
        with st.spinner("Processing..."):
            if uploaded_image.type == "application/pdf":
                images = convert_from_bytes(uploaded_image.read(), fmt="jpeg")
            else:
                images = [convert_from_bytes(uploaded_image.read(), fmt="jpeg")[0]]

            image_list = save_images(images)

        encoded_frame = base64.b64encode(image_list[0].getvalue()).decode("utf-8")

        result = call_vision_model(encoded_frame, prompt, vision_model)
        st.write(result)

# ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
