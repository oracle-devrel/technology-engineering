import streamlit as st
import config
from PIL import Image

import torch
from sam2.sam2_image_predictor import SAM2ImagePredictor

from utils.image_utils import load_image, save_uploaded_image, draw_detections, draw_masks
from utils.ai_tools import InferencePipeline
from navigation import make_sidebar

@st.cache_resource
def load_sam():
    # This will require internet access when deploying the model
    # Alternative, larger model: "facebook/sam2.1-hiera-large"
    predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2.1-hiera-small", device=torch.device("cpu"))
    return predictor
    

def main():

    ## Page config
    icon = Image.open(config.ORACLE_LOGO)

    st.set_page_config(
        page_title="Detect and segment",
        page_icon=icon,
        layout="wide",
    )
    
    ## Header ##
    st.markdown("<h1 style='margin-bottom: 0;'>Segment Images with OCI AI Vision + SAM2 from Meta</h1>", unsafe_allow_html=True)
    st.divider()


    ### Init application ###

    sam_model = load_sam()
    ai_pipeline = InferencePipeline(config=config, sam_model=sam_model)
    
    # Sidebar for upload and run
    uploaded_file, run_button = make_sidebar()


    ######### finish init

    ## Upload image & process ##
    coli1, coli2 = st.columns([0.5, 0.5])
    if uploaded_file:
        image = load_image(uploaded_file)
        with coli1: st.image(image, caption="Original Image")

        if run_button:
            with st.spinner("Processing...", show_time=True):
                uploaded_file.seek(0)
                # Save image:
                image_path = save_uploaded_image(uploaded_file, save_dir=config.UPLOAD_PATH)

                #detections = ai_pipeline.get_detection(uploaded_file)
                detections, masks = ai_pipeline.get_detections_and_masks(image_path)

                image_with_boxes = draw_detections(image, detections)
                with coli2: st.image(image_with_boxes, caption="OCI Vision Detections")

                st.header("Final segmentations")
                
                ## Plot masks:
                mask_names = [msk["class"] for msk in masks]
                tabs_list = st.tabs(mask_names)
                for id_msk, msk in enumerate(masks):
                    ctab = tabs_list[id_msk]
                    det = detections[id_msk]
                    image_with_mask = draw_masks(image, msk["mask"])
                    with ctab: 
                        st.image(image_with_mask, 
                                 width=700,
                                 caption=f"{msk["class"]} - Detection confidence score: {det["confidence_score"]:.2f}")


if __name__ == '__main__':
    main()
