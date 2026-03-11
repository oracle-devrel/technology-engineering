## OCI Lite-LLM installation script

### Usage
- Login to OCI Cloud
- Create a compartment and get the ##compartment OCID##
- Click on your user icon.
  - Profile / your user
  - Go in the tab tokens and key. In API Keys, click add **API Keys**
  - Download the 2 keys
    - private (##PRIVATE_KEY##) 
    - and public.
  - You will also some user ##SETTINGS##. Ex:
    ```
    [DEFAULT]
    user=ocid1.user.oc1..xxxxx
    fingerprint=12:34:56:78:12:34:56:78:12:34:56:78:12:34:56:78:12:34:56:78
    tenancy=ocid1.tenancy.oc1..xxxxxx
    region=eu-frankfurt-1
    key_file=<path to your private keyfile>
    ```
- In OCI Console, start the OCI Cloud Shell or the Cloud Editor.
- Run: git clone https://github.com/mgueury/oci-litellm.git
- Edit the files
  - src/config.yaml: fill in the files based on the ##SETTINGS## above
  - src/oci_api_key.pem : put the content of ##PRIVATE_KEY##
- Run terraform
  ```
  ./starter.sh build
  > Compartment use: ##Compartment OCID##
  > Password: (!!!!) Use your own password and use only underscore "_" as special character. LiteLLM is sensitive to a lot of them and the installation can brake because of them.
  ```
- Wait that it finishes
  You will get something like this at the end
  ```
  LiteLLM UI:
  - http://12.34.45.67:8080/ui
    admin / pwd123

  OpenAI compatible URL
  - http://152.70.27.47:8080/v1
  - https://xxxx.apigateway.eu-frankfurt-1.oci.customer-oci.com/litellm/v1
    API KEY : pwd123
    MODEL   : oci_cohere_command_latest (see config.yaml)

  curl https://xxxx.apigateway.eu-frankfurt-1.oci.customer-oci.com/litellm/v1/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer pwd123" \
  -d '{"model": "oci_cohere_command_latest", "prompt": "Who are you", "max_tokens": 200}'
  ```
  
### Commands
- starter.sh         : Show the menu
- starter.sh help    : Show the list of commands
- starter.sh build   : Build the whole program: Run Terraform, Configure the DB, Build the App, Build the UI
- starter.sh destroy : Destroy the objects created by Terraform
- starter.sh env     : Set the env variables in BASH Shell

### Directories
- src           : Sources files
    - app       : Source of the Backend Application
    - terraform : Terraform scripts
    - compute   : Contains the deployment files to Compute

Help (Tutorial + How to customize): https://www.ocistarter.com/help

### Next Steps:

- Run:
  cd starter
  ./starter.sh
