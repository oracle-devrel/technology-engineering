# OCI Vision Streaming Setup and Consumption

## Quick Start Guide

- The code files in this demo are 
  - stream-job.py - Python script to start a stream job.
  - Stream-analysis.py - Streamlit application that can be used to consume the generated outputs of stream video analysis

## 1. Region Selection

OCI Vision Streaming is available in multiple regions.

- **[follow these steps](https://docs.oracle.com/en-us/iaas/Content/vision/using/video-stream-processing-top.htm)**.

---

## 2. Prerequisites

- **An active RTSP stream URL** (e.g., from an IP camera or RTSP streaming source)
- An Active OCI subnet configured according to the steps mentioned in the previous link.
- Required permissions in your OCI compartment to use Vision, Stream Jobs, and Object Storage buckets

---

## 3. Setting up the Vision Streaming Job

1. **Run the stream-job.py script**

2. **Pass the required parameters when running the script**

    - `subnet_id` &mdash; ID of the subnet you created (e.g., 'ocid1.subnet.oc1.phx.......')
    - `compartment_id` &mdash; your OCI compartment's OCID
    - `camera-url` &mdash; your RTSP stream URL
    - `namespace` &mdash; your Object Storage namespace
    - `bucket` &mdash; target Object Storage bucket
    - `prefix` &mdash; (Optional) Prefix for output files in Object Storage

3. **The following commands will run in order, if you want to keep the stream job running**
    - create_private_endpoint - creates a private endpoint inside the subnet to stream the frames to 
    - create_stream_source, create_stream_job, create_stream_group - define the features (object/face detection/tracking) and create the stream.
    - start_stream_job - this function begins streaming of frames from your rtsp url to OCI vision through the private endpoint and updates the bucket defined in real time with json files containing the embeddings of the images and the bounding boxes of the detected objects.
     _This will start streaming frames from your camera to OCI Vision for detection (e.g., face or object recognition). The results (bounding box coordinates, frame encodings, etc.) will be stored as JSON files in the specified Object Storage bucket._
    - Comment out the other function calls in case you want to keep the stream job running - the way the code is setup - it will automatically call the stop_stream_job function after a 60 second timeout
    
    *** ps:
    - each subnet can only have one private endpoint, if you try to generate another private endpoint within the same subnet you will get an error
    - the streaming will keep running as long as you did not shutdown the stream or the stream job - bucket storage can expand greatly if not managed properly.
    - Refer to the documentation for the API Specs where you can list the active stream jobs in a subnet and have more control over them.

   

---

## 4. Consuming Streams with Streamlit

  Install the required dependencies by running 
    
      pip install -r requirements.txt
    

While the stream job is active:

1. **Start the Streamlit app (in terminal):**
   ```bash
   streamlit run streamlit_app.py 
2. In the Streamlit UI, enter the following:
    - Stream Job OCID
    - Bucket Name
    - Prefix (Object Storage path, if applicable)
    - Object Storage Namespace
    - Detection Type: choose between "Object Detection" or "Face Detection"
3. Click on Consume Stream The video with detected objects/faces will appear in your browser as annotated frames.
Note: Frames may appear slow; OCI Vision Streaming currently supports a maximum of 2 frames per second.
- Depending on whether you selected object detection or face detection in the features during the creation of the stream job, select the appropriate radio button to get the relevant analytics.
![UI Screenshot](./media/appUI.png)

 
## 5. Resource Management — Important!
Stop the Stream Job when finished!
Leaving it running will keep streaming data into your bucket, leading to large storage consumption.
Clean up resources:
Use the notebook cells to delete the Stream Job and Stream Source.
Optionally, store the OCIDs of created resources and reuse them to avoid recreating each time.
 

## 6. References
- [OCI Vision Stream Analysis Documentation](https://docs.oracle.com/en-us/iaas/Content/vision/using/video-stream-processing-top.htm)  
- [OCI Python SDK API Reference](https://docs.oracle.com/en-us/iaas/tools/python/2.162.0/api/landing.html)
 
## 7. Troubleshooting
**Common Errors: 
If you encounter a 405 – Request Not Allowed error while running the stream job, it may be because the job is currently transitioning between states (for example, from CREATED to RUNNING). During this UPDATING phase, the job is temporarily locked, and you won’t be able to perform any actions on it. If it remains stuck in this state, try deleting the stream job and creating a new one.

## 8. License
Copyright (c) 2025 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](LICENSE) for more details.
