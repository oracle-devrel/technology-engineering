# 🖼️ Image Embedding & Search — OCI GenAI

A Gradio-based web application that demonstrates **image embedding and similarity search** using **Oracle Generative AI** embeddings. This tool allows you to upload images, create vector embeddings, and perform semantic searches using text queries or image-to-image similarity.

**Author:** Ilayda Ece Temir

**Reviewed date:** 17.02.2026

---

# When to use this asset?
## 🔧 Features

### Image Embedding with OCI GenAI
- Upload multiple images and create vector embeddings using Cohere embedding models
- Support for various image formats (JPG, PNG, etc.)
- Batch processing to handle large image collections efficiently
- In-memory vector storage using ChromaDB for fast retrieval

### Text-to-Image Search
- Search your image collection using natural language queries
- Semantic understanding powered by OCI Generative AI embeddings
- Returns ranked results with similarity scores
- Find images by describing visual concepts, objects, or scenes

### Image-to-Image Similarity Search
- Upload a reference image to find visually similar images
- Advanced image-to-image similarity using vector embeddings
- Perfect for finding duplicates, similar products, or visual patterns
- Confidence scoring for search results

### Interactive Web Interface
- Modern Gradio UI with tabbed interface
- Real-time progress indicators and status updates
- Image gallery for browsing your embedded collection
- Pagination support for large image databases

---

## 👥 Who Can Use This

**Data Scientists & ML Engineers**
→ Experiment with multimodal embeddings and vector search workflows.

**Content Creators & Digital Asset Managers**
→ Organize and search through large image collections efficiently.

**Developers & AI Researchers**
→ Build prototypes for image retrieval systems using OCI GenAI embeddings.

**E-commerce & Retail Teams**
→ Implement visual product search capabilities.

---

## 🗂️ Files & Structure

```
.
├── main.py              # Main Gradio application
├── config.py            # OCI configuration & model settings
├── requirements.txt     # Python dependencies
└── README.md           # This documentation
```

---

# How to use this asset?
## ⚙️ Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/oracle-devrel/technology-engineering.git
cd technology-engineering/ai/generative-ai-service/image-embed-and-search
```

### 2. Configure OCI Credentials
Edit your `config.py` file with your OCI details:

```python
# config.py
COMPARTMENT_ID = "ocid1.compartment.oc1..your-compartment-id"
ENDPOINT = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
EMBEDDING_MODEL = "cohere.embed-v4.0"
```

Ensure your OCI credentials file (`~/.oci/config`) is correctly configured with API keys and region.

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

---

## 🚀 Run the App
```bash
python main.py
```

The application will launch in your browser at `http://localhost:7860`.

---

## 📝 Get it running

### 1. **Load & Embed Images**
   → Upload multiple images using the file picker
   → Select your preferred embedding model (Cohere v4.0, English Image v3.0, etc.)
   → Click "Upload & Embed Images" to process them in batches
   → Monitor progress in the status area

### 2. **Search by Text**
   → Enter descriptive text like "red sports car" or "mountain landscape"
   → Select embedding model and click "Search by Text"
   → View the top matching image with confidence score

### 3. **Search by Image**
   → Upload a reference image
   → Click "Search by Image" to find visually similar images
   → Results show similarity rankings

### 4. **Browse Collection**
   → Navigate through all embedded images with pagination
   → View thumbnails in a gallery format
   → Check total image count and current page status

---

## 🛠️ Customization

- **Embedding Models**: Switch between different Cohere models in `config.py`:
  - `cohere.embed-v4.0` - General purpose embeddings
  - `cohere.embed-english-image-v3.0` - Optimized for image-text tasks
  - `cohere.embed-english-light-image-v3.0` - Lightweight version

- **Vector Storage**: The current implementation uses in-memory ChromaDB. For persistence, modify `main.py` to use disk-based storage.

- **Batch Processing**: Adjust batch size in `process_uploaded_images()` function for optimal API performance.

- **UI Customization**: Modify the Gradio interface in `main.py` to add features like export capabilities or advanced filtering.

---

## 🧠 Example Interactions

**Text Search:**
- Query: *"golden retriever playing in park"*
- Result: Top match shows image of dog with 0.87 confidence score

**Image Search:**
- Upload: Photo of a red bicycle
- Result: Returns similar bicycle images ranked by visual similarity

---

## 🔧 OCI Services Used

1. **OCI Generative AI – Cohere Embeddings**
   → Multimodal text and image embedding models
   ```python
   from langchain_community.embeddings import OCIGenAIEmbeddings
   ```

2. **OCI Identity and Access Management**
   → Authentication and compartment access

---

# Docs & References

📘 [OCI Generative AI Overview](https://docs.oracle.com/en-us/iaas/Content/generative-ai/home.htm)

📘 [Cohere Embedding Models](https://docs.oracle.com/en-us/iaas/api/#/en/generative-ai/20231130/datatypes/EmbedTextDetails)

📘 [LangChain OCI Integration](https://python.langchain.com/docs/integrations/providers/oci/)

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.