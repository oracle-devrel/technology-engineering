# ========================================
# Imports
# ========================================
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain.document_loaders import PyPDFLoader
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.docstore.document import Document

import streamlit as st
import io
import base64
import cv2
import os
import ast
from datetime import timedelta

# ========================================
# Helper Functions
# ========================================

def encode_image(image_path):
    """Encodes an image to base64 format for LLM input."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_frames(video_path, interval, output_folder="frames"):
    """
    Extracts frames from a video at a specified interval.
    
    Args:
        video_path (str): Path to the video file.
        interval (int): Frame extraction interval.
        output_folder (str): Directory to store extracted frames.
    
    Returns:
        list: Tuples containing frame file paths and corresponding timecodes.
    """
    os.makedirs(output_folder, exist_ok=True)
    video_capture = cv2.VideoCapture(video_path)
    frame_count = 0
    extracted_frames = []
    frame_rate = int(video_capture.get(cv2.CAP_PROP_FPS))

    while True:
        ret, frame = video_capture.read()
        if not ret:
            break

        if frame_count % interval == 0:
            frame_path = os.path.join(output_folder, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
            timecode = str(timedelta(seconds=frame_count // frame_rate))
            extracted_frames.append((frame_path, timecode))

        frame_count += 1

    video_capture.release()
    return extracted_frames

# ========================================
# Streamlit App UI and Logic
# ========================================

def videoAnalyze():
    # Title of the app
    st.title("Analyze Images and Videos with OCI Generative AI")
    
    # Sidebar inputs
    with st.sidebar:
        st.title("Parameters")
        st.selectbox("Output Language", ["English", "French"])
        confidenceThreshold = st.slider("Confidence Threshold", 0.0, 1.0)
        st.caption("Adjust the corresponding parameters to control the AI's responses and accuracy")
        interval = st.slider("Select the desired interval: ", 1, 48)
    
    # Optional: Custom styling
    with open('style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

    # File upload
    uploaded_file = st.file_uploader("Upload an image or video", type=["png", "jpg", "jpeg", "mp4", "avi", "mov"])
    user_prompt = st.text_input("Enter your prompt for analysis:", value="Is this frame suitable for PG-rated movies?")

    if uploaded_file is not None:
        # Save the uploaded file locally
        temp_video_path = "temp_uploaded_video.mp4"
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Check if file is a video
        if uploaded_file.type.startswith("video"):
            # Extract frames at defined interval
            with st.spinner("Extracting frames from the video..."):
                frames_with_timecodes = extract_frames(temp_video_path, interval)
                st.success(f"Extracted {len(frames_with_timecodes)} frames for analysis.")

            # Instantiate the OCI Generative AI Vision model
            llm = ChatOCIGenAI(
                model_id="meta.llama-3.2-90b-vision-instruct",
                compartment_id="",  # <-- Add your compartment ID here
                model_kwargs={"max_tokens": 2000, "temperature": 0}
            )

            # Loop through each frame for analysis
            violence_detected = False
            for frame_path, timecode in frames_with_timecodes:
                with st.spinner("Analyzing the frame..."):
                    try:
                        # Prepare the frame and messages
                        encoded_frame = encode_image(frame_path)
                        human_message = HumanMessage(
                            content=[
                                {"type": "text", "text": user_prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_frame}"}},
                            ]
                        )

                        system_message = SystemMessage(
                            content="You are an expert in assessing the age-appropriateness of visual content. Your task is to analyze the provided image and provide a detailed assessment of its suitability for a PG-rated audience." 
                                    "Respond only in dictionary format. Examples:\n"
                                    "If the frame contains elements unsuitable for a PG-rating: "
                                    "{'AgeAppropriate': 'not-appropriate', 'response': 'Brief description of the scene (e.g., shows graphic violence, explicit nudity).', 'ConfidenceLevel': 0.95}\n"
                                    "If the frame complies with PG-rating guidelines: "
                                    "{'AgeAppropriate': 'appropriate', 'response': 'Brief description of the scene (e.g., depicts a serene landscape, no concerning elements).', 'ConfidenceLevel': 0.90}\n"
                                    "Ensure your responses are concise and focused on the image's content. Avoid unnecessary details or conversations unrelated to the task."
                        )

                        # LLM call
                        ai_response = llm.invoke(input=[human_message, system_message])
                        print(ai_response.content)
                        response_dict = ast.literal_eval(ai_response.content)

                        # Parse and validate the response
                        violence_status = response_dict.get("AgeAppropriate")
                        detailed_response = response_dict.get("response")
                        confidence = float(response_dict.get("ConfidenceLevel"))

                        # Display flagged frames
                        if violence_status == "not-appropriate" and confidence >= confidenceThreshold:
                            st.write(f"Frame Analysis: {detailed_response}")
                            st.write(f"Timecode: {timecode}")
                            st.image(frame_path, caption="Analyzing Frame", width=500)
                            violence_detected = True

                    except Exception as e:
                        print(f"Error analyzing frame: {str(e)}")

            # Final result
            if violence_detected:
                st.warning("This movie is NOT PG Rated!")
            else:
                st.success("This movie is PG Rated!")
