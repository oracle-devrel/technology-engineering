#!/usr/bin/env bash
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd $SCRIPT_DIR

. ./env.sh

# OCI_GenAI_access_gateway
sudo dnf install -y git
sudo dnf install -y python3.12 python3.12-pip python3-devel
sudo update-alternatives --set python /usr/bin/python3.12
curl -LsSf https://astral.sh/uv/install.sh | sh

# git clone https://github.com/jin38324/OCI_GenAI_access_gateway.git
cd OCI_GenAI_access_gateway

# Install virtual env python_env
uv venv myenv
source myenv/bin/activate
uv pip install -r requirements.txt

cd app
# AUTH_TYPE
sed -i "s&AUTH_TYPE = \"API_KEY\"&AUTH_TYPE = \"INSTANCE_PRINCIPAL\"&" config.py

# REGION
# sed -i "s&AUTH_TYPE = \"API_KEY\"&AUTH_TYPE = \"INSTANCE_PRINCIPAL\"&" config.py

# COMPARTMENT
sed -i '/^PORT =.*/i import os\n' config.py
sed -i "s&REGION = .*&REGION = os.environ['TF_VAR_region']&" config.py

if [ "$TF_VAR_use_models_yaml" == "true" ]; then
  # OCI_COMPARTMENT = "" -> Use models.yaml
  sed -i "s&OCI_COMPARTMENT = \"ocid1.compartment.oc1..xxx\"&OCI_COMPARTMENT = \"\"&" config.py
else
  # Use the compartment to auto-discover the models
  sed -i "s&OCI_COMPARTMENT = \"ocid1.compartment.oc1..xxx\"&OCI_COMPARTMENT = os.environ['TF_VAR_compartment_ocid']&" config.py
fi 

# Models.yaml
sed -i "s&ocid1.generativeaiendpoint.oc1\..*$&$TF_VAR_dac_endpoint_ocid&" models.yaml
# Region
sed -i "s&us-chicago-1&$TF_VAR_region&" models.yaml
# Compartment
sed -i "s&compartment_id: ocid1.compartment.oc1\.\..*$&compartment_id: $TF_VAR_compartment_ocid&" models.yaml 
