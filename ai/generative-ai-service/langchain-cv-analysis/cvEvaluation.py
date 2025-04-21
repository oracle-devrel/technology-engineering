"""
CV Evaluation App using Oracle Gen AI and Streamlit

This module implements a Streamlit-based web application for evaluating resumes
against job descriptions using Oracle's Generative AI via the ChatOCIGenAI model.

Modules and Functionality:
--------------------------
- Loads job description templates and resume PDFs.
- Uses a predefined prompt to query Oracle Gen AI for resume evaluation.
- Parses and visualizes the response in an interactive format.
- Supports multiple resume uploads.
- Assigns classification labels such as 'Excellent', 'Strong', etc.
- Highlights missing keywords and provides reasoning for classification.

Dependencies:
-------------
- os
- json
- PyPDF2
- streamlit
- langchain_community (ChatOCIGenAI)

Functions:
----------
- input_pdf_text(uploaded_file): Extracts and returns text from a PDF file.
- parse_response(response): Parses the model's JSON response into usable parts.
- cvEvaluate(): Launches the Streamlit UI and handles interactions.

Usage:
------
Run the script with Streamlit:
    streamlit run <script_name>.py

Author: Ali Ottoman
"""

import os
import json
import PyPDF2 as pdf
import streamlit as st
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI



llm = ChatOCIGenAI(
    model_id="", #TO-DO: Add the model name here
    compartment_id="", #TO-DO: Add the compartment ID here
    model_kwargs={"temperature": 0, "max_tokens": 1000}
)

def input_pdf_text(uploaded_file):
    """
    Extracts and returns text from the provided PDF file.
    """
    reader = pdf.PdfReader(uploaded_file)
    text = ""
    for page in range(len(reader.pages)):
        page = reader.pages[page]
        text += str(page.extract_text())
    return text

def parse_response(response):
    """
    Parses the model's response JSON and extracts relevant details like name, JD match, 
    missing keywords, profile summary, and reasoning.
    """
    try:
        response_json = json.loads(response.split('}')[0] + '}')
        name = response_json.get("Name", "N/A")
        jd_match = response_json.get("JD Match", "N/A")
        missing_keywords = response_json.get("MissingKeywords", [])
        profile_summary = response_json.get("Profile Summary", "N/A")
        reason = response_json.get("Reason", "N/A")
        return name, jd_match, missing_keywords, profile_summary, reason
    except (json.JSONDecodeError, IndexError) as e:
        st.error(f"Error parsing response: {e}")
        return "N/A", "N/A", [], "N/A", "N/A"


# Prompt Template
input_prompt = """
You are a highly advanced and experienced ATS (Application Tracking System) with deep expertise in evaluating resumes in the tech field.

Your task is to:
1. Give a unique name to the candidate
2. Evaluate the resume provided against the given job description (JD).
3. Assign a classification label for the match based on the alignment between the resume and the JD, using the following range:
   - "Not Suited" (very low alignment with the JD)
   - "Unlikely" (partial alignment but missing key qualifications or skills)
   - "Possible" (moderate alignment with some gaps in experience or keywords)
   - "Strong" (high alignment with minor gaps)
   - "Excellent" (very high alignment with minimal to no gaps)
4. Identify keywords in the job description and list any missing keywords or key competencies essential for the role.
5. Summarize the candidates profile concisely.
6. Clearly explain why the resume is classified as such, including suggestions for improvement if applicable.

Here is the data:
Resume: {text}
Job Description: {jd}

Consider the competitive nature of the job market and ensure high accuracy in your evaluation. Your response MUST and always has to adhere to the following JSON structure:
{{"Name": "name", "JD Match": "classification label", "MissingKeywords": ["list of missing keywords"], "Profile Summary": "concise profile summary", "Reason": "reason for classification with improvement suggestions"}}
"""

