# Overview
This project demonstrates how to deploy a machine learning model using the ADS SDK while customizing the default generated model artifacts, which is often required in production scenarios.

While ADS provides a standard template for model artifacts, real-world use cases frequently require additional logic. In this notebook, we focus on modifying the generated artifacts to incorporate feature engineering directly into the deployment pipeline.

The main advantage of this approach is that feature engineering is executed as part of the model inference process, eliminating the need to repeat these steps each time the model is invoked.

Specifically, the notebook covers:
1. Building a model to predict Titanic survival using a Scikit-learn pipeline
2. Preparing model artifacts using the ADS SDK
3. Customizing the generated artifact to include feature engineering in score.py
4. Registering, deploying, and invoking the model

# Environment

Conda environment: generalml_p311_cpu_x86_64_v1
Created: April 2026

# Prerequisites
- Access to OCI Data Science
- Required IAM permissions for model registration and deployment
- Basic familiarity with Python, Pandas, and Scikit-learn

# License
Copyright (c) 2026 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.