"""
Custom class to support Embeddings model deployed using NVIDIA E.

License: MIT
"""

from typing import List
from langchain_core.embeddings import Embeddings
import requests
from utils import get_console_logger

# list of allowed values for dims, input_type and truncate parms
ALLOWED_DIMS = {384, 512, 768, 1024, 2048}
ALLOWED_INPUT_TYPES = {"passage", "query"}
ALLOWED_TRUNCATE_VALUES = {"NONE", "START", "END"}

# list of models with tunable dimensions
MATRIOSKA_MODELS = {"nvidia/llama-3.2-nv-embedqa-1b-v2"}

logger = get_console_logger()


class CustomRESTEmbeddings(Embeddings):
    """
    Custom class to wrap an embedding model with rest interface from NVIDIA NIM

    see:
        https://docs.api.nvidia.com/nim/reference/nvidia-llama-3_2-nv-embedqa-1b-v2-infer
    """

    def __init__(self, api_url: str, model: str, batch_size: int = 10, dimensions=2048):
        """
        Init

        as of now, no security
        args:
            api_url: the endpoint
            model: the model id string
            batch_size
            dimensions: dim of the embedding vector
        """
        self.api_url = api_url
        self.model = model
        self.batch_size = batch_size

        if self.model in MATRIOSKA_MODELS:
            self.dimensions = dimensions
        else:
            # changing dimensions is not supported
            self.dimensions = None

        # Validation at init time
        if self.dimensions is not None and self.dimensions not in ALLOWED_DIMS:
            raise ValueError(
                f"Invalid dimensions {self.dimensions!r}: must be one of {sorted(ALLOWED_DIMS)}"
            )

    def embed_documents(
        self,
        texts: List[str],
        # must be passage and not document
        input_type: str = "passage",
        truncate: str = "NONE",
    ) -> List[List[float]]:
        """
        Embed a list of documents using batching.
        """
        # normalize
        truncate = truncate.upper()

        logger.info("Calling NVIDIA embeddings, embed_documents...")

        if input_type not in ALLOWED_INPUT_TYPES:
            raise ValueError(
                f"Invalid value for input_types: must be one of {ALLOWED_INPUT_TYPES}"
            )
        if truncate not in ALLOWED_TRUNCATE_VALUES:
            raise ValueError(
                f"Invalid value for truncate: must be one of {ALLOWED_TRUNCATE_VALUES}"
            )

        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            # process a single batch
            if self.model in MATRIOSKA_MODELS:
                json_request = {
                    "model": self.model,
                    "input": batch,
                    "input_type": input_type,
                    "truncate": truncate,
                    "dimensions": self.dimensions,
                }
            else:
                json_request = {
                    "model": self.model,
                    "input": batch,
                    "input_type": input_type,
                    "truncate": truncate,
                    "dimensions": self.dimensions,
                }

            resp = requests.post(
                self.api_url,
                json=json_request,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json().get("data", [])

            if len(data) != len(batch):
                raise ValueError(f"Expected {len(batch)} embeddings, got {len(data)}")
            all_embeddings.extend(item["embedding"] for item in data)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """
        Embed the query (a str)
        """
        logger.info("Calling NVIDIA embeddings, embed_query...")

        return self.embed_documents([text], input_type="query")[0]
