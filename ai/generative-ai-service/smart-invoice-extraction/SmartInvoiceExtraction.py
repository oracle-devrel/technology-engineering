"""
Smart Invoice Extraction

A Streamlit-based invoice data extraction tool leveraging Oracle Cloud Infrastructure (OCI)
Generative AI models for multimodal (text + image) processing.

This module provides:

- Helper functions:
  - save_images(images, output_format="JPEG"):
      Convert PIL Image objects to in-memory byte streams for downstream processing.
  - encode_image(image_path):
      Read an image file from disk and return its Base64-encoded string.
  - save_to_csv(data, file_name="extracted_data.csv"):
      Persist a list of dicts to a CSV file.

- extractor(image_list):
    Uses the image of a PDF invoice to identify and extract key header fields, by:
      • Initializing an LLM (meta.llama-3.2-90b-vision-instruct)
      • Encoding the image as Base64
      • Sending a system + human message prompt to extract invoice headers in list format.

- invoiceAnalysisPlus():
    The main Streamlit application which:
      • Renders a UI for uploading PDF invoices
      • Converts PDFs to JPEG images and prepares byte streams
      • Invokes extractor() to propose candidate fields
      • Constructs and sends prompts to two OCI LLMs:
          – A vision model for image-based extraction
          – A text-only model (cohere.command-r-plus-08-2024) for dynamic prompt generation
      • Displays results in a DataFrame and saves them to CSV

Usage:
    Run the module as a standalone script:
        streamlit run invoice_analysis.py

Author: Ali Ottoman
"""

import io
import json
import base64
import pandas as pd
import streamlit as st
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pdf2image import convert_from_bytes


# Helper function to convert a list of images into byte arrays for further processing
def save_images(images, output_format="JPEG"):
    """
        Convert PIL Image objects to in-memory byte streams for downstream processing.
    """
    image_list = []
    for image in images:
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=output_format)
        img_byte_arr.seek(0)
        image_list.append(img_byte_arr)
    return image_list

# Helper function to encode an image to base64 for sending to LLM
def encode_image(image_path):
    """
        Read an image file from disk and return its Base64-encoded string.
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Save extracted data to a CSV file and show success message in Streamlit
def save_to_csv(data, file_name="extracted_data.csv"):
    """
        Persist a list of dicts to a CSV file.
    """
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)
    st.success(f"Data saved to {file_name}")

# Extract key headers from the first image of a PDF invoice
def extractor(image_list):
    """
        Uses the image of a PDF invoice to identify and extract key header fields
    """
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
def invoice_analysis_plus():
    """
        The main Streamlit application
    """
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
                    Based on the following set of elements {elements}, with their respective types ({elements[0][1]}, {elements[1][1]}, {elements[2][1]}), Extract the following details and provide the response only in valid JSON format (no extra explanation or text):
                    - {elements[0][0]}
                    - {elements[1][0]}
                    - {elements[2][0]}
                    Ensure the extracted data is formatted correctly as JSON and include nothing else at all in the response, not even a greeting or closing.
                    For example:
                    {{
                        {elements[0][0]}: "296969",
                        {elements[1][0]}: "296969",
                        {elements[2][0]}: "296969",
                    }}
                """)
            ai_response_cohere = system_message_cohere
        else:
            system_message_cohere = SystemMessage(
                content = f"""
                    Based on the following system prompt, create a new prompt accordingly based on the elements specified in the user prompt here ({user_prompt}). 

                    This is the system prompt template:
                    "
                    Extract the following details and provide the response only in valid JSON format (no extra explanation or text):
                    - **Debit / Credit Note No.**
                    - **Policy Period** 
                    - **Insured** 
                    - **Vessel Name** 
                    - **Details** 
                    - **Currency** 
                    - **Gross Premium 100%**
                    - **OIMSL Share** 
                    - **Total Deductions**
                    - **Net Premium** 
                    - **Premium Schedule**
                    - **Installment Amount**

                    Ensure the extracted data is formatted correctly as JSON and include nothing else at all in the response, not even a greeting or closing.

                    For example:
                    
                        "Debit / Credit Note No.": "296969",
                        "Policy Period": "Feb 20, 2024 to Jul 15, 2025",
                        "Insured": "Stealth Maritime Corp. S.A.",
                        "Vessel Name": "SUPRA DUKE - HULL & MACHINERY", (Make sure this is the entire vessel name only)
                        "Details": "SUPRA DUKE - Original Premium",
                        "Currency": "USD",
                        "Gross Premium 100%": 56973.63,
                        "OIMSL Share": 4557.89,
                        "Total Deductions": 979.92,
                        "Net Premium": 3577.97,
                        "Premium Schedule": ["Apr 20, 2024", "Jun 14, 2024", "Sep 13, 2024", "Dec 14, 2024", "Mar 16, 2025", "Jun 14, 2025"],
                        "Installment Amount": [372.87, 641.02, 641.02, 641.02, 641.02, 641.02]
                    
                    )" ensure your response is a system prompt format with an example of what the ouput should look like. Also ensure to mention in your gernerated prompt that no other content whatsover should appear except the JSON
            """)
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
    invoice_analysis_plus()
