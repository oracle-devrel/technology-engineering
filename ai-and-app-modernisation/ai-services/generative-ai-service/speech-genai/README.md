# Simplify Transcriptions with OCI Generative AI and OCI Speech

## Introduction

If you’ve ever needed to take an audio recording, transcribe it, and summarize what was said, you know how many steps that can take while juggling several files. Let’s use AI to more efficiently solve the problem.
With Oracle Cloud Infrastructure (OCI) Speech and OCI Generative AI, we can automate audio-to-text conversion and build a concise summary all at once. This could, for example, be applied to a call center that handles thousands of calls, using a summary of the call transcripts to draw insights for improving customer experience.
OCI Speech is an AI service that uses automatic speech recognition technology to transform audio-based content into text. OCI Generative AI analyzes this text and can generate, summarize, transform, and extract information from it. You could even take the next step to use these AI capabilities to build a low-code application with Oracle Visual Builder.
Try this project to invoke the OCI Speech REST API, convert audio files into text, and invoke the Generative AI REST API to summarize it.

![Simplify Transcriptions with OCI Generative AI and OCI Speech](files/AISpeechGenAISummary.png)

## Prerequisites

1. Oracle Cloud account—[sign-up page](https://signup.cloud.oracle.com/)
2. Visual Builder—[Documentation](https://docs.oracle.com/en/cloud/paas/app-builder-cloud/index.html)
3. OCI Speech—[Documentation](https://docs.oracle.com/en-us/iaas/Content/speech/using/speech.htm#overview)
4. Integration workflow—[Oracle Integration 3](https://docs.oracle.com/en-us/iaas/application-integration/index.html)
5. OCI Generative AI—[Python SDK](https://pypi.org/project/oci/)

## Getting started

1. AI Speech App using VBCS:  
Oracle Visual Builder Cloud Service (VBCS) is a hosted environment for your application development infrastructure. It provides an open-source standards-based development service to create, collaborate on, and deploy applications within Oracle Cloud. This application is developed in VBCS.
2. Transcriptions with OCI AI Speech Service:  
Speech harnesses the power of spoken language enabling you to easily convert media files containing human speech into highly exact text transcriptions.
Produces accurate and easy-to-use JSON and SubRip Subtitle (SRT) files written directly to the Object Storage bucket you choose.
3. Integration with OCI Generative AI Service:
The transcriptions (text) are sent to the OCI Generative AI Service for text summarization.
4. Integration with OCI AI Vision and OCI Generative AI Service using Visual Builder Service Endpoint:
Build a Service Connection Endpoint option is used to integrate the VBCS app and OCI Object Storage, OCI AI Speech Service, and Generative AI Summarization.
5. Summarization Process:
OCI Generative AI Service generates text using the keywords received from OCI Speech service, to create a concise summary of the audio or video.

![Application Architecture](files/AISpeechSummaryAppArch.svg)

### Application Flow in Detail (VBCS, OCI Speech, OCI Generative AI Service)

In this application, the drag-and-drop component in VBCS allows the user to drop the audio or video.

- Create a Service Endpoint connection in Visual Builder to handle the communication between Visual Builder and OCI Speech Service.
- Pass the selected audio or video from Visual Builder to OCI Speech Service to convert it into text.
- OCI Speech Service analyzes the media (audio or video) file and converts it into text.
- The OCI Speech Service returns the transcription to the AI Speech Service Endpoint and returns the results to the Visual Builder app.
- The transcription further passes to the Generative AI Service Endpoint and returns the Summarization results to the Visual Builder app.

User (Visual Builder) --> (Drag and Drop File) --> |Media File (adudio or video) --> (Service Endpoint) --> |OCI Speech Service| --> |Speech to Text| --> (Service Endpoint) --> |Result| --> (Visual Builder) --> (Gen AI Service Endpoint) --> |Result| --> (Visual Builder) 

![OCI Speech Engine](files/AISpeechEngine.png)

### Service Endpoint call - Invoke OCI Object Storage

      uploadfile - /n/{namespaceName}/b/{bucketName}/o/{objectName}
      getObject - /n/{namespaceName}/b/{bucketName}/o/{outputFolderName}/{outputObjectName}

### Service Endpoint call - Invoke AI Speech Service 

      create transcription - /transcriptionJobs
      get transcription - transcriptionJobs/{transcriptionJobId}

### Service Endpoint call - Invoke Generative AI Service

      create summary - /20231130/actions/summarizeText

## Conclusion

In this article, we've covered how to utilize Oracle AI Speech Service features to provide a transription and summarize using Generative AI service.  

Feel free to modify and expand upon this template according to your specific use case and preferences.

## License
Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.