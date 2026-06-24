"""
Document Understanding with LLMs

1) Input pdfs/images/docs
2) Output a JSON of each, and have it saved

To run this code: 
1) pip install -r requirements.txt
2) streamlit run doc_llm.py

Author: Ali Ottoman

"""

import io
import json
import os
import base64
import pandas as pd
from PIL import Image
import streamlit as st
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.messages import HumanMessage, SystemMessage
import oci
from oci.ai_document.models import (
    AnalyzeDocumentDetails,
    InlineDocumentDetails,
    DocumentTextExtractionFeature
)
from oci.ai_document import AIServiceDocumentClient
from pdf2image import convert_from_bytes
from config import COMPARTMENT_ID, MODEL_ID

# Load OCI config
config = oci.config.from_file(profile_name="DEFAULT")
document_client = AIServiceDocumentClient(config)

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
def du_extractor(image_list, e1, e2, e3):
    """
        Uses the image of a PDF invoice to identify and extract key header fields
    """

    # Load LLM
    llm = ChatOCIGenAI(
        model_id=MODEL_ID,
        compartment_id=COMPARTMENT_ID,
        model_kwargs={"max_tokens": 2000, "temperature": 0},
    )

    # Encode the first page as base64
    encoded_frame = base64.b64encode(image_list[0].getvalue()).decode("utf-8")

    with st.spinner("Extracting the key elements"):
        # Document Understanding extraction
        inline_doc = InlineDocumentDetails(
            data=encoded_frame,
            source='INLINE'
        )

        analyze_details = AnalyzeDocumentDetails(
            compartment_id=COMPARTMENT_ID,
            features=[DocumentTextExtractionFeature()],
            document=inline_doc,
            language="ar"
        )

        # To skip blank pages:

        doc_response = document_client.analyze_document(analyze_details)
        response_dict = oci.util.to_dict(doc_response.data)
        string_doc_result = json.dumps(response_dict, indent=2)

        with st.sidebar:
            if e1 and e2 and e3:
                # Adjust the prompt as necessary with the additional list of documents for classification
                system_prompt = (
                    f"""You are an intelligent assistant that extracts structured data from OCR'd documents.
                    1) Classify document from this list: documents = [
                        "Account Opening Form",
                        "General Banking Services Agreement",
                        "Signature",
                        "KFS",
                        "Background Screening",
                        "CDD/EDD form",
                        "FATCA",
                        "CRS / Self Certification forms",
                        "VISA",
                        "Passport",
                        "Emirates ID",
                        "ICP Verification proof",
                        "Salary Certificate/Pay slip",
                        "Trade License",
                        "Registered Property Purchase Agreement/Title",
                        "Tenancy Contract / Lease agreement",
                        "Utility Bill",
                        "Declaration from Landlord/Employer",
                        "Wealth Statement / disclosure for wealth customers and PEP",
                        "AECB Report",
                        "Credit Approval Memo",
                        "Customer profile",
                        "Bank Statement",
                        "Financial Statement / Tax Return",
                        "Municipal Certificate",
                        "Emails",
                        "Letter of Reference",
                        "Any Other Documents Received - Other",
                        "Blank"
                    ]
                    2) Extract fields:1. {e1}2. {e2}3. {e3}
                    
                    Respond exactly in this JSON format, do not include any other text or ```json or ```:
                    {{
                        classification: invoice,
                        {e1}": "<value>",
                        {e2}": "<value>",
                        {e3}": "<value>"
                    }} 
                    If a field is not found, return null for that value.
                    """
                )

                document_input = f"Document OCR JSON:\n{string_doc_result}"

                prompt = f"{system_prompt}\n\n{document_input}"

                ai_response = llm.invoke(prompt)
                return ai_response.content

