# Image segmentation with OCI AI Vision and SAM2 from Meta
In this demo, you will see how you can segment objects in images by combining **OCI AI Vision** with **Meta’s SAM2 (Segment Anything Model 2)**.

**Segmenting objects in images has never been this easy!**
You can combine both OCI AI Vision to handle image analysis and SAM2 to provide high-precision segmentation, you can quickly identify and isolate objects in any image using just a few clicks or simple prompts. This integration demonstrates how cloud-based vision services and cutting-edge AI models can work together to streamline complex computer vision tasks.

For more accurate results, you can build a custom object detection model in OCI AI Vision (see [the documentation](https://docs.oracle.com/en-us/iaas/Content/vision/using/custom_image_analysis_models_using.htm) for more details).

## Some possible business cases
- Compute areas of roofs to detect the area available for solar panels.
- Segment construction sites to estimate areas from aerial images.
- Environmental monitoring: segment different land types (forest, water, urban areas,...) from satellite imagery and estimate changes in those areas.
- Urban planning: segment and detect roads, bridges, and utilities for urban development projects.
- Crop and weed segmentation to optimize pesticide usage and crop management.

## Requirements
You can install the following demo in a personal PC. 
You would need some space and at least a CPU with 300MB of memory, for `sam2.1-hiera-small`.

## Setup
1. Install Python (this project requires Python 3.13.5 or later). You can check your current Python version by running:
</br>
```
python --version
```
or
```
python3 --version
```
2. Install the requirements from `requirements.txt` file.
</br>
```
pip install -r /path/to/requirements.txt
```
3. Update the `.config` file with your own `CONFIG_FILE_PATH` and `COMPARTMENT_ID`:
```
CONFIG_FILE_PATH = <path_to_oci_login_config_file>
COMPARTMENT_ID = <compartment_OCID>
# Change the endpoint to match your account's region
ENDPOINT = "https://inference.generativeai.eu-frankfurt-1.oci.oraclecloud.com" 
```
4. Run the application using `streamlit run app.py`.

## Technical Details
* The solution leverages Oracle Cloud Infrastructure (OCI) AI Vision Service, an AI service designed to simplify AI adoption.
* Specifically, this demo utilizes:
	+ OCI Vision object detection
    + SAM2 segmentation

### About SAM2
SAM2 is an open-source model developed by Meta AI as the next-generation version of the original Segment Anything Model (SAM). It enables fast and flexible image segmentation, allowing users to easily extract precise object masks from images with minimal input. Built to support both interactive and automated segmentation tasks, SAM2 improves on efficiency, accuracy, and generalization across diverse image types and domains.

Key features include:
- State-of-the-art segmentation performance
- Support for promptable segmentation (points, boxes, masks)
- Open-source and ready for integration into custom workflows

You can find more information [here](https://docs.ultralytics.com/models/sam-2/).
And you can find information about the License [here](https://github.com/facebookresearch/sam2/blob/main/LICENSE).

## Project Structure
The repository is organized as follows:

```plaintext
│   .config                 # File to be added as explained in `Setup`, with your own OCI variables
│   app.py                  # Main Streamlit application entry point
│   config.py               # Variables for the Streamlit application
│   navigation.py           # Configuration for the sidebar in the Streamlit application
│   README.md               # Project documentation
│   requirements.txt        # Python dependencies
│
├───utils
│   │   ai_tools.py         # Wrappers for inference on the AI models
│   │   image_utils.py      # Wrappers for image functionalities
│
├───app_images
│   │   oracle_logo.png     # Logo of Oracle for Streamlit application
│
├───.streamlit              # Parameters for UI appearance of the Streamlit application
│
└───uploaded_images         # Folder to be used by the Streamlit application
```

## Output
The demo will display an interactive dashboard to upload an image and process it, displaying the resulting detections from OCI Vision and segmentations of those detections.

## Authors
- Matthias Wolf
- Cristina Granés

## Contributing
We welcome contributions to improve and expand the capabilities of this demo. Please fork the repository and submit a pull request with your changes.

## License
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](../LICENSE) for more details.
