import asyncio
import base64
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_oci import ChatOCIGenAI
import logging
from PIL import Image
import streamlit as st

from oci_utils import get_tenancy_id, list_subscribed_regions, list_genai_models


# Supported by Grok
FILE_TYPES = ["jpg", "jpeg", "png"]
MULTIMODALS = [
    "meta.llama-3.2-90b-vision-instruct",
    "meta.llama-4-maverick-17b-128e-instruct-fp8",
    "xai.grok-4",
]
DEFAULT_LLM = "xai.grok-4"
DEFAULT_REGION = "us-chicago-1"


load_dotenv()


compartment_id = os.environ.get("COMPARTMENT_ID", get_tenancy_id())


def create_chain(ai_prompt: str, model_id: str, region_id: str):
    """Create a langchain from a text prompt.

    Expects the user to supply an image.
    """
    prompt = ChatPromptTemplate(
        [
            {
                "role": "system",
                "content": ai_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:{image_mime_type};base64,{image_data}"
                        },
                    },
                ],
            },
        ]
    )
    llm = ChatOCIGenAI(
        model_id=model_id,
        compartment_id=compartment_id,
        service_endpoint=f"https://inference.generativeai.{region_id}.oci.oraclecloud.com",
    )
    return prompt | llm


category_list = [
    "Transportation",
    "Transportation/Road/Car",
    "Transportation/Road/Van",
    "Transportation/Road/Lorry",
    "Furniture/Office",
    "Furniture/Office/Desk",
    "Furniture/Office/Chair",
    "Furniture/Home",
    "Furniture/Home/Chair",
    "Tools",
    "Tools/Electric",
    "Tools/Hydraulic",
]

property_template = """\
{
    "Brand": "",
    "Model": "",
    "Category": "",
    "Signed": false
}
"""


def create_chains(model_id, region_id):
    """Instantiate all LLM chains to be invoked."""
    with open("prompt_describe.txt") as fd:
        yield create_chain(fd.read(), model_id, region_id)

    with open("prompt_categorize.txt") as fd:
        yield create_chain(fd.read(), model_id, region_id)

    with open("prompt_properties.txt") as fd:
        yield create_chain(fd.read(), model_id, region_id)


async def invoke_chains(chains, upload, category_list, property_template):
    image_data = base64.b64encode(image_upload.getvalue()).decode("utf-8")
    image_type = image_upload.type
    results = await asyncio.gather(
        chains[0].ainvoke(
            {
                "image_data": image_data,
                "image_mime_type": image_type,
            }
        ),
        chains[1].ainvoke(
            {
                "image_data": image_data,
                "image_mime_type": image_type,
                "categories": category_list,
            }
        ),
        chains[2].ainvoke(
            {
                "image_data": image_data,
                "image_mime_type": image_type,
                "properties": property_template,
            }
        ),
    )
    return [r.content for r in results]


image_category = None
image_description = None
image_properties = None


with st.sidebar:
    st.header("Settings")

    regions = st.cache_data(list_subscribed_regions)()
    region_idx = 0
    if DEFAULT_REGION in regions:
        region_idx = regions.index(DEFAULT_REGION)
    region = st.selectbox("Region", regions, region_idx)
    logging.info("Selected region %s", region)

    models = sorted(
        set(st.cache_data(list_genai_models)(compartment_id, region))
        & set(MULTIMODALS)
    )
    model_idx = 0
    if DEFAULT_LLM in models:
        model_idx = models.index(DEFAULT_LLM)
    model = st.sidebar.selectbox("Model", models, model_idx)
    logging.info("Selected model %s", model)

    category_list = st.text_area(
        "Categories",
        value="\n".join(category_list),
        height=400,
    ).splitlines()
    property_template = st.text_area(
        "Property template",
        value=property_template,
        height=400,
    )

st.set_page_config(
    page_title="Describe and Classify",
    page_icon=Image.open("images/oracle_logo.png"),
    layout="wide",
)
st.logo(Image.open("images/oracle_logo.png"))
st.header("Describe and Classify")

col1, col2, col3 = st.columns(3)

with col1:
    image_upload = st.file_uploader("Choose an image…", type=FILE_TYPES)
    if image_upload:
        image = Image.open(image_upload)
        st.image(image, width="stretch")
        chains = list(create_chains(model, region))
        image_description, image_category, image_properties = asyncio.run(
            invoke_chains(
                chains,
                image_upload,
                category_list,
                property_template,
            )
        )

with col2:
    st.text_area("Description", value=image_description, height=200, disabled=True)
    st.text_area("Properties", value=image_properties, height=400, disabled=True)

with col3:
    try:
        idx = category_list.index(image_category)
    except ValueError:
        idx = None
    st.radio(
        "Category",
        category_list,
        index=idx,
        disabled=True,
    )