def llm_extractor(image_list, e1, e2, e3):
    """
    Uses LLM directly on the image to extract same elements.
    """
    llm = ChatOCIGenAI(
        model_id="meta.llama-4-maverick-17b-128e-instruct-fp8",
        compartment_id=COMPARTMENT_ID,
        model_kwargs={"max_tokens": 2000, "temperature": 0}
    )

    encoded_frame = base64.b64encode(image_list[0].getvalue()).decode("utf-8")

    system_message = SystemMessage(
                            content=
        f"""You are an AI assistant that extracts information from visual documents.
        Given a document image, extract the following 4 fields:
        1. Classification of documents = [
                        "Account Opening Form",
                        "General Banking Services Agreement",
                        "Signature",
                        "KFS",
                        "Background Screening",
                        "CDD/EDD form",
                        "FATCA",
                        "CRS / Self Certification forms",
                        "VISA",
                        "Passport",
                        "Emirates ID",
                        "ICP Verification proof",
                        "Salary Certificate/Pay slip",
                        "Trade License",
                        "Registered Property Purchase Agreement/Title",
                        "Tenancy Contract / Lease agreement",
                        "Utility Bill",
                        "Declaration from Landlord/Employer",
                        "Wealth Statement / disclosure for wealth customers and PEP",
                        "AECB Report",
                        "Credit Approval Memo",
                        "Customer profile",
                        "Bank Statement",
                        "Financial Statement / Tax Return",
                        "Municipal Certificate",
                        "Emails",
                        "Letter of Reference",
                        "Any Other Documents Received - Other",
                        "Blank"
                    ]
        1. {e1}
        2. {e2}
        3. {e3}

         Some field names may be provided in Arabic (e.g., "الاسم"), and these may also appear in the document in either Arabic or English (e.g., "Name"). If a field is provided in Arabic:
         - First, search for a matching Arabic label in the document and return its value.
         - If not found, search for the English equivalent and return that value.
        Respond exactly in this JSON format, do not include any other text or ```json or ```:
        {{
            "classification": "<value>",
            "{e1}": "<value>",
            "{e2}": "<value>",
            "{e3}": "<value>"
        }}

        If a field is not found, return null for that value.
        If the element name is in Arabic, return the arabic value if present in the document, if not return the english value.
        """
    )

    human_message = HumanMessage(
        content=[
            {"type": "text", "text": "This is my image"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_frame}"}},
        ]
    )

    with st.spinner("Extracting using multimodal LLM..."):
        response = llm.invoke(input=[human_message, system_message])
        return json.loads(response.content)

# Comparison function to compare outputs from DU+LLM and LLM-only
def compare_outputs(du_output: dict, llm_output: dict):
    """
    Compare DU+LLM output with image-only LLM output.
    """
    comparison = {}
    keys = set(du_output.keys()).union(set(llm_output.keys()))

    for key in keys:
        val_du = du_output.get(key)
        val_llm = llm_output.get(key)

        if val_du == val_llm:
            comparison[key] = val_du
        elif val_du and not val_llm:
            comparison[key] = f"{val_du} (from DU)"
        elif val_llm and not val_du:
            comparison[key] = f"{val_llm} (from LLM)"
        else:
            comparison[key] = {
                "DU + LLM": val_du,
                "Multimodal LLM": val_llm
            }

    return comparison


# Main Streamlit app function
def du_vs_MMLLM():
    """
        The main Streamlit application
    """
    st.set_page_config(layout="wide")
    st.title("📄 DU + LLM (Command A) vs. Multi-Modal LLM (Maverick)")

    uploaded_file = st.file_uploader("Upload your invoices here:", type=["pdf", "jpg", "jpeg", "png"])
    with st.sidebar:
        st.title("Key Elements Extraction")
        st.caption("This will extract key elements from your document.")
        e1 = st.text_input("Field 1")
        e2 = st.text_input("Field 2")
        e3 = st.text_input("Field 3")

    if not (e1 and e2 and e3):
        st.info("Provide three fields to extract")

    if uploaded_file is not None and e1 and e2 and e3:
        with st.spinner("Processing..."):
            # Convert PDF to image list
            if uploaded_file.type == "application/pdf":
                images = convert_from_bytes(uploaded_file.read(), fmt="jpeg")
            else:
                image = Image.open(uploaded_file)
                images = [image]

            # Save as byte streams
            image_list = save_images(images)

            du_results_raw = du_extractor(image_list, e1, e2, e3)
            llm_results = llm_extractor(image_list, e1, e2, e3)

            # Try parsing DU results (stringified JSON)
            try:
                du_results = json.loads(du_results_raw)
            except:
                st.error("Could not parse DU + LLM result into JSON.")
                return

            comparison = compare_outputs(du_results, llm_results)

            # Display
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("🔍 DU + LLM Output")
                st.json(du_results)

            with col2:
                st.subheader("🧠 Multimodal LLM Output")
                st.json(llm_results)

            with col3:
                st.subheader("📊 Comparison")
                for key, val in comparison.items():
                    if isinstance(val, dict):
                        st.markdown(f"**{key}**")
                        st.markdown(
                            f"- 🟦 DU + LLM: `{val['DU + LLM']}`\n"
                            f"- 🟩 Multimodal: `{val['Multimodal LLM']}`"
                        )
                    else:
                        st.markdown(f"**{key}**: `{val}`")

# Run the app
if __name__ == "__main__":
    du_vs_MMLLM()
