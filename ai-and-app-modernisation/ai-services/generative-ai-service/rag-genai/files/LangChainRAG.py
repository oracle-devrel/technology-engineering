from langchain_community.embeddings import OCIGenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from langchain_core.prompts import PromptTemplate
from langchain_community.llms import OCIGenAI
from langchain_community.document_loaders import UnstructuredURLLoader
compartment_id = "ocid1.compartment.oc1..aaaaaaaa7ggqkd4ptkeb7ugk6ipsl3gqjofhkr6yacluwj4fitf2ufrdm65q"
embeddings = OCIGenAIEmbeddings(model_id="cohere.embed-english-light-v3.0",service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",compartment_id= compartment_id,)
testurls = ['https://docs.oracle.com/iaas/odsaz/odsa-rotate-wallet.html', 'https://docs.oracle.com/iaas/odsaz/odsa-change-password.html', 'https://docs.oracle.com/iaas/odsaz/odsa-database-actions.html']
loader = UnstructuredURLLoader(urls=testurls)
docs = loader.load()
vectorstore = Qdrant.from_documents(docs,embeddings,location=":memory:",prefer_grpc=False,collection_name="test_db")
retriever = vectorstore.as_retriever()
rag_prompt_template = """Answer the question based only on the following context:
{context}
Question: {question}"""
rag_prompt = PromptTemplate.from_template(rag_prompt_template)
llm = OCIGenAI(model_id="cohere.command",service_endpoint="https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",compartment_id= compartment_id,model_kwargs={"temperature": 0, "max_tokens": 300})
rag = RetrievalQA.from_chain_type(llm=llm,retriever=retriever,chain_type_kwargs={"prompt": rag_prompt,},)
data = rag.invoke("What is rotate a wallet")
print(data['result'])