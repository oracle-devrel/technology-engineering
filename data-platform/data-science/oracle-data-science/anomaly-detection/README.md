# Overview

This repository contains end-to-end anomaly detection projects demonstrating both supervised and unsupervised approaches using OCI Data Science and the ADS SDK.

The projects cover key stages of the ML lifecycle, including data preparation, modeling, validation, model registration and deployment, deployment invocation, and monitoring workflows.

The repository currently includes:

* **Fraud Classification** – supervised fraud detection using classification models.
* **Sales Unlabeled Anomaly Detection** – time-series anomaly detection using SARIMAX forecasting and prediction intervals.

---

# Projects

## Fraud Classification

This project demonstrates a supervised fraud detection workflow, including preprocessing, modeling, validation, model deployment, and deployment invocation.

The project also demonstrates production-oriented concepts such as:
1. Scikit-learn pipelines
2. Custom deployment artifacts
3. Feature engineering within the deployment pipeline, and handling high-cardinality categorical features.

The deployed model can support both real-time and batch fraud monitoring workflows. The batch implementation is also covered in this project, the real time use case requires streaming tool, and not covered here.

---

## Sales Unlabeled Anomaly Detection

This project demonstrates anomaly detection for a continuous unlabeled target variable using time-series regression and SARIMAX forecasting.

The workflow includes exploratory analysis, time-series modeling and validation, anomaly detection using prediction intervals, custom model deployment, and production monitoring workflows integrated with OCI Monitoring.


---

# Environment

Conda environment: `generalml_p311_cpu_x86_64_v1`

Created: 2026

---

# Prerequisites

* Access to OCI Data Science
* Required IAM permissions
* Familiarity with Python and machine learning workflows

---

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
