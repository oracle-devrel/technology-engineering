# Overview
This project demonstrates how to register and deploy a machine learning model using the OCI SDK, while using the ADS SDK to create the model artifact.
Although ADS simplifies model registration and deployment, it can be limiting for advanced scenarios. In this notebook, we use the OCI SDK to:
- Register a model in a different compartment than the Notebook Session
- Deploy the model to that target compartment
- Move an existing model deployment between compartments

# Environment
Conda environment: automlx251_p311_cpu_x86_64_v2
Created: 05/03/2026

# Prerequisites
- Access to OCI Data Science
- Required IAM permissions for model registration and deployment
- Basic familiarity with Python and OCI SDK
# License
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.