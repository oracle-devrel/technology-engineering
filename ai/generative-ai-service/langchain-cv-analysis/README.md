# CV Evaluation App using Oracle Gen AI 


This is a Streamlit-based web application that evaluates resumes (CVs) against job descriptions using Oracle Cloud Infrastructure's Generative AI via Langchain `ChatOCIGenAI`.

Reviewed: 22.09.2025

---

## 🔍 How to use this asset

- Upload multiple resumes in PDF format
- Select or input a job description
- Evaluate resumes using Oracle Gen AI
- Receive classification like `Excellent`, `Strong`, `Possible`, etc.
- Get profile summaries, missing keywords, and improvement suggestions
- Interactive Streamlit interface

---

## 🎯 When to Use This Asset (Who & When)

### Who
- **HR & talent acquisition teams** screening large volumes of CVs  
- **Hiring managers** comparing candidates against role requirements  
- **Recruitment operations teams** standardising resume evaluations   

### When
- When evaluating **multiple PDF resumes** against a single role  
- When consistent, explainable **candidate classification** is needed  
- When identifying **skill gaps and missing keywords** is important  
- When reducing **manual CV screening time** is a priority  

---

## 📁 Project Structure

```
.
├── main.py                  # Streamlit application file
├── LoadProperties2.py       # Loads configuration details (custom module)
├── requirements.txt         # Required packages
```

---

## ⚙️ Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-repo/cv-evaluation-genai.git
   cd cv-evaluation-genai
   ```

2. **Create a virtual environment (optional but recommended)**  
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Update the model name and compartment ID**  
   ```bash
   streamlit run main.py
   ```

5. **Run the Streamlit app**  
   ```bash
   streamlit run main.py
   ```

---

## 📦 Dependencies

- `streamlit`
- `PyPDF2`
- `langchain_community`
- `oci` (for Oracle Cloud access)

Make sure you have valid OCI credentials and access to the Generative AI service.

---

## 🧠 Technologies

- **Oracle Generative AI**: For advanced natural language processing and resume evaluation
- **LangChain**: For structured LLM integration
- **Streamlit**: For building a fast, interactive UI

---

## ✅ Example Use Case

1. Choose a job role or paste your custom Job Description.
2. Upload one or more resume PDFs.
3. Click **Submit**.
4. View evaluation results, summaries, and suggested improvements.

## License
Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE.txt) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 
