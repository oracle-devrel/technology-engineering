import io
import os
import pandas as pd
import requests

import oci

import helper
import config


bucket_name = config.BUCKET_NAME
folder_name= config.FOLDER_NAME
feature_cols = config.FEATURE_COLS
date_col= config.DATE_COL
target_col= config.TARGET_COL
compartment_id=config.COMPARTMENT
monitoring_namespace=config.MONITORING_NAMESPACE
metric_name=config.MONITORING_METRIC_NAME
endpoint=config.ENDPOINT

input_file_name = os.getenv("INPUT_FILE_NAME")
print(input_file_name)

signer = oci.auth.signers.get_resource_principals_signer()
object_storage_client = oci.object_storage.ObjectStorageClient(
    config={},
    signer=signer
)

namespace_name = object_storage_client.get_namespace().data

df = helper.read_csv_from_object_storage(
    client=object_storage_client,
    namespace=namespace_name,
    bucket=bucket_name,
    folder_name=folder_name,
    object_name=input_file_name
)
#df.head()

agg_df = helper.create_aggregated_df(df)

if len(agg_df) != 1:
    raise ValueError(f"Expected exactly 1 aggregated row, got {len(agg_df)}")
features_df = agg_df[feature_cols].copy()
#features_df.head()

features_df = features_df[feature_cols].copy()
payload = features_df.to_dict(orient="list")

result = helper.call_deployed_model(endpoint, signer, payload)

prediction = float(result["prediction"])
lower = float(result["lower_prediction_interval"])
upper = float(result["upper_prediction_interval"])
actual = float(agg_df[target_col].iloc[0])

is_anomaly = actual < lower or actual > upper
print(is_anomaly)

monitoring_client = oci.monitoring.MonitoringClient(
    config={},
    signer=signer,
    service_endpoint="https://telemetry-ingestion.eu-frankfurt-1.oraclecloud.com"
)

response = helper.push_forecast_metrics(
    monitoring_client=monitoring_client,
    compartment_id=compartment_id,
    namespace=monitoring_namespace,
    metric_name=metric_name,
    actual=actual,
    predicted=prediction,
    lower=lower,
    upper=upper,
)
print(response.data)
