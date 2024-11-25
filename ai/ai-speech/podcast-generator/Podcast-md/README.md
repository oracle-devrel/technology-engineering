# Podcast Generator with Oracle AI and Low-Code
Welcome to this guide on building a groundbreaking application that uses Oracle's AI-powered tools to generate high-quality podcasts effortlessly. Leveraging the Oracle Cloud Infrastructure (OCI) GenAI and AI Speech (Text-to-Speech) services, this solution transforms written content into engaging, natural-sounding audio.
The application is designed to streamline podcast production through advanced AI capabilities. Starting from a simple text input, the app uses GenAI to generate a structured podcast script. It then enhances the speech output with SSML (Speech Synthesis Markup Language), which gives the audio a natural flow, making it sound like a professional recording. The result is a high-quality audio experience that can cater to a wide range of content needs and audiences.
This application is built using Oracle Visual Builder Cloud Service (VBCS), a powerful low-code platform that simplifies development and accelerates the creation of robust applications without extensive coding. With this low-code approach, even complex workflows are straightforward to set up, allowing developers to focus on leveraging AI's potential for high-quality audio synthesis.
This AI-powered solution not only automates and optimizes the podcast creation process but also allows content creators to deliver professional audio content at scale efficiently.
# **1. Prepare your user**
   
   In Oracle Cloud Infrastructure (OCI), API keys are used for secure authentication when accessing OCI resources through REST APIs. OCI API keys consist of two parts: a Public key and a Private key. You use the OCI console to generate the Private/Public key pair.
   Generate API Keys using OCI Console
    To Generate the API Keys using OCI Console:

  - Login into your OCI Account.
   ![alt text](ak1.png)
  - Click on the Profile icon at the top-right corner and select your Profile hyperlink.
   ![alt text](ak2.png)
  - Under Resources section at the bottom-left, select API Keys and then click Add API Key.
   ![alt text](ak3.png)
  - The Add API Key dialog is displayed. Select Generate API Key Pair to create a new key pair.
  ![alt text](ak4.png)
  - Click Download Private Key. A .pem file is saved to your local device. You do not need to download the public key and click Add button.
  ![alt text](ak5.png)
  


# **2.Pick you compartment**
Identify the compartment you're currently working within. Navigate to 'Identity' -> 'Compartments'. Locate your compartment and make a note of its OCID (Oracle Cloud Identifier)

# **3.Open Visual Builder**
## Import Visual Builder project
* Open Visual Builder and click on the "Import" button. Choose "Application from file".
* Drop the zip project file
* Provide a name and an ID, for example "Podcast_Generator". Click on Import button.
 ![alt text](import_project.jpg)
  
## Configure REST APIs authentication
* Open the recently created project.
 
* Click on Services button (left side) and click on "Backends"
 ![alt text](services.jpg)

* Now, click on TTS, and Servers to edit server authentication.
![alt text](edit_tts.jpg)

* Click the pencil to provide the OCI Crendentials
 ![alt text](edit_tts_2.jpg)

* Provide the crendentials you got during the step 1.
 ![alt text](signature.jpg)

* Repeat the same process with the GenAI backend.

## Provide your compartmentId 
* Provide compartmentId default value in the project variable named "comparmentid" that you got during the step 2.
 ![alt text](compartmentid.jpg)

#  **4.Preview the application**
* Now can provide a topic in the text area and click "generate" button. 
 ![alt text](preview.jpg)

* Automatically a podcast script will be created and will generate the audio podcast using the Cindy and Bob voices
  ![alt text](generated.jpg)


## I hope you liked it.
Author: Jesús Brasero