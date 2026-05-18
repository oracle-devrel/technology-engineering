"""
Custom integration with Langflow and OCI Embeddings Model

Author: L. Saetta (Oracle)

"""

from langchain_community.embeddings import OCIGenAIEmbeddings

from langflow.base.models.model import LCModelComponent
from langflow.io import DropdownInput, StrInput, Output, SecretStrInput
from langflow.field_typing import Embeddings

class OCIEmbeddingsComponent(LCModelComponent):
    """
    This class integrates the OCI Embeddings Model with Langflow.

    Notes:
        * Security: for now API_KEY, set your key-pair in $HOME/.oci

    """

    display_name = "OCI Cohere Embeddings"
    description = "Generate Embeddings using OCI Cohere models."

    inputs = [
        # example of dropdown
        DropdownInput(
            name="auth_type",
            display_name="auth_type",
            info="The type of auth_type to use for the chat model",
            advanced=True,
            options=[
                "API_KEY",
                "RESOURCE_PRINCIPAL",
            ],
            value="API_KEY",
        ),
        DropdownInput(
            name="model",
            display_name="Model",
            advanced=True,
            options=[
                "cohere.embed-english-v3.0",
                "cohere.embed-multilingual-v3.0",
            ],
            value="cohere.embed-english-v3.0",
        ),
        StrInput(
            name="service_endpoint",
            display_name="Service Endpoint",
            info="OCI Service Endpoint URL",
            required=True,
        ),
        SecretStrInput(
            name="compartment_id",
            display_name="Compartment ID",
            info="OCI Compartment OCID",
        ),
    ]

    outputs = [
        Output(display_name="Embeddings", name="embeddings", method="build_embeddings"),
    ]

    def build_model(self) -> Embeddings:
        """
        build the embeddings model
        """
        return self.build_embeddings()

    def build_embeddings(self) -> Embeddings:
        """
        build the embeddings model
        """
        # default truncate strategy is END
        return OCIGenAIEmbeddings(
            auth_type=self.auth_type,
            model_id=self.model,
            service_endpoint=self.service_endpoint,
            compartment_id=self.compartment_id,
        )
