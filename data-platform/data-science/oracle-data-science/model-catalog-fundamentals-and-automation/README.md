# Overview

This project demonstrates the fundamentals of using the OCI Data Science Model Catalog and shows how to automate model registration workflows using jobs.

It contains two examples with increasing levels of sophistication:
1. Model Catalog Fundamentals – introduces core Model Catalog concepts and operations.
2. Automated Model Registration – demonstrates how to automate model registration using Data Science Jobs and model version sets.

Reviewed: 2026.01.19

# Project Scope

This project covers the following topics:

1. Model Catalog Fundamentals

* Essential Model Catalog operations, including:
1. Model serialization
2. Model registration in the Model Catalog
3. Loading a registered model and using it for inference
4. Retrieving model metadata from the catalog (using multiple approaches)
5. Updating a registered model’s metadata (using multiple approaches)

* The implementation heavily relies on the ADS SDK.
* Note: Model deployment is out of scope for this notebook.

2. Automated Model Registration

* Automating the model registration process using OCI Data Science Jobs and model version sets, including:
1. Defining a model version set
2. Adding multiple model versions to a version set via job runs
3. Implementing a retention mechanism for archiving older model versions
4. Use of Object stroage in the JupyterLab and Jobs 
* This example also heavily relies on the ADS SDK.

# Prerequisites
* Access to the OCI Data Science Platform
* Basic familiarity with Python and machine learning concepts
* An OCI compartment with:
1. Resource principal configured
2. Appropriate IAM policies for OCI Data Science, Object Storage, and Model Catalog

# How to Use
1. Open the notebooks in an OCI Data Science Notebook Session.
2. Select the following conda environment: generalml_p311_cpu_x86_64_v1
3. Run the notebook cells sequentially to reproduce each workflow:
4. Start with the Model Catalog Fundamentals notebook
5. Proceed to the Automated Model Registration notebook for advanced automation
