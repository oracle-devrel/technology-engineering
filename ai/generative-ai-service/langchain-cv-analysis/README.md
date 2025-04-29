# CV Evaluation App using Oracle Gen AI

This is a Streamlit-based web application that evaluates resumes (CVs) against job descriptions using Oracle Cloud Infrastructure's Generative AI via Langchain `ChatOCIGenAI`.

---

## 🔍 Features

- Upload multiple resumes in PDF format
- Select or input a job description
- Evaluate resumes using Oracle Gen AI
- Receive classification like `Excellent`, `Strong`, `Possible`, etc.
- Get profile summaries, missing keywords, and improvement suggestions
- Interactive Streamlit interface

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

## 🧠 Powered By

- **Oracle Generative AI**: For advanced natural language processing and resume evaluation
- **LangChain**: For structured LLM integration
- **Streamlit**: For building a fast, interactive UI

---

## ✅ Example Use Case

1. Choose a job role or paste your custom Job Description.
2. Upload one or more resume PDFs.
3. Click **Submit**.
4. View evaluation results, summaries, and suggested improvements.
