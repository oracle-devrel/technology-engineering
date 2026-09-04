"""
To test Embeddings from NVIDIA NIMS
"""

import numpy as np
from custom_rest_embeddings import CustomRESTEmbeddings

#
# Main
#
API_URL = "http://150.230.157.213:8000/v1/embeddings"
MODEL_ID = "baai/bge-m3"
DIMENSIONS = 1024

embed_model = CustomRESTEmbeddings(
    api_url=API_URL, model=MODEL_ID, dimensions=DIMENSIONS
)

QUERY = "Who is Larry Ellison?"

# if embedding chunk use embed_document, if query, embed_query
vec = embed_model.embed_documents([QUERY])

print("Vector is: ", vec)
print("Dimension is: ", np.array(vec).shape)
