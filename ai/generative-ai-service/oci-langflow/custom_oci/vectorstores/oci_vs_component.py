"""
Custom integration with Langflow and OCI Vector Store

Author: L. Saetta (Oracle)

"""

import oracledb
from langchain_community.vectorstores.oraclevs import OracleVS
from langchain_community.vectorstores.utils import DistanceStrategy

from langflow.base.vectorstores.model import (
    LCVectorStoreComponent,
    check_cached_vector_store,
)
from langflow.helpers.data import docs_to_data
from langflow.io import (
    HandleInput,
    IntInput,
    StrInput,
    SecretStrInput,
    MessageTextInput,
)
from langflow.schema import Data


class OCIVectorStoreComponent(LCVectorStoreComponent):
    """
    Wrapper for the OCI Vector Store
    """

    display_name = "OCIVectorStore"
    description = "OCI Vector Store based on 23AI"
    name = "ocivector"

    inputs = [
        SecretStrInput(name="db_user", required=True),
        SecretStrInput(name="db_pwd", required=True),
        SecretStrInput(name="dsn", required=True),
        SecretStrInput(name="wallet_dir", required=True),
        SecretStrInput(name="wallet_pwd", required=True),
        StrInput(name="collection_name", display_name="Table", required=True),
        # this way we can handle the input for the search and it can be connected
        # in the flow
        MessageTextInput(
            name="search_query",
            display_name="search_query",
            info="Enter the search query.",
        ),
        *LCVectorStoreComponent.inputs,
        HandleInput(
            name="embedding", display_name="Embedding", input_types=["Embeddings"]
        ),
        IntInput(
            name="number_of_results",
            display_name="Number of Results",
            info="Number of results to return.",
            value=4,
            advanced=True,
        ),
    ]

    def handle_credentials(self) -> dict:
        """
        this function organizes the parameters to connect
        to DB
        """
        _connect_args_vector = {
            "user": self.db_user,
            "password": self.db_pwd,
            "dsn": self.dsn,
            "config_dir": self.wallet_dir,
            "wallet_location": self.wallet_dir,
            "wallet_password": self.wallet_pwd,
        }
        return _connect_args_vector

    @check_cached_vector_store
    def build_vector_store(self) -> OracleVS:
        connect_args_vector = self.handle_credentials()

        conn = oracledb.connect(**connect_args_vector)

        v_store = OracleVS(
            client=conn,
            table_name=self.collection_name,
            distance_strategy=DistanceStrategy.COSINE,
            embedding_function=self.embedding,
        )
        return v_store

    def search_documents(self) -> list[Data]:
        """
        no changes needed here
        """
        vector_store = self.build_vector_store()

        if (
            self.search_query
            and isinstance(self.search_query, str)
            and self.search_query.strip()
        ):
            docs = vector_store.similarity_search(
                query=self.search_query,
                k=self.number_of_results,
            )

            data = docs_to_data(docs)
            self.status = data
            return data
        return []
