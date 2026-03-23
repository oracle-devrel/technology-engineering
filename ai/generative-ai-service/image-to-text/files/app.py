# Author: Ansh
import streamlit as st
import oci
import base64
from PIL import Image

# OCI Configuration ( Put your compartment id below)
compartmentId = "ocid1.compartment.oc1..***************************"
llm_service_endpoint = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"

# Define functions
def get_message(encoded_image, user_prompt):
    content1 = oci.generative_ai_inference.models.TextContent()
    content1.text = user_prompt
    
    content2 = oci.generative_ai_inference.models.ImageContent()
    image_url = oci.generative_ai_inference.models.ImageUrl()
    image_url.url = f"data:image/jpeg;base64,{encoded_image}"
    content2.image_url = image_url
    
    message = oci.generative_ai_inference.models.UserMessage()
    message.content = [content1, content2]
    return message

def get_chat_request(encoded_image, user_prompt):
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

def get_chat_detail(chat_request):
    chat_detail = oci.generative_ai_inference.models.ChatDetails()
    chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(model_id="meta.llama-3.2-90b-vision-instruct")
    chat_detail.compartment_id = compartmentId
    chat_detail.chat_request = chat_request
    return chat_detail

# Streamlit UI
st.title("Image to Text with Oci Gen AI")
st.write("Upload an image, provide a prompt, and get a response from Oci Gen AI.")

# Upload image
uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

# Prompt input
user_prompt = st.text_input("Enter your prompt for the image:", value="Tell me about this image.")

if uploaded_file:
    # Display the uploaded image
    st.image(uploaded_file, caption="Uploaded Image", use_column_width=True)
    
    # Process and call the model
    if st.button("Generate Response"):
        with st.spinner("Please wait while the model processes the image..."):
            try:
                # Encode the image
                encoded_image = base64.b64encode(uploaded_file.getvalue()).decode("utf-8")
                
                # Setup OCI client
                CONFIG_PROFILE = "DEFAULT"
                config = oci.config.from_file('~/.oci/config', CONFIG_PROFILE)
                
                llm_client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config=config,
                    service_endpoint=llm_service_endpoint,
                    retry_strategy=oci.retry.NoneRetryStrategy(),
                    timeout=(10, 240)
                )
                
                # Get the chat request and response
                llm_request = get_chat_request(encoded_image, user_prompt)
                llm_payload = get_chat_detail(llm_request)
                llm_response = llm_client.chat(llm_payload)
                
                # Extract and display the response
                llm_text = llm_response.data.chat_response.choices[0].message.content[0].text
                st.success("Model Response:")
                st.write(llm_text)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
