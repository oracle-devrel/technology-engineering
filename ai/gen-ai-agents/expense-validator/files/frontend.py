import streamlit as st
from backend import process_expense_workflow

st.set_page_config(page_title="Employee Expense Validator", page_icon="📤")

st.title("Employee Expense Claim Validator")

# File uploader
uploaded_file = st.file_uploader("Upload Expense Claim PDF", type=["pdf"])
declared_amount = st.number_input("Enter Declared Total Amount ($)", min_value=0.0, step=10.0)

if uploaded_file and declared_amount > 0:
    st.success("✅ PDF uploaded and amount entered.")

    with st.spinner("Running extraction and validation workflow..."):
        try:
            pdf_bytes = uploaded_file.read()
            extracted_data, validations = process_expense_workflow(pdf_bytes, declared_amount)

            st.subheader("🔎 Extracted Expense Data")
            st.json(extracted_data, expanded=False)

            st.subheader("Validation Results")
            for message in validations:
                if message.startswith("⚠️") or message.startswith("❌"):
                    st.error(message)
                elif message.startswith("✅"):
                    st.success(message)
                else:
                    st.info(message)

        except Exception as e:
            st.error(f"❌ Error: {str(e)}. Please check the uploaded file or inputs.")

