# Describe an image using OCI AI Vision Service and OCI Generative AI Service

# Introduction
In this article, we'll explore how to describe an image using OCI AI Vision Service and OCI Generative AI Service.
The application is developed using Oracle VBCS, OIC, OCI AI Vision service, and OCI Generative AI Service.
This integrated approach combines the strength of OCI AI Vision and OCI Generative AI Service, allowing for efficient and insightful summarization of image content.


<img src="./files/AIVisionApp.jpg"></img>


# Prerequisites

Before getting started, make sure you have access to these services:

- Oracle Generative AI Service
- Oracle Vision Service
- Oracle Visual Builder Cloud Service
- Oracle Integration Cloud

# AI Vision and OCI Generative AI Service Integration Architecture

1. AI Vision App using VBCS
- Oracle Visual Builder Cloud Service (VBCS) is a hosted environment for your application development infrastructure. It provides an open-source standards-based development service to create, collaborate on, and deploy applications within Oracle Cloud. This application is developed in VBCS.

2. Image Analysis with OCI AI Vision Service:
- The AI Vision service is employed to analyze images.
- It identifies objects within the image by using advanced computer vision algorithms.

3. Integration with OCI Generative AI Service:
- The extracted object keywords are sent to the OCI Generative AI Service

4. Integration with OCI AI Vision and OCI Generative AI Service using OIC:
- Oracle Integration Cloud integrates the VBCS app and OCI AI Services.

5. Summarization Process:
- OCI Generative AI Service generates text using the keywords received from OCI Vision service, to create a concise summary of the image.

<img src="./files/AIVisionAppArch.svg"></img>

# Application Flow in Detail (VBCS, OIC, OCI Vision, OCI Generative AI Service)

In this application,
-	The File Picker action in VBCS allows the user to select the image. 
-	Create an integration process in Oracle Integration Cloud (OIC) to handle the communication between   VBCS and OCI Vision Service.
-	Pass the selected image from VBCS to OCI Vision Service to analyze the image.
-	OCI Vision Service analyzes the image and identifies objects within it.
-	The OCI Vision Service returns the detected objects (keywords) to the OIC integration process and returns the results to VBCS.

         User (VBCS) --> (File Picker) --> |Image| --> (OIC) --> |OCI Vision Service| --> |Detected Objects| --> (OIC) --> |Result| --> (VBCS)

   <img src="./files/VBCS_Vision.jpg">
      </img>

      OIC call - Invoke OCI Vision Service
      Endpoint - /actions/analyzeImage

   <img src="./files/OIC_VisionService.jpg">
      </img>

-	User clicks the "Generate" button in the app to initiate the summary generation.
-	Configure the OIC integration process to invoke the GenAI service.
-	Pass the keywords returned by the OCI Vision Service along with any additional relevant information.
-	Generative AI Service processes the received keywords and generates a summary of the image content.

         User (VBCS) --> (File Picker) --> |Image| --> (OIC) --> |OCI Vision Service| --> |Detected Keywords| --> (OIC) --> | OCI Generative AI Service  --> |Summary| --> (OIC) --> |Result| --> (VBCS)

   <img src="./files/VBCS_GenerateSummary.jpg">
      </img>

      OIC call - Invoke OCI Generative AI Service
      Endpoint - /20231130/actions/generatText
   <img src="./files/OIC_GenerateSummary.jpg">
      </img>

# Code
      VBCS app -  ImageClassification-1.0.zip
      OIC Vision Integration - RESTVISION_01.00.0000.iar
      OIC Generate Summary - IMAGEDESCRIPTIONGENERATION_01.00.0000.iar

# Conclusion

In this article, we've covered how to utilize Oracle AI Vision Service features to provide a summary of an image using Generative AI service.  
Feel free to modify and expand upon this template according to your specific use case and preferences.

# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
	
