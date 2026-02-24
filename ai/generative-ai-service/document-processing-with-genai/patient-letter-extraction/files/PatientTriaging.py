import pandas as pd
import json
import streamlit as st
import tempfile
import base64
import io
import os

from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage

from pdf2image import convert_from_bytes, convert_from_path
from docx import Document
from collections import OrderedDict

# Function to extract text from a Word (.docx) document
def extract_text_from_docx(file_path):
    """
    Extracts text from a .docx file and returns it as a single string.
    
    Parameters:
        file_path (str): The path to the .docx file.
    
    Returns:
        str: The extracted text from the document.
    """
    doc = Document(file_path)
    text = ' '.join(para.text.strip() for para in doc.paragraphs if para.text.strip())
    return text

# Function to save extracted data to a CSV file
def save_to_csv(data, file_name="extracted_data.csv"):
    """
    Saves extracted data to a CSV file.
    
    Parameters:
        data (list or dict): Extracted data in dictionary format.
        file_name (str): Name of the CSV file (default: 'extracted_data.csv').
    """
    if isinstance(data, dict):
        data = [data]  # Convert dictionary to a list of dictionaries
    df = pd.DataFrame(data)
    df.to_csv(file_name, index=False)

# Streamlit UI for Patient Triage Extraction
def patientTriage():
    """
    Streamlit app function for processing patient triage letters.
    
    Allows users to upload patient referral letters (.pdf, .docx) and processes them using an LLM to extract key details.
    """
    st.title("🏥 Patient Triage Extraction")
    
    # Sidebar for file upload
    with st.sidebar:
        st.title("Upload your letters here")
        uploaded_files = st.file_uploader("Upload your patient file(s) here", type=["pdf", "docx"], accept_multiple_files=True)
    
    extracted_data = []  # List to store extracted data from all uploaded files
    
    # Process each uploaded file
    if uploaded_files:
        for uploaded_file in uploaded_files:
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_file.write(uploaded_file.read())
                temp_path = temp_file.name
            
            # Extract text from docx files
            if uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                text_pages = extract_text_from_docx(temp_path)
            else:
                st.error("Unsupported file format!")
                continue
            
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # TO-DO: Initialize OCI AI model
                llm = ChatOCIGenAI(
                    model_id= "Add your model name",
                    compartment_id="Add your compartment ID",
                    model_kwargs={"temperature": 0, "max_tokens": 2000},
                )
                
                # Construct system message to ensure structured JSON response
                system_message = SystemMessage(
                    content="""
                    You are an AI system processing patient referral letters to the Dermatology Department. Your task is to extract key details from each letter and return the information strictly in valid JSON format.

                    Extract the following details:
                    - Referring Doctor: Extract the full name of the doctor if mentioned.
                    - Condition: Identify the primary dermatological condition mentioned.
                    - Recommended Clinic: Assign the relevant dermatology clinic EXCLUSIVELY from this list: 
                      (Acne, Eczema and Dermatitis, Psoriasis, Skin Cancer, Hair and Nail Disorders, Laser Skin Treatments, Male Genital and Vulval Skin Disorders, Patch Testing for Contact Dermatitis, Leg Ulcers, Cosmetic Camouflage)
                    - Brief Summary: A concise summary of the condition and reason for referral.

                    Ensure the response is formatted strictly as JSON, without additional text.

                    Example Response:
                    {
                        "Referring Doctor": "Dr. Sarah Thompson"/ "Not mentioned",
                        "Condition": "Severe plaque psoriasis",
                        "Recommended Clinic": "Psoriasis",
                        "Brief Summary": "Patient has been experiencing severe plaque psoriasis unresponsive to topical treatments. Referral requested for specialist evaluation and potential systemic therapy."
                    }
                    """
                )
                
                # Construct human message with extracted text
                human_message = HumanMessage(
                    content=f"Patient triage letter content: {text_pages}"
                )
                
                # Invoke the LLM with system and human messages
                ai_response = llm.invoke(input=[system_message, human_message])
                response_dict = json.loads(ai_response.content)  # Convert response to dictionary
                
                extracted_data.append(response_dict)
        
        # Save extracted data and display in Streamlit
        if extracted_data:
            save_to_csv(extracted_data)
            st.dataframe(pd.DataFrame(extracted_data))

# Run the Streamlit app
if __name__ == "__main__":
    patientTriage()
