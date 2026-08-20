# Registration and Deployment with OCI SDK

This project demonstrates how to register and deploy a machine learning model using the OCI SDK, while using the ADS SDK to create the model artifact.
Although ADS simplifies model registration and deployment, it can be limiting for advanced scenarios. In this notebook, we use the OCI SDK to:
- Register a model in a different compartment than the Notebook Session
- Deploy the model to that target compartment
- Move an existing model deployment between compartments

Reviewed: 2026.08.13

# Environment
Conda environment: automlx251_p311_cpu_x86_64_v2


# Prerequisites
- Access to OCI Data Science
- Required IAM permissions for model registration and deployment
- Basic familiarity with Python and OCI SDK

# License
 
Copyright (c) 2026 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.