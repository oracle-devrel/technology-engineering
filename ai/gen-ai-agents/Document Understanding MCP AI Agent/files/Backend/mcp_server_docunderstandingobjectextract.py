import os
import logging
from rich.logging import RichHandler
from rich.markup import escape

import oci
from oci.ai_document.models import (
    AnalyzeDocumentDetails,
    ObjectLocation,
    ObjectStorageDocumentDetails,
    DocumentTextExtractionFeature,
)

from mcp.server.fastmcp import FastMCP

# — Logging —
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)

# — MCP Setup —
os.environ["MCP_PORT"] = "8000"
mcp = FastMCP("Smart Toolbox")

@mcp.tool()
def ocr_extract_from_object_storage2(namespace: str, bucket: str, name: str) -> str:
    """
    Extract text from a document in Object Storage using Document Understanding.
    """
    try:
        cfg = oci.config.from_file()
        du_client = oci.ai_document.AIServiceDocumentClient(cfg)

        doc = ObjectStorageDocumentDetails(
            source="OBJECT_STORAGE",
            namespace_name=namespace,
            bucket_name=bucket,
            object_name=name
        )

        feats = [DocumentTextExtractionFeature(feature_type="TEXT_EXTRACTION")]

        details = AnalyzeDocumentDetails(
            compartment_id="ocid1.compartment.oc1..aaa",
            document=doc,
            features=feats
        )

        resp = du_client.analyze_document(analyze_document_details=details)

        text = "\n".join(
            line.text for page in resp.data.pages or [] for line in page.lines or []
        ).strip()

        logger.info(" Extracted %d characters from %s", len(text), name)
        return text or "No text found in document."

    except Exception as e:
        logger.exception(" Document extraction failed")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    print(" MCP server running at http://localhost:8000/mcp")
    mcp.run(transport="streamable-http")
