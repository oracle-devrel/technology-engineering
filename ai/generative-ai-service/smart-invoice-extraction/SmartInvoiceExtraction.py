import pandas as pd
import json
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
import streamlit as st
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
import base64
from pdf2image import convert_from_bytes
import io

# Helper function to convert a list of images into byte arrays for further processing
def save_images(images, output_format="JPEG"):
    image_list = []
    for image in images:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)
        image_list.append(img_byte_arr)
    return image_list

# Helper function to encode an image to base64 for sending to LLM
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Save extracted data to a CSV file and show success message in Streamlit
def save_to_csv(data, file_name="extracted_data.csv"):
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)
    st.success(f"Data saved to {file_name}")

# Extract key headers from the first image of a PDF invoice
def extractor(image_list):
    # Replace this with your own compartment ID
    compID = "<YOUR_COMPARTMENT_OCID_HERE>"

    # Load a multimodal LLM for invoice header analysis
    llm = ChatOCIGenAI(
        model_id="meta.llama-3.2-90b-vision-instruct",  # Replace with your model ID
        compartment_id=compID,
        model_kwargs={"max_tokens": 2000, "temperature": 0}
    )

    # Encode the first page as base64
    encoded_frame = base64.b64encode(image_list[0].getvalue()).decode("utf-8")

    with st.spinner("Extracting the key elements"):
        # Provide system instruction to extract headers from invoice
        system_message = SystemMessage(
            content="""Given this invoice, extract in list format, all the headers that can be needed for analysis
            For example: [\"REF. NO.\", \"INSURED\", \"REINSURED\", \"POLICY NO.\", \"TYPE\", \"UNDERWRITER REF. NO.\", \"PERIOD\", \"PARTICULARS\", \"PPW DUE DATE\"]
            Return the answer in a list format, and include nothing else at all in the response.
            """
        )

        # Human message includes the image
        human_message = HumanMessage(
            content=[
                {"type": "text", "text": "This is my invoice"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_frame}"}},
            ]
        )

        # Invoke the LLM and extract elements
        ai_response = llm.invoke(input=[human_message, system_message])
        st.caption("Here are some key elements you may want to extract")
        return eval(ai_response.content)

# Main Streamlit app function
def invoiceAnalysisPlus():
    st.title("Invoice Data Extraction")

    with st.sidebar:
        st.title("Parameters")
        # Replace with your own compartment ID
        compID = "<YOUR_COMPARTMENT_OCID_HERE>"
        user_prompt = st.text_input("Input the elements you are looking to extract here")
        st.caption("Our AI assistant has extracted the following key elements from the invoice. Please select the elements you wish to extract.")

    uploaded_file = st.file_uploader("Upload your invoices here:", type=["pdf"])

    if uploaded_file is not None:
        with st.spinner("Processing..."):
            # Convert PDF to image list
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read(), fmt="jpeg")
            else:
                images = [convert_from_bytes(uploaded_file.read(), fmt="jpeg")[0]]

            # Save as byte streams
            image_list = save_images(images)

        # Load both image-based and text-based LLMs
        llm = ChatOCIGenAI(
            model_id="meta.llama-3.2-90b-vision-instruct",  # Replace with your model ID
            compartment_id=compID,
            model_kwargs={"max_tokens": 2000, "temperature": 0}
        )
        llm_for_prompts = ChatOCIGenAI(
            model_id="cohere.command-r-plus-08-2024",  # Replace with your model ID
            compartment_id=compID,
            model_kwargs={"max_tokens": 2000, "temperature": 0}
        )

        # Select box UI for user to pick elements and their data types
        data_types = ["Text", "Number", "Percentage", "Date"]
        elements = []

        if "availables" not in st.session_state:
            st.session_state.availables = extractor(image_list)

        for i in range(3):  # Max 3 fields
            col1, col2 = st.columns([2, 1])
            with col1:
                name = st.selectbox(f"Select an element {i+1}", st.session_state.availables, key=f"name_{i}", index=i)
            with col2:
                data_type = st.selectbox(f"Type {i+1}", data_types, key=f"type_{i}")
                elements.append((name, data_type))

        # Generate appropriate prompt based on selected or input fields
        if elements:
            system_message_cohere = SystemMessage(
                content=f"""
                Based on the following set of elements {elements}, with their respective types, extract their values and respond only in valid JSON format (no explanation):
                {', '.join([f'- {e[0]}' for e in elements])}
                For example:
                {{
                    {elements[0][0]}: "296969",
                    {elements[1][0]}: "296969",
                    {elements[2][0]}: "296969"
                }}
                """
            )
            ai_response_cohere = system_message_cohere
        else:
            system_message_cohere = SystemMessage(
                content=f"""
                Generate a system prompt to extract fields based on user-defined elements: {user_prompt}.
                Output should be JSON only. No other text.
                """
            )
            ai_response_cohere = llm_for_prompts.invoke(input=[system_message_cohere])

        # Extracted data list
        extracted_data = []

        with st.spinner("Analyzing invoice..."):
            for idx, img_byte_arr in enumerate(image_list):
                try:
                    encoded_frame = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")

                    if elements:
                        system_message = ai_response_cohere
                    else:
                        system_message = SystemMessage(content=ai_response_cohere.content)

                    human_message = HumanMessage(
                        content=[
                            {"type": "text", "text": "This is my invoice"},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_frame}"}},
                        ]
                    )

                    ai_response = llm.invoke(input=[human_message, system_message])
                    json_start = ai_response.content.find('{')
                    json_end = ai_response.content.find('}', json_start)
                    json_data = ai_response.content[json_start:json_end + 1]

                    response_dict = json.loads(json_data)
                    response_dict["File Name"] = uploaded_file.name
                    response_dict["Page Number"] = idx + 1
                    extracted_data.append(response_dict)

                except Exception as e:
                    st.error(f"Error processing page {idx+1}: {str(e)}")

        # Display and save results
        if extracted_data:
            save_to_csv(extracted_data)
            st.dataframe(pd.DataFrame(extracted_data))

# Run the app
if __name__ == "__main__":
    invoiceAnalysisPlus()