def cvEvaluate():
    """
    Launches the Streamlit web app, handles user inputs (job descriptions and resumes),
    invokes the OCI Gen AI model, and displays the evaluation results.
    """
    # Streamlit app
    st.title("CV Evaluation (ATS) using Oracle Gen AI")

    # Set up the session state for the job description
    if "jd" not in st.session_state:
        st.session_state["jd"] = ""

    st.header("Available Opportunities:")
    col1, col2, col3 = st.columns(3)
    
    st.session_state["jd"] = st.text_area("Please provide the job description or select from the below open-opportunities")
    # Place buttons in each column
    with col1:
        if st.button("Human Resources Specialist"):
            st.session_state["jd"] = """**Job Title**: Human Resources Specialist

                            **Company**: XYZ Energy

                            **Location**: London, UK

                            **Job Description**:

                            XYZ Energy is seeking a dedicated and proactive HR Specialist to join our team. In this role, you will support our mission of powering sustainable energy solutions by managing employee relations, recruitment, and organizational development.

                            **Key Responsibilities**:

                            - Coordinate end-to-end recruitment for various roles within the energy sector.
                            - Manage onboarding processes to ensure new hires integrate seamlessly.
                            - Provide support for employee relations, including conflict resolution and policy interpretation.
                            - Implement HR initiatives to enhance employee engagement and retention.
                            - Ensure compliance with employment laws and regulations.

                            **Qualifications**:

                            - Bachelor’s degree in Human Resources or related field.
                            - 2+ years of HR experience, preferably in the energy or utility sector.
                            - Strong interpersonal and organizational skills.
                            - Familiarity with HR software and best practices.

                            Join XYZ Energy and play a key role in fostering a thriving workplace culture that drives our commitment to sustainable energy."""
            st.write("Human Resources Specialist role is selected")
    with col2:
        if st.button("Technical Specialist"):
            st.session_state["jd"] = """Job Title: Technical Specialist

                        Company: XYZ Energy

                        Location: London, UK

                        Job Description:

                        XYZ Energy is seeking a dynamic and skilled Technical Specialist to join our innovative team. In this role, you will contribute to our mission of delivering sustainable energy solutions by leveraging your technical expertise to support and enhance operations, systems, and technology implementations.

                        Key Responsibilities:

                        Provide technical support for the implementation, maintenance, and optimization of energy systems and technologies.
                        Collaborate with cross-functional teams to identify and address technical challenges in energy projects.
                        Analyze system performance data to identify areas for improvement and recommend solutions.
                        Manage the integration of new technologies into existing operations, ensuring minimal disruption.
                        Support troubleshooting efforts, resolve technical issues, and deliver expert guidance to internal and external stakeholders.
                        Stay updated on emerging technologies and industry trends to maintain XYZ Energy's competitive edge.
                        Qualifications:

                        Bachelor’s degree in Engineering, Computer Science, or a related technical field.
                        3+ years of experience in a technical role, preferably within the energy or utilities sector.
                        Strong analytical and problem-solving skills with the ability to interpret complex technical data.
                        Hands-on experience with energy systems, software tools, and technical project management.
                        Excellent communication and collaboration skills to engage with diverse stakeholders.
                        A passion for sustainability and a commitment to supporting XYZ Energy's vision for a greener future.
                        Join XYZ Energy and help us drive innovation in the energy industry as we work together to power a more sustainable tomorrow."""
            st.write("Technical Specialist role is selected")
    with col3:
        if st.button("Customer Support Agent"):
            st.session_state["jd"] = """"Job Title: Customer Support Agent

                        Company: XYZ Energy

                        Location: London, UK

                        Job Description:

                        XYZ Energy is looking for a friendly and proactive Customer Support Agent to join our team. In this role, you will be the first point of contact for our customers, providing exceptional support and ensuring a seamless customer experience as we deliver sustainable energy solutions.

                        Key Responsibilities:

                        Respond to customer inquiries via phone, email, and chat, providing timely and accurate information.
                        Resolve customer issues, including billing, service requests, and technical concerns, with professionalism and efficiency.
                        Guide customers through the onboarding process and educate them about our energy solutions and services.
                        Maintain detailed records of customer interactions and escalate complex issues to the appropriate teams.
                        Collaborate with internal departments to ensure customer needs are met promptly and effectively.
                        Continuously seek feedback to improve the customer support experience and processes.
                        Qualifications:

                        High school diploma or equivalent; a bachelor’s degree is a plus.
                        1+ years of experience in a customer support or service role, ideally in the energy or utility sector.
                        Strong communication and interpersonal skills with a customer-first attitude.
                        Ability to handle challenging situations with empathy and problem-solving skills.
                        Proficiency in CRM systems and standard office software.
                        A passion for sustainable energy and a commitment to helping customers achieve their goals.
                        Join XYZ Energy and be a key player in delivering outstanding service to our customers while contributing to a greener future."""
            st.write("Customer Support agent role is selected")
    

    # Resumes to be analyzed
    uploaded_files = st.sidebar.file_uploader("Upload Your Resumes", accept_multiple_files=True, type="pdf", help="Please upload the pdfs")

    submit = st.button("Submit")
    with st.spinner("Processing. Please wait...."):
        if submit:
            if uploaded_files:
                print(st.session_state["jd"])
                for uploaded_file in uploaded_files:
                    if uploaded_file is not None:
                        resume_text = input_pdf_text(uploaded_file)
                        resume_name = os.path.splitext(uploaded_file.name)[0]  # Use file name without extension as candidate name
                        formatted_prompt = input_prompt.format(text=resume_text, jd=st.session_state["jd"])
                        response = llm.invoke(formatted_prompt)
                        
                        print(response)
                        
                        name, jd_match, missing_keywords, profile_summary, reason = parse_response(response)

                        # Determine selection status
                        if jd_match != "N/A" and jd_match in ['Excellent', 'Strong', 'Possible']:
                            status = "Selected"
                            status_color = "green"
                        else:
                            status = "Rejected"
                            status_color = "red"

                        # Display the result
                        st.markdown(f"## <span style='color:cadetblue'>{name}'s Resume</span> File ({resume_name})", unsafe_allow_html=True)
                        st.markdown(f"**<span style='color:Orange'>JD Match:</span>** {jd_match}", unsafe_allow_html=True)
                        st.markdown(f"**Status:** <span style='color:{status_color}'>{status}</span>", unsafe_allow_html=True)
                        
                        # Create a collapsible section for additional details
                        with st.expander("View More Details"):
                            st.markdown(f"**<span style='color:cadetblue'>Profile Summary:</span>** {profile_summary}", unsafe_allow_html=True)
                            st.markdown(f"**<span style='color:cadetblue'>Missing Keywords:</span>** {', '.join(missing_keywords) if missing_keywords else 'None'}", unsafe_allow_html=True)
                            st.markdown(f"**<span style='color:cadetblue'>Reason:</span>** {reason}", unsafe_allow_html=True)
            else:
                st.error("Please provide both the job description and resumes for matching.")