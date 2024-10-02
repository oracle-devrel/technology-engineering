from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.readers.web import SitemapReader
from qdrant_client import QdrantClient
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.llms import VLLM, VLLMOpenAI


loader = SitemapReader(html_to_text=True)
# Reads pages from the web based on their sitemap.xml.
# Other data connectors available.

documents = loader.load_data(
    sitemap_url='https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/frpj5kvxryk1/b/thisIsThePlace/o/latest.xml'
)
# for document in documents:
#    print(document.metadata['Source'])

# local Docker-based instance of Qdrant
client = QdrantClient(
    location=":memory:"
)

embeddings = SentenceTransformerEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

# local instance of Mistral 7B v0.1 using vLLM inference server
# and FlashAttention backend for performance. Model is downloaded
# from HuggingFace (no accoutn needed).
llm = VLLM(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    gpu_memory_utilization=0.95,
    tensor_parallel_size=1, # inference distributed over X GPUs
    trust_remote_code=True, # mandatory for hf model
    max_new_tokens=128,
    top_k=10,
    top_p=0.95,
    temperature=0.8,
    vllm_kwargs={
        "swap_space": 1,
        "gpu_memory_utilization": 0.95,
        "max_model_len": 16384, # limitation due to unsufficient RAM
        "enforce_eager": True,
    },
)

system_prompt="As a support engineer, your role is to leverage the information \
    in the context provided. Your task is to respond to queries based strictly \
    on the information available in the provided context. Do not create new \
    information under any circumstances. Refrain from repeating yourself. \
    Extract your response solely from the context mentioned above. \
    If the context does not contain relevant information for the question, \
    respond with 'How can I assist you with questions related to the document?"

Settings.llm = llm
Settings.embed_model = embeddings
Settings.chunk_size=1000
Settings.chunk_overlap=100
Settings.num_output = 256
Settings.system_prompt=system_prompt

vector_store = QdrantVectorStore(
    client=client,
    collection_name="ansh"
)

storage_context = StorageContext.from_defaults(
    vector_store=vector_store
)

index = VectorStoreIndex.from_documents(
    documents,
    storage_context=storage_context
)

query_engine = index.as_query_engine(llm=llm)

response = query_engine.query(
    'What are the document formats supported by the Vision service?'
)

print("Response: ", response.response.strip())
for key in response.metadata.keys():
    print("Source: ", response.metadata[key]['Source'])