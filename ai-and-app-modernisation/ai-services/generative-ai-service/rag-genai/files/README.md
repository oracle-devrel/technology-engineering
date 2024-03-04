# Creating a RAG (Retrieval-Augmented Generation) with Oracle Generative AI Service in just 21 lines of code

## Introduction
In this article, we'll explore how to create a Retrieval-Augmented Generation (RAG) model using Oracle Gen AI, llama index, Qdrant Vector Database, and SentenceTransformerEmbeddings. This 21-line code will allow you to scrape through web pages, use llama index for indexing, Oracle Generative AI Service for question generation, and Qdrant for vector indexing.

Find below the code of building a RAG using llamaIndex with Oracle Generative AI Service.
Also check the file LangChainRAG.py which allows you to create an application (implementing RAG) using Langchain and the file langChainRagWithUI.py which includes a UI build with Streamlit.

<img src="./RagArchitecture.svg">
</img>

<!-- ## Limited Availability

Oracle Generative AI Service is in Limited Availability as of today when we are creating this repo.

Customers can easily enter in the LA programs. To test these functionalities you need to enrol in the LA programs and install the proper versions of software libraries.

Code and functionalities can change, as a result of changes and new features -->

## Prerequisites

Before getting started, make sure you have the following installed:

- Oracle Generative AI Service
- llama index
- langchain
- qdrant client
- SentenceTransformerEmbeddings

## Setting up the Environment
1. Install the required packages:
   ```bash
   pip install -U langchain oci
   pip install langchain llama-index qdrant-client sentence-transformers transformers
   ```

## Loading data

You need to create a sitemap.xml file where you can specify or list the webpages which you want to include in your RAG. 
Here we have used SentenceTransformerEmbeddings to create the embeddings but you can easily use any embeddings model . In the next blog we will show how easily you can use Oracle Generative AI Service embeddings model.

In this example we have used some Oracle documentation pages and created a xml file for the same and have placed it in Oracle object storage. 

sitemap used : https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frpj5kvxryk1/b/thisIsThePlace/o/combined.xml

## Entire code

   ```bash
from llama_index import VectorStoreIndex
from llama_index import ServiceContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.storage.storage_context import StorageContext
from qdrant_client import qdrant_client
from langchain_community.embeddings import SentenceTransformerEmbeddings
from llama_hub.web.sitemap import SitemapReader
from langchain_community.llms import OCIGenAI
loader = SitemapReader()
documents = loader.load_data(sitemap_url='https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frpj5kvxryk1/b/thisIsThePlace/o/latest.xml')
client = qdrant_client.QdrantClient(location=":memory:")
embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
llm = OCIGenAI(model_id="cohere.command",service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",model_kwargs={"temperature": 0.0, "max_tokens": 300},compartment_id = "ocid1.compartment.oc1..aaaaaaaa7ggqkd4ptkeb7ugk6ipsl3gqjofhkr6yacluwj4fitf2ufrdm65q")
system_prompt="As a support engineer, your role is to leverage the information in the context provided. Your task is to respond to queries based strictly on the information available in the provided context. Do not create new information under any circumstances. Refrain from repeating yourself. Extract your response solely from the context mentioned above. If the context does not contain relevant information for the question, respond with 'How can I assist you with questions related to the document?"
service_context = ServiceContext.from_defaults(llm=llm, chunk_size=1000, chunk_overlap=100, embed_model=embeddings,system_prompt=system_prompt)
vector_store = QdrantVectorStore(client=client, collection_name="ansh")
storage_context = StorageContext.from_defaults(vector_store=vector_store)
index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, service_context=service_context)
query_engine = index.as_query_engine()
response = query_engine.query('What is activity auditing report?')
print(response)
   ```



## Conclusion

In this article, we've covered the process of creating a RAG model using Oracle Generative AI Service, llama index, Qdrant, and SentenceTransformerEmbeddings. Feel free to experiment with different web pages and datasets to enhance the capabilities of your model.

In a future blog post, we'll explore how to integrate Oracle Vector Database and Oracle Gen AI embeddings model into this RAG setup.

Feel free to modify and expand upon this template according to your specific use case and preferences. Good luck with your article!
