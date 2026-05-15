# Author: Ansh
import streamlit as st
import oci
import base64
import cv2
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# OCI Configuration
compartmentId = "ocid1.compartment.oc1..XXXXXXXXXXXXXxxxxxxxxxxxxxxxxxxxxxxxxxxx"
llm_service_endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
CONFIG_PROFILE = "DEFAULT"
visionModel = "meta.llama-3.2-90b-vision-instruct"
summarizeModel = "cohere.command-r-plus-08-2024"
config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
llm_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                        config=config,
                        service_endpoint=llm_service_endpoint,
                        retry_strategy=oci.retry.NoneRetryStrategy(),
                        timeout=(10, 240)
                    )

# Functions for Image Analysis
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Functions for Video Analysis
def encode_cv2_image(frame):
    _, buffer = cv2.imencode('.jpg', frame)
    return base64.b64encode(buffer).decode("utf-8")

# Common Functions
def get_message(encoded_image=None, user_prompt=None):
    content1 = oci.generative_ai_inference.models.TextContent()
    content1.text = user_prompt
    
    message = oci.generative_ai_inference.models.UserMessage()
    message.content = [content1]
    
    if encoded_image:
        content2 = oci.generative_ai_inference.models.ImageContent()
        image_url = oci.generative_ai_inference.models.ImageUrl()
        image_url.url = f"data:image/jpeg;base64,{encoded_image}"
        content2.image_url = image_url
        message.content.append(content2)
    return message

def get_chat_request(encoded_image=None, user_prompt=None):
    chat_request = oci.generative_ai_inference.models.GenericChatRequest()
    chat_request.messages = [get_message(encoded_image, user_prompt)]
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
    chat_request.num_generations = 1
    chat_request.is_stream = False
    chat_request.max_tokens = 500
    chat_request.temperature = 0.75
    chat_request.top_p = 0.7
    chat_request.top_k = -1
    chat_request.frequency_penalty = 1.0
    return chat_request

def cohere_chat_request(encoded_image=None, user_prompt=None):
    print(" i am here")
    chat_request = oci.generative_ai_inference.models.CohereChatRequest()
    chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_COHERE
    message = get_message(encoded_image, user_prompt)
    chat_request.message = message.content[0].text
    chat_request.is_stream = False
    chat_request.preamble_override = "Make sure you answer only in "+ lang_type
    chat_request.max_tokens = 500
    chat_request.temperature = 0.75
    chat_request.top_p = 0.7
    chat_request.top_k = 0
    chat_request.frequency_penalty = 1.0
    return chat_request


def get_chat_detail(chat_request,model):
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id=model)
    chat_detail.compartment_id = compartmentId
    chat_detail.chat_request = chat_request
    return chat_detail

def extract_frames(video_path, interval=1):
    frames = []
    cap = cv2.VideoCapture(video_path)
    frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
    success, frame = cap.read()
    count = 0

    while success:
        if count % (frame_rate * interval) == 0:
            frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        success, frame = cap.read()
        count += 1
    cap.release()
    return frames

def process_frame(llm_client, frame, prompt):
    encoded_image = encode_cv2_image(frame)
    try:
        llm_request = get_chat_request(encoded_image, prompt)
        llm_payload = get_chat_detail(llm_request,visionModel)
        llm_response = llm_client.chat(llm_payload)
        return llm_response.data.chat_response.choices[0].message.content[0].text
    except Exception as e:
        return f"Error processing frame: {str(e)}"

def process_frames_parallel(llm_client, frames, prompt):
    with ThreadPoolExecutor() as executor:
        results = list(tqdm(
            executor.map(lambda frame: process_frame(llm_client, frame, prompt), frames),
            total=len(frames),
            desc="Processing frames"
        ))
    return results

def generate_final_summary(llm_client, frame_summaries):
    combined_summaries = "\n".join(frame_summaries)
    final_prompt = (
        "You are a video content summarizer. Below are summaries of individual frames extracted from a video. "
        "Using these frame summaries, create a cohesive and concise summary that describes the content of the video as a whole. "
        "Focus on providing insights about the overall theme, events, or key details present in the video, and avoid referring to individual frames or images explicitly.\n\n"
        f"{combined_summaries}"
    )
    try:
        llm_request = cohere_chat_request(user_prompt=final_prompt)
        llm_payload = get_chat_detail(llm_request,summarizeModel)
        llm_response = llm_client.chat(llm_payload)
        return llm_response.data.chat_response.text
    except Exception as e:
        return f"Error generating final summary: {str(e)}"

# Streamlit UI
st.title("Decode Images and Videos with OCI GenAI")
uploaded_file = st.sidebar.file_uploader("Upload an image or video", type=["png", "jpg", "jpeg", "mp4", "avi", "mov"])
user_prompt = st.text_input("Enter your prompt for analysis:", value="Describe the content of this image.")
lang_type = st.sidebar.selectbox("Output Language", ["English", "French", "Arabic", "Spanish", "Italian", "German", "Portuguese", "Japanese", "Korean", "Chinese"])

if uploaded_file:
    if uploaded_file.name.split('.')[-1].lower() in ["png", "jpg", "jpeg"]:
        # Image Analysis
        temp_image_path = "temp_uploaded_image.jpg"
        with open(temp_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.image(temp_image_path, caption="Uploaded Image", width=500)
        
        if st.button("Generate image Summary"):
            with st.spinner("Analyzing the image..."):
                try:
                    encoded_image = encode_image(temp_image_path)                  
                    llm_request = get_chat_request(encoded_image, user_prompt)
                    llm_payload = get_chat_detail(llm_request,visionModel)
                    llm_response = llm_client.chat(llm_payload)                   
                    llm_text = llm_response.data.chat_response.choices[0].message.content[0].text
                    st.success("OCI gen AI Response:")
                    st.write(llm_text)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    elif uploaded_file.name.split('.')[-1].lower() in ["mp4", "avi", "mov"]:
        
        # Video Analysis
        temp_video_path = "temp_uploaded_video.mp4"
        video_html = f"""
        <video width="600" height="300" controls>
            <source src="data:video/mp4;base64,{base64.b64encode(open(temp_video_path, 'rb').read()).decode()}" type="video/mp4">
            Your browser does not support the video tag.
        </video>
    """
        st.markdown(video_html, unsafe_allow_html=True)
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # st.video(temp_video_path)
        st.write("Processing the video...")
        
        frame_interval = st.sidebar.slider("Frame extraction interval (seconds)", 1, 10, 1)
        frames = extract_frames(temp_video_path, interval=frame_interval)
        num_frames = len(frames)
        st.write(f"Total frames extracted: {num_frames}")
        
        frame_range = st.sidebar.slider("Select frame range for analysis", 0, num_frames - 1, (0, num_frames - 1))
        
        if st.button("Generate Video Summary"):
            with st.spinner("Analyzing selected frames..."):
                try:
                    selected_frames = frames[frame_range[0]:frame_range[1] + 1]
                    waiting_message = st.empty()
                    waiting_message.write(f"Selected {len(selected_frames)} frames for processing.")
                    # st.write(f"Selected {len(selected_frames)} frames for processing.")
                    frame_summaries = process_frames_parallel(llm_client, selected_frames, user_prompt)
                    # st.write("Generating final video summary...")
                    waiting_message.empty()
                    waiting_message.write("Generating final video summary...")
                    final_summary = generate_final_summary(llm_client, frame_summaries)
                    waiting_message.empty()                    
                    st.success("Video Summary:")
                    st.write(final_summary)
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
