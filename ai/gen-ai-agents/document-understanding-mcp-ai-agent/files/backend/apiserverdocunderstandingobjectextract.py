# backend/apiserver.py
import logging
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from rich.logging import RichHandler
from rich.markup import escape

import oci
from mcp.client.session_group import StreamableHttpParameters
from oci.addons.adk import Agent, AgentClient
from oci.addons.adk.mcp import MCPClientStreamableHttp

# — Logging —
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)

# — FastAPI Setup —
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

BUCKET_NAME = "bucket-20250714-1419"

@app.on_event("startup")
async def startup_event():
    logger.info("Connecting to MCP…")
    mcp_params = StreamableHttpParameters(url="http://localhost:8000/mcp")
    mcp_client = await MCPClientStreamableHttp(params=mcp_params, name="Smart Toolbox MCP").__aenter__()

    client = AgentClient(auth_type="api_key", debug=False, region="us-chicago-1")
    agent = Agent(
        client=client,
        agent_endpoint_id="ocid1.genaiagentendpoint",
        instructions=(
"If the user wants to extract text from a document in Object Storage, "
"call the `ocr_extract_from_object_storage2` tool with the `namespace`, `bucket`, and `name`."

        ),
        tools=[await mcp_client.as_toolkit()],
    )
    agent.setup()
    app.state.agent = agent
    logger.info(" Agent ready.")

@app.post("/chat")
async def chat(message: str = Form(...), file: UploadFile = File(None)):
    if file:
        try:
            file_bytes = await file.read()
            file_name = file.filename

            config = oci.config.from_file()
            obj_client = oci.object_storage.ObjectStorageClient(config)
            namespace = obj_client.get_namespace().data

            # Upload file
            obj_client.put_object(namespace, BUCKET_NAME, file_name, file_bytes)
            logger.info(f" Uploaded {file_name} to {BUCKET_NAME}")

            # Inject the correct call instruction to the agent
            message = f"Extract text from object storage. Namespace: {namespace}, Bucket: {BUCKET_NAME}, Name: {file_name}"

        except Exception as e:
            logger.exception(" Upload failed")
            return JSONResponse({"error": f"Upload failed: {str(e)}"}, status_code=500)

    try:
        result = await app.state.agent.run_async(message)

        if isinstance(result.output, dict) and result.output.get("type") == "function":
            name = result.output["name"]
            args = result.output["parameters"]
            logger.info(" Agent calls tool: %s(%r)", name, args)

            tool_out = await app.state.agent.invoke_tool(name, args)
            followup = await app.state.agent.run_async({"type": "tool", "name": name, "output": tool_out})
            out = followup.output if not isinstance(followup.output, dict) else followup.output.get("text", "")
        else:
            out = result.output if not isinstance(result.output, dict) else result.output.get("text", "")

        logger.info(" Replying: %s", escape(out))
        return JSONResponse({"text": out})

    except Exception:
        logger.exception(" Chat error")
        return JSONResponse({"error": "internal error"}, status_code=500)
