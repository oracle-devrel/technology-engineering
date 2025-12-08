# OCI Vision Streaming — Setup & Stream Consumption Guide

##  Overview
This demo includes two main components:

- **stream-job.py** — Python script for creating and managing OCI Vision stream jobs  
- **Stream-analysis.py** — Streamlit app for consuming and visualizing the stream outputs  

---

##  1. Region Availability
OCI Vision Streaming is available only in supported regions.

 **Check regional availability:**  
https://docs.oracle.com/en-us/iaas/Content/vision/using/video-stream-processing-top.htm

---

##  2. Prerequisites

Before you start, ensure you have:

- An active **RTSP stream URL** (IP camera or RTSP source)  
- A configured **OCI Subnet**  
- Proper IAM permissions for:
  - Vision  
  - Stream Jobs  
  - Object Storage  
- An Object Storage bucket + namespace  
- A local Python environment with required libraries  

---

Install required dependencies:

- pip install -r requirements.txt

##  3. Setting Up a Vision Stream Job

### **Step 1 — Run the script**

python stream-job.py
--compartment-id <OCID>
--subnet-id <OCID>
--camera-url rtsp://...

--namespace <namespace>
--bucket <bucket>
--prefix <prefix-optional>

### **Step 2 — Parameter Definitions**

| Argument | Description |
|---------|-------------|
| `--compartment-id` | Your compartment OCID |
| `--subnet-id` | Subnet OCID used for the Vision Private Endpoint |
| `--camera-url` | RTSP URL of your streaming source |
| `--namespace` | Object Storage namespace |
| `--bucket` | Target Object Storage bucket |
| `--prefix` | Optional intermediate path inside the bucket |

---

##  4. Understanding the Stream Job Steps

The script automatically performs the following actions (in order):

1. **create_private_endpoint**  
   - Creates a Vision Private Endpoint inside the subnet  
   - Required for sending frames from your RTSP stream to OCI Vision  

2. **create_stream_source, create_stream_job, create_stream_group**  
   - Defines detection features (object / face detection)  
   - Creates the streaming job  

3. **start_stream_job**  
   - Starts transmitting frames (max 2 FPS)  
   - Outputs JSON detection results into the specified bucket  

>  *If you want the job to keep running, comment out the stop_stream_job call in the script.*

###  Notes

- Each subnet can contain **only one** Vision Private Endpoint  
- Streaming continues indefinitely unless explicitly stopped  
- Buckets may grow rapidly — remember to clean up  
- You can list active stream jobs via OCI APIs for more control  

---

##  5. Consuming Streams with Streamlit


Run the Streamlit app:

- streamlit run Stream-analysis.py

In the Streamlit UI, enter:

- Stream Job OCID  
- Bucket name  
- Prefix  
- Namespace  
- Detection type (**Object Detection** or **Face Detection**)  

Click **Consume Stream** to view annotated video frames.

> OCI Vision Streaming outputs ~2 FPS by design.

---

##  6. Resource Management (IMPORTANT)

- Always **stop the Stream Job** when you're done.  
- Delete resources using the provided cleanup cells in the notebook.  
- You may store OCIDs to reuse the same resources without recreating them.  

---

##  7. Troubleshooting

**405 – Request Not Allowed**

- Occurs when the stream job is transitioning between states  
- If stuck in `UPDATING`, delete the job and recreate it  

---

##  8. References

- OCI Vision Streaming Docs  
  https://docs.oracle.com/en-us/iaas/Content/vision/using/video-stream-processing-top.htm

- OCI Python SDK Reference  
  https://docs.oracle.com/en-us/iaas/tools/python/2.162.0/api/landing.html  

---

##  9. License
Copyright (c) 2025 Oracle and/or its affiliates.  
Licensed under UPL 1.0.  
See *LICENSE* file for details